# stt/tiago_spacy.py
# Versión con lazy loading de spaCy para evitar bloqueos en import.
# - get_nlp() carga el modelo solo cuando se necesita.
# - Si no puede cargar es_core_news_sm, usa spacy.blank("es") como fallback.
# - Esto permite que 'import stt.tiago_spacy' sea rápido y no bloquee main.py.

import unicodedata
from typing import Optional, Tuple
import spacy

# Variable privada para almacenar la instancia del modelo
_nlp: Optional[spacy.language.Language] = None

def _normalize_text_remove_accents(s: str) -> str:
    """
    Normaliza texto: minúsculas, strip y elimina marcas diacríticas (tildes).
    Útil para matching fuzzy y para normalizar conectores.
    """
    s = s.lower().strip()
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return s

def get_nlp() -> spacy.language.Language:
    """
    Devuelve la instancia de spaCy. Si no está cargada, intenta cargar
    'es_core_news_sm'. Si falla, crea y devuelve un modelo en blanco.
    """
    global _nlp
    if _nlp is not None:
        return _nlp

    try:
        # Intento de carga del modelo entrenado
        _nlp = spacy.load("es_core_news_sm")
        print("spaCy: modelo es_core_news_sm cargado correctamente.")
    except Exception as e:
        # Fallback: modelo en blanco para evitar que la importación falle
        print("spaCy: no se pudo cargar es_core_news_sm. Usando modelo en blanco. Error:", e)
        _nlp = spacy.blank("es")
    return _nlp

# Funciones del parser que usan get_nlp() en lugar de usar nlp global en import
def normalize(text: str) -> str:
    return text.lower().strip()

def map_action_from_text(text: str):
    # Placeholder: tu lógica de fuzzy con COMMAND_MAP aquí
    # Importa COMMAND_MAP localmente si lo necesitas para evitar import circular
    from input.command_map import COMMAND_MAP
    from rapidfuzz import process, fuzz
    choices = list(COMMAND_MAP.keys())
    match = process.extractOne(text, choices, scorer=fuzz.ratio)
    if match:
        matched_text, score, _ = match
        if score >= 75:
            return COMMAND_MAP[matched_text]
    return None

def map_action_from_word(word: str):
    nlp = get_nlp()
    if not word:
        return None
    lemma = nlp(word)[0].lemma_ if len(nlp(word)) > 0 else word
    from input.command_map import COMMAND_MAP
    from rapidfuzz import process, fuzz
    choices = list(COMMAND_MAP.keys())
    match = process.extractOne(word, choices, scorer=fuzz.ratio)
    if match and match[1] >= 70:
        return COMMAND_MAP[match[0]]
    match = process.extractOne(lemma, choices, scorer=fuzz.ratio)
    if match and match[1] >= 70:
        return COMMAND_MAP[match[0]]
    return None

def parse_syntax(text: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Analizador sintáctico robusto que usa spaCy para extraer verbo, determinante,
    nombre y dirección. Usa get_nlp() para asegurar lazy loading.
    """
    nlp = get_nlp()
    doc = nlp(text)
    verb = None
    det = None
    noun = None
    direction = None

    direction_words = {
        "izquierda": "left",
        "derecha": "right",
        "arriba": "up",
        "abajo": "down",
        "delante": "forward",
        "adelante": "forward",
        "atrás": "back",
        "atras": "back",
        "hacia": None
    }

    for token in doc:
        if token.pos_ == "VERB":
            verb = token.lemma_
            break

    for token in doc:
        if token.pos_ == "DET" and det is None:
            det = token.text
        if token.pos_ == "NOUN" and noun is None:
            noun = token.text
            if noun in direction_words:
                direction = direction_words[noun]
                break

    for token in doc:
        if token.text in direction_words:
            if direction_words[token.text]:
                direction = direction_words[token.text]
            if token.text == "hacia":
                # intentar lookahead
                try:
                    next_token = token.nbor(1)
                    if next_token.text in direction_words:
                        direction = direction_words[next_token.text]
                except Exception:
                    pass

    if verb is None and noun:
        if noun in ["pata", "mano"]:
            verb = "dar"
        if noun in ["cinco"]:
            verb = "chocar"

    return verb, det, noun, direction

def parse_command(text: str):
    """
    Función principal que normaliza, intenta mapeo directo por frase,
    y si no, usa análisis sintáctico y mapeo por palabra.
    """
    text_norm = normalize(text)
    action = map_action_from_text(text_norm)
    if action:
        return {"action": action, "object": None, "direction": None, "topic": text_norm}

    verb, det, noun, direction = parse_syntax(text_norm)
    action = None
    if verb:
        action = map_action_from_word(verb)
    if noun and not action:
        action = map_action_from_word(noun)
    if direction and not action:
        action = direction

    return {"action": action, "object": noun, "direction": direction, "topic": text_norm}