import tarfile
import requests
from io import BytesIO
import pandas as pd
import os
import re
import lxml
from bs4 import BeautifulSoup
from lxml import etree as ET
import sqlite3
from datetime import datetime


def normalize_pmid_value(pmid):
    # Eliminar cualquier carácter que no sea un dígito
    pmid = re.sub(r'\D', '', pmid)
    return pmid

def normalize_citation(citation):
    normalized = re.sub(r'\.\s+\d{4}.*', '', citation)
    return normalized

def extraer_texto_completo(root, path):
    element = root.find(path)
    if element is not None:
        text = ''.join(element.itertext())  # Asegura obtener todo el texto dentro del elemento
        #print(f"Extracción completa - {path}: {text}")  # Control de errores
        return text
    else:
        print(f"No se encontró el elemento - {path}", flush=True)  # Control de errores
        return None

def extraer_seccion_completa(root, keywords):
    sections = []
    # Buscar todos los títulos de sección primero
    section_titles = root.findall(".//sec/title") + root.findall(".//sec/section-title")
    for section_title in section_titles:
        # Verificar que section_title.text no sea None antes de llamar a .lower()
        if section_title is not None and section_title.text and any(keyword.lower() in section_title.text.lower() for keyword in keywords):
            # Buscar el elemento 'sec' que es contiene la sección
            sec_element = section_title
            while sec_element.tag != 'sec' and sec_element is not None:
                sec_element = sec_element.getparent()
            
            if sec_element is not None:
                # Extraer todo el texto dentro del elemento sec
                text_elements = [elem.text for elem in sec_element.iter() if elem.text]
                sections.append(' '.join(text_elements).strip())
    
    return " ".join(sections)

def process_extracted_article(xml_path, conn):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    pmid = extraer_texto_completo(root, ".//article-id[@pub-id-type='pmid']")
    title = extraer_texto_completo(root, ".//article-title")
    year = extraer_texto_completo(root, ".//pub-date/year")
    doi = extraer_texto_completo(root, ".//article-id[@pub-id-type='doi']")
    journal_name = extraer_texto_completo(root, ".//journal-title")
    first_author = extraer_texto_completo(root, ".//contrib-group/contrib[@contrib-type='author']/name/surname")
    abstract = extraer_texto_completo(root, ".//abstract")
    methods = extraer_seccion_completa(root, ['methods', 'methodology', 'materials'])
    results = extraer_seccion_completa(root, ['results', 'findings'])

    if None in [pmid]:  # Datos esenciales
        print("Faltan datos críticos, no se inserta el registro.", flush=True) # Control de errores
        return

    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO articles (pmid, title, year, doi, journal_name, first_author, abstract, methods, results)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (pmid, title, year, doi, journal_name, first_author, abstract, methods, results))
        conn.commit()
        print(f"Artículo {pmid} insertado correctamente.", flush=True)
    except sqlite3.IntegrityError:
        print(f"Error: El artículo con PMID {pmid} ya existe en la base de datos.", flush=True) # Control de errores
    except Exception as e:
        print(f"Error al insertar: {e}", flush=True) # Control de errores

def extract_pmids_from_database(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT distinct(pmid) FROM sra_metadata where length(pmid) > 2")  
        pmids = [normalize_pmid_value(str(row[0])) for row in cursor.fetchall() if row[0] and int(row[0]) >= 1]  
        print("Número de PMIDs extraídos de la base de datos:", len(pmids), flush=True) # Deben ser 7135
        return pmids
    except sqlite3.Error as e:
        print(f"Error al extraer PMIDs de la base de datos: {e}") # Control de errores
        return []
    
def connect_to_database(database_path):
    try:
        conn = sqlite3.connect(database_path)
        print("Conexión a la base de datos establecida.")
        return conn
    except sqlite3.Error as e:
        print(f"Error al conectar a la base de datos: {e}") # Control de errores
        return None

def download_and_process_articles(base_url, extract_path):
    conn = sqlite3.connect('pubmed_articles.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            pmid TEXT PRIMARY KEY,
            title TEXT,
            year TEXT,
            doi TEXT,
            journal_name TEXT,
            first_author TEXT,
            abstract TEXT,
            methods TEXT,
            results TEXT
        )
    ''')
    conn.commit()

    # Conectarse a la base de datos complete_db.db
    complete_db_conn = connect_to_database('/Storage/data1/isabella.gallego/IC/SRA_dbs/complete_db.db')
    
    if complete_db_conn is not None:
        pmids_from_db = extract_pmids_from_database(complete_db_conn)
        #pass
    else:
        print("No se pudo conectar a la base de datos. Deteniendo la ejecución.") # Control de errores
        return
    
    response = requests.get(base_url)
    if response.status_code != 200:
        print(f"Fallo en la conexión: Estado {response.status_code}") # Control de errores
        return

    soup = BeautifulSoup(response.content, 'html.parser')
    links = soup.find_all('a')
    txt_files = [link.get('href') for link in links if link.get('href').endswith('.filelist.txt')]
    #print("Archivos .txt encontrados en la página web:", txt_files) # Control de errores

    # Filtrar los archivos filetext.txt según PMIDs
    filtered_txt_files = [] 
    for txt_file in txt_files:
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        print(f"Pre-Procesando {txt_file} Current Time: {current_time}", flush=True)
        txt_url = os.path.join(base_url, txt_file)
        txt_data = requests.get(txt_url).text
        data = pd.read_csv(BytesIO(bytes(txt_data, 'utf-8')), sep='\t', dtype={4: 'str'})

        # Buscar PMIDs en la columnda PMID del archivo .txt
        pmids_in_file = set(data['PMID'].dropna())    

        filtered_pmids = pmids_in_file.intersection(pmids_from_db)
        #print(f"PMIDs relevantes encontrados en {txt_file}: {filtered_pmids}") # Control de errores
    
        if filtered_pmids:
            filtered_txt_files.append(txt_file)
            #else:
                #print(f"No se encontraron PMIDs relevantes en {txt_file}") # Control de errores

            filtered_data = data[data['PMID'].astype(str).apply(normalize_pmid_value).isin(pmids_from_db)]

            if filtered_data.empty:
                #print(f"No se encontraron artículos relevantes en {txt_file}") # Control de errores
                continue

            #        tar_gz_filename = tar_gz_files.get(txt_file.split('.filelist.')[0] + '.tar.gz')
            tar_gz_filename = txt_file.split('.filelist.')[0] + '.tar.gz'
    
            if tar_gz_filename:
                tar_gz_url = os.path.join(base_url, tar_gz_filename)
                tar_gz_response = requests.get(tar_gz_url)
                print(f"{tar_gz_filename}\t{tar_gz_response.elapsed.total_seconds()}", flush=True)

                tar_gz_file = tarfile.open(fileobj=BytesIO(tar_gz_response.content), mode="r:gz")
    
                for member in tar_gz_file.getmembers():
                    if member.name in filtered_data['Article File'].values:
                        tar_gz_file.extract(member, path=extract_path)
                        full_path = os.path.join(extract_path, member.name)
                        print(f"Procesando artículo {member.name}...")
                        process_extracted_article(full_path, conn)
                #else:
                    #print(f"Archivo {member.name} no encontrado en los datos filtrados.") # Control de errores

    conn.close()
    print('------------')

base_url = 'https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_bulk/oa_comm/xml/'
extract_path = '/Storage/data1/isabella.gallego/IC/extracted_articles'
download_and_process_articles(base_url, extract_path)
