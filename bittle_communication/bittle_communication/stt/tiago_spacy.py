# stt/tiago_spacy.py

import unicodedata
from typing import Optional
import spacy
from rapidfuzz import process, fuzz

# Lazy loading del modelo
_nlp = None

def get_nlp():
    global _nlp
    if _nlp is not None:
        return _nlp
    try:
        _nlp = spacy.load("es_core_news_sm")
        print("spaCy cargado correctamente.")
    except Exception as e:
        print("spaCy no disponible, usando modelo en blanco:", e)
        _nlp = spacy.blank("es")
    return _nlp

# Normalización
def normalize(s: str) -> str:
    s = s.lower().strip()
    s = unicodedata.normalize("NFD", s)
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn")

# Cargar lugares desde input/places.txt
def load_places():
    try:
        with open("input/places.txt", "r", encoding="utf-8") as f:
            places = [normalize(line) for line in f.read().splitlines() if line.strip()]
        return set(places)
    except FileNotFoundError:
        print("⚠ No se encontró input/places.txt. No habrá detección de lugares.")
        return set()

PLACES = load_places()

# Mapeo de acciones
def map_action(text: str):
    from input.command_map import COMMAND_MAP
    choices = list(COMMAND_MAP.keys())
    match = process.extractOne(text, choices, scorer=fuzz.ratio)
    if match and match[1] >= 75:
        return COMMAND_MAP[match[0]]
    return None

# Parser principal
def parse_command(text: str):
    text_norm = normalize(text)
    nlp = get_nlp()
    doc = nlp(text_norm)

    # 1) Intento de acción por frase completa
    action = map_action(text_norm)

    # 2) Si no, intento por palabra
    if not action:
        for token in doc:
            candidate = map_action(token.lemma_)
            if candidate:
                action = candidate
                break

    # 3) Objeto → primer sustantivo relevante
    obj = None
    for token in doc:
        if token.pos_ == "NOUN":
            obj = token.lemma_
            break

    # 4) Lugar → cualquier palabra que coincida con PLACES
    place = None
    for token in doc:
        t = normalize(token.text)
        if t in PLACES:
            place = t
            break

    return {
        "action": action,
        "object": obj,
        "place": place,
        "topic": text_norm
    }