# Configuración de la API (https://docs.llama-api.com/essentials/chat)

from openai import OpenAI

# Configurar el cliente de API de LLAMA
client = OpenAI(
    api_key="<api_token>",  # Reemplazar con API Key
    base_url="https://api.llama-api.com"
)

# Definición de prompts

def crear_prompt_metodologia(texto_metodologia, tipo_informacion):
    prompt = f"Del siguiente texto de metodología, extrae {tipo_informacion}: {texto_metodologia}"
    return prompt

# Función para Enviar Prompts a LLAMA

def enviar_prompt_a_llama(prompt):
    response = client.Completion.create(
        model="llama-13b-chat",  # Modelo de LLAMA escogido
        prompt=prompt,
        max_tokens=1000  # Depende de la longitud de la respuesta esperada
    )
    
# Procesamiento de la Respuesta

def procesar_respuesta_llama(respuesta):
    # Asumiendo que la respuesta es un objeto y no un diccionario JSON directo
    texto_extraido = respuesta.choices[0].text  # Revisar
    return texto_extraido

# Integración en el workflow

def actualizar_metadatos_con_llama(texto_metodologia, tipo_informacion, id_sra):
    prompt = crear_prompt_metodologia(texto_metodologia, tipo_informacion)
    respuesta_llama = enviar_prompt_a_llama(prompt)
    info_extraida = procesar_respuesta_llama(respuesta_llama)


def actualizar_base_de_datos(id_sra, campo, valor):
    # Implementar la lógica para actualizar la base de datos aquí
    pass