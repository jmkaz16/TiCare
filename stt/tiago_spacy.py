import spacy
from rapidfuzz import fuzz, process
from input.command_map import COMMAND_MAP

nlp = spacy.load("es_core_news_sm")

# ============================
# NORMALIZACIÓN
# ============================

def normalize(text):
    return text.lower().strip()


# ============================
# Fuzzy matching
# ============================

def fuzzy_match(text, threshold=75):
    """
    Devuelve el comando si encuentra un sinónimo con suficiente similitud.
    """
    choices = list(COMMAND_MAP.keys())

    match, score, _ = process.extractOne(
        text,
        choices,
        scorer=fuzz.ratio
    )

    if score >= threshold:
        return COMMAND_MAP[match]

    return None


# ============================
# PARSEADOR PRINCIPAL
# ============================

def parse_command(text):
    text_norm = normalize(text)

    # 1) Coincidencia exacta
    if text_norm in COMMAND_MAP:
        return {
            "action": COMMAND_MAP[text_norm],
            "object": None,
            "topic": text_norm
        }

    # 2) Fuzzy matching
    fuzzy_result = fuzzy_match(text_norm)
    if fuzzy_result:
        return {
            "action": fuzzy_result,
            "object": None,
            "topic": text_norm
        }

    # 3) Fallback con spaCy si no se reconoce la orden
    doc = nlp(text_norm)

    action = None
    obj = None

    # Primer verbo
    for token in doc:
        if token.pos_ == "VERB":
            action = token.lemma_
            break

    # Primer sustantivo, adverbio o adposición
    for token in doc:
        if token.pos_ in ["NOUN", "ADV", "ADP"]:
            obj = token.text
            break

    return {
        "action": action,
        "object": obj,
        "topic": text_norm
    }


# ============================
# PROCESAR ARCHIVO
# ============================

def process_file(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read().strip()

    result = parse_command(text)

    output = (
        f"Acción: {result['action']}\n"
        f"Objeto: {result['object']}\n"
        f"Topic: {result['topic']}\n"
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output)
