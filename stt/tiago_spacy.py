import spacy

nlp = spacy.load("es_core_news_sm")

# Limpia el texto de puntuación y espacios innecesarios
def clean_text(text):
    return text.strip().replace(".", "").replace("!", "").replace("?", "")

# Parsea el comando de texto y extrae la acción, objeto y topic
def parse_command(text):
    text = clean_text(text) # Limpiar el texto antes de procesar
    doc = nlp(text) # Procesar el texto con spaCy para obtener tokens y sus propiedades

    tokens = [t.text.lower() for t in doc] # Convertir los tokens a minúsculas para facilitar la comparación

    # Acción = primer token
    action = tokens[0] if len(tokens) > 0 else None

    # Objeto = segundo token en adelante (si existe)
    obj = None
    if len(tokens) > 1:
        # buscamos el primer token que no sea determinante
        for t in doc[1:]:
            if t.pos_ not in ["DET", "ADP", "PRON"]:
                obj = t.lemma_.lower()
                break

    topic = text.lower() # El topic se puede considerar como el texto completo en minúsculas

    # Devolver un diccionario con la acción, objeto y topic extraído
    return {
        "action": action,
        "object": obj,
        "topic": topic
    } 

# Función principal para procesar un archivo de texto y escribir el resultado en otro archivo
def process_file(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read().strip()

    result = parse_command(text)

    action = result["action"]
    obj = result["object"]
    topic = result["topic"]

    # Crear una salida formateada con la información extraída
    output = (
        f"Orden detectada:\n"
        f"Acción: {action}\n"
        f"Objeto: {obj}\n"
        f"Topic: {topic}\n"
    )

    # Escribir la salida en el archivo de salida
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output)

