import spacy
from rapidfuzz import fuzz, process
from input.command_map import COMMAND_MAP

nlp = spacy.load("es_core_news_sm")


# ============================================================
# 1. NORMALIZACIÓN
# ============================================================

def normalize(text):
    return text.lower().strip()


# ============================================================
# 2. MAPEO DE ACCIONES (usa diccionario + fuzzy)
# ============================================================

def map_action_from_text(text):
    """
    Intenta mapear la frase completa a una acción conocida.
    """
    choices = list(COMMAND_MAP.keys())
    match, score, _ = process.extractOne(text, choices, scorer=fuzz.ratio)

    if score >= 75:
        return COMMAND_MAP[match]

    return None


def map_action_from_word(word):
    """
    Intenta mapear una sola palabra (o su lema) a una acción conocida.
    """
    lemma = nlp(word)[0].lemma_
    choices = list(COMMAND_MAP.keys())

    # Coincidencia directa
    match, score, _ = process.extractOne(word, choices, scorer=fuzz.ratio)
    if score >= 70:
        return COMMAND_MAP[match]

    # Coincidencia por lema
    match, score, _ = process.extractOne(lemma, choices, scorer=fuzz.ratio)
    if score >= 70:
        return COMMAND_MAP[match]

    return None


# ============================================================
# 3. ANALIZADOR SINTÁCTICO ROBUSTO
# ============================================================

def parse_syntax(text):
    """
    Extrae:
    - verbo principal
    - determinante
    - objeto (nombre)
    - dirección (izquierda, derecha, adelante, atrás…)
    """
    doc = nlp(text)

    verb = None
    det = None
    noun = None
    direction = None

    # Lista de direcciones reconocidas
    direction_words = {
        "izquierda": "left",
        "derecha": "right",
        "arriba": "up",
        "abajo": "down",
        "delante": "forward",
        "adelante": "forward",
        "atrás": "back",
        "atras": "back",
        "hacia": None  # se usa en combinación
    }

    # Buscar verbo principal
    for token in doc:
        if token.pos_ == "VERB":
            verb = token.lemma_
            break

    # Buscar determinante + nombre
    for token in doc:
        if token.pos_ == "DET":
            det = token.text

        if token.pos_ == "NOUN":
            noun = token.text

            # Si el nombre es una dirección
            if noun in direction_words:
                direction = direction_words[noun]

            break

    # Buscar direcciones como adverbios o adposiciones
    for token in doc:
        if token.text in direction_words:
            # Caso simple: "izquierda", "derecha"
            if direction_words[token.text]:
                direction = direction_words[token.text]

        # Caso compuesto: "hacia atrás"
        if token.text == "hacia":
            next_token = token.nbor(1)
            if next_token.text in direction_words:
                direction = direction_words[next_token.text]

    # Si no hay verbo pero sí nombre → verbo implícito
    if verb is None and noun:
        if noun in ["pata", "mano"]:
            verb = "dar"
        if noun in ["cinco"]:
            verb = "chocar"

    return verb, det, noun, direction


# ============================================================
# 4. PARSEADOR PRINCIPAL
# ============================================================

def parse_command(text):
    text_norm = normalize(text)

    # ---- 1. Intento directo por frase completa ----
    action = map_action_from_text(text_norm)
    if action:
        return {
            "action": action,
            "object": None,
            "direction": None,
            "topic": text_norm
        }

    # ---- 2. Análisis sintáctico ----
    verb, det, noun, direction = parse_syntax(text_norm)

    # ---- 2.1 Mapear verbo a acción ----
    if verb:
        action = map_action_from_word(verb)

    # ---- 2.2 Si no hay acción pero sí nombre → intentar mapear nombre ----
    if noun and not action:
        action = map_action_from_word(noun)

    # ---- 2.3 Si no hay acción pero sí dirección → movimiento ----
    if direction and not action:
        action = direction

    # ---- 3. Resultado final ----
    return {
        "action": action,
        "object": noun,
        "direction": direction,
        "topic": text_norm
    }