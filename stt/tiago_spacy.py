import spacy

nlp = spacy.load("es_core_news_sm")

def clean_text(text):
    return text.strip().replace(".", "").replace("!", "").replace("?", "")

def parse_command(text):
    text = clean_text(text)
    doc = nlp(text)

    tokens = [t.text.lower() for t in doc]

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

    topic = text.lower()

    return {
        "action": action,
        "object": obj,
        "topic": topic
    }

def process_file(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read().strip()

    result = parse_command(text)

    action = result["action"]
    obj = result["object"]
    topic = result["topic"]

    output = (
        f"Orden detectada:\n"
        f"Acción: {action}\n"
        f"Objeto: {obj}\n"
        f"Topic: {topic}\n"
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output)

