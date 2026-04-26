# stt/tiago_spacy.py

import unicodedata
import spacy
from rapidfuzz import process, fuzz

_nlp = None

def get_nlp():
    global _nlp
    if _nlp is not None:
        return _nlp
    try:
        _nlp = spacy.load("es_core_news_sm")
    except Exception as e:
        print("spaCy no disponible, usando modelo en blanco:", e)
        _nlp = spacy.blank("es")
    return _nlp

def normalize(s: str) -> str:
    s = s.lower().strip()
    s = unicodedata.normalize("NFD", s)
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn")

def map_action(text: str):
    from input.command_map import COMMAND_MAP
    choices = list(COMMAND_MAP.keys())
    match = process.extractOne(text, choices, scorer=fuzz.ratio)
    if match and match[1] >= 75:
        return COMMAND_MAP[match[0]]
    return None

def map_place(word: str):
    from input.command_map import PLACES_MAP
    choices = list(PLACES_MAP.keys())
    match = process.extractOne(word, choices, scorer=fuzz.ratio)
    if match and match[1] >= 75:
        return PLACES_MAP[match[0]]
    return None

def detect_gender(palabra: str):
    nlp = get_nlp()
    doc = nlp(palabra)
    token = doc[0]

    genero = token.morph.get("Gender")

    if "Fem" in genero:
        return "femenino"
    elif "Masc" in genero:
        return "masculino"
    else:
        return "desconocido"

def parse_command(text: str):
    text_norm = normalize(text)
    nlp = get_nlp()
    doc = nlp(text_norm)

    # 1) Acción por frase completa
    action = map_action(text_norm)

    # 2) Acción por palabra
    if not action:
        for token in doc:
            candidate = map_action(token.lemma_)
            if candidate:
                action = candidate
                break

    # 3) Objeto → primer sustantivo
    obj = None
    for token in doc:
        if token.pos_ == "NOUN":
            obj = token.lemma_
            break

    # 4) Lugar → fuzzy matching con PLACES_MAP
    place = None
    for token in doc:
        candidate = map_place(token.lemma_)
        if candidate:
            place = candidate
            break

    return {
        "action": action,
        "object": obj,
        "place": place,
        "topic": text_norm
    }