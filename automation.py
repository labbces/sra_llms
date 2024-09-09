# API configuration (https://docs.llama-api.com/essentials/chat)

from openai import OpenAI

# LLAMA API 
client = OpenAI(
    api_key="<api_token>",  # API Key
    base_url="https://api.llama-api.com"
)

# Prompt definition

def crear_prompt_metodologia(texto_metodologia, tipo_informacion):
    prompt = f"Del siguiente texto de metodología, extrae {tipo_informacion}: {texto_metodologia}"
    return prompt

# Prompt sending

def enviar_prompt_a_llama(prompt):
    response = client.Completion.create(
        model="llama-13b-chat",  # Modelo de LLAMA escogido
        prompt=prompt,
        max_tokens=1000  # Depende de la longitud de la respuesta esperada
    )
    
# Response processing

def procesar_respuesta_llama(respuesta):
    # Asumiendo que la respuesta es un objeto y no un diccionario JSON directo
    texto_extraido = respuesta.choices[0].text  # Revisar
    return texto_extraido

# Workflow integration

def actualizar_metadatos_con_llama(texto_metodologia, tipo_informacion, id_sra):
    prompt = crear_prompt_metodologia(texto_metodologia, tipo_informacion)
    respuesta_llama = enviar_prompt_a_llama(prompt)
    info_extraida = procesar_respuesta_llama(respuesta_llama)


def actualizar_base_de_datos(id_sra, campo, valor):
    # Database logic here
    pass
