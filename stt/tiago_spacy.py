import spacy
from rapidfuzz import fuzz, process
from input.command_map import COMMAND_MAP


# ============================================================
# 1. CARGAR MODELO spaCy
# ============================================================

nlp = spacy.load("es_core_news_sm")


# ============================================================
# 2. NORMALIZACIÓN DE TEXTO
# ============================================================

def normalize(text):
    return text.lower().strip()


# ============================================================
# 3. FUZZY MATCHING POR FRASE COMPLETA
# ============================================================

def fuzzy_match(text, threshold=75):
    """
    Intenta encontrar una coincidencia aproximada entre la frase completa
    y los sinónimos del diccionario.
    """
    choices = list(COMMAND_MAP.keys())
    match, score, _ = process.extractOne(text, choices, scorer=fuzz.ratio)

    if score >= threshold:
        return COMMAND_MAP[match]

    return None


# ============================================================
# 4. FUZZY MATCHING POR PALABRAS CLAVE (MEJORA IMPORTANTE)
# ============================================================

def fuzzy_match_words(text, threshold=70):
    """
    Permite reconocer órdenes incompletas como:
    - "choca"
    - "cinco"
    - "choca la mano"
    - "choca eso"
    - "choca conmigo"

    Analiza:
    - palabras individuales
    - bigramas
    - trigramas
    """
    words = text.split()
    choices = list(COMMAND_MAP.keys())

    # ---- 4.1 Palabras individuales ----
    for w in words:
        match, score, _ = process.extractOne(w, choices, scorer=fuzz.ratio)
        if score >= threshold:
            return COMMAND_MAP[match]

    # ---- 4.2 Bigramas ----
    for i in range(len(words) - 1):
        bg = f"{words[i]} {words[i+1]}"
        match, score, _ = process.extractOne(bg, choices, scorer=fuzz.ratio)
        if score >= threshold:
            return COMMAND_MAP[match]

    # ---- 4.3 Trigramas ----
    for i in range(len(words) - 2):
        tg = f"{words[i]} {words[i+1]} {words[i+2]}"
        match, score, _ = process.extractOne(tg, choices, scorer=fuzz.ratio)
        if score >= threshold:
            return COMMAND_MAP[match]

    return None


# ============================================================
# 5. PARSEADOR PRINCIPAL
# ============================================================

def parse_command(text):
    """
    Devuelve un diccionario con:
    - Acción
    - Objeto
    - Topic original
    """

    text_norm = normalize(text)

    # ----