import speech_recognition as sr
from gtts import gTTS
import pygame
import io
import time
import unicodedata
import spacy
from rapidfuzz import process, fuzz

from command_map import (
    COMMAND_MAP,
    PLACES_MAP,
    OBJECTS_MAP,
    YES_MAP,
    NO_MAP,
    STOP_MAP,
)

_nlp = None
_cached_mic_index = None
_cached_sample_rate = None


# ==========================
# Utilidades generales
# ==========================

def normalize(s: str) -> str:
    s = s.lower().strip()
    s = unicodedata.normalize("NFD", s)
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn")


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


# ==========================
# Micrófono / audio
# ==========================

def get_microphone_index():
    global _cached_mic_index
    if _cached_mic_index is not None:
        return _cached_mic_index

    try:
        devices = sr.Microphone.list_microphone_names()
        print("\n=== Dispositivos detectados ===")
        for i, name in enumerate(devices):
            print(f"{i}: {name}")

        for i, name in enumerate(devices):
            if "monitor" not in name.lower():
                print(f"\nUsando micrófono: {name} (index {i})")
                _cached_mic_index = i
                return _cached_mic_index

        print("\nNo se encontró un micrófono claro, usando index 0")
        _cached_mic_index = 0
        return _cached_mic_index

    except Exception as e:
        print("Error detectando micrófono:", e)
        _cached_mic_index = None
        return None


def record_audio(duration=3):
    global _cached_sample_rate

    r = sr.Recognizer()
    r.energy_threshold = 300
    r.dynamic_energy_threshold = True

    mic_index = get_microphone_index()
    if mic_index is None:
        print("No hay micrófono disponible.")
        return None

    # Si ya tenemos un sample_rate válido, úsalo directamente
    if _cached_sample_rate is not None:
        try:
            with sr.Microphone(device_index=mic_index, sample_rate=_cached_sample_rate) as source:
                print(f"Usando micrófono index {mic_index} con sample_rate={_cached_sample_rate}")
                r.adjust_for_ambient_noise(source, duration=0.5)
                print(f"Grabando {duration} segundos...")
                audio = r.record(source, duration=duration)
                return audio
        except Exception as e:
            print(f"Falló sample_rate cacheado ({_cached_sample_rate}): {e}")
            _cached_sample_rate = None  # forzar re-detección

    # Detectar sample_rate válido
    sample_rates = [44100, 48000, 32000, 22050, 16000]
    for rate in sample_rates:
        try:
            print(f"Intentando abrir micrófono {mic_index} con sample_rate={rate}...")
            with sr.Microphone(device_index=mic_index, sample_rate=rate) as source:
                r.adjust_for_ambient_noise(source, duration=0.5)
                print(f"Grabando {duration} segundos con sample_rate={rate}...")
                audio = r.record(source, duration=duration)
                _cached_sample_rate = rate
                return audio
        except Exception as e:
            print(f"Falló sample_rate={rate}: {e}")
            continue

    print("ERROR: No se pudo abrir el micrófono con ningún sample_rate.")
    return None


# ==========================
# STT / TTS
# ==========================

def transcribe_audio(audio_data):
    if audio_data is None:
        return "Errr"
    r = sr.Recognizer()
    try:
        text = r.recognize_google(audio_data, language='es-ES')
        print("Transcripción:", text)
        return text
    except sr.UnknownValueError:
        return "Errr"
    except Exception as e:
        print("Error en reconocimiento:", e)
        return "Errr"


def speak_audio(texto):
    tts = gTTS(text=texto, lang='es')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)

    pygame.mixer.init()
    pygame.mixer.music.load(fp)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        time.sleep(0.1)


# ==========================
# Wake word (parametrizada)
# ==========================

def clean_wake_word(text, wake_word):
    text = text.lower().strip()
    if wake_word in text:
        cleaned = text.replace(wake_word, "").strip(" ,.")
        return cleaned or ""
    return ""


def is_wake_word(text, wake_word):
    text = text.lower().strip()
    if wake_word in text:
        print("Wake-word encontrada dentro de la frase.")
        return True

    score = fuzz.ratio(text, wake_word)
    print(f"Similitud con wake-word: {score}")
    return score > 70


def listen_for_wake_word(wake_word, duration=3):
    while True:
        print("Grabando fragmento ... ")
        audio = record_audio(duration=duration)
        if audio is None:
            print("No se pudo grabar audio, reintentando...")
            continue

        text = transcribe_audio(audio)
        if not text or text == "Errr":
            print("No se entendió nada.")
            continue

        text = text.lower().strip()
        print(f"Detectado: {text}")

        if is_wake_word(text, wake_word):
            remaining = clean_wake_word(text, wake_word)
            if remaining:
                print("Wake-word + orden detectada en la misma frase.")
                print(f"Orden detectada: {remaining}")
                return remaining
            print("¡Palabra clave detectada!")
            return ""


# ==========================
# Fuzzy mapeos
# ==========================

def map_action(text: str):
    choices = list(COMMAND_MAP.keys())
    match = process.extractOne(text, choices, scorer=fuzz.ratio)
    if match and match[1] >= 75:
        return COMMAND_MAP[match[0]]
    return None


def map_place(word: str):
    choices = list(PLACES_MAP.keys())
    match = process.extractOne(word, choices, scorer=fuzz.ratio)
    if match and match[1] >= 75:
        return PLACES_MAP[match[0]]
    return None


def map_object(text: str):
    choices = list(OBJECTS_MAP.keys())
    match = process.extractOne(text, choices, scorer=fuzz.ratio)
    if match and match[1] >= 75:
        return OBJECTS_MAP[match[0]]
    return None


def classify_answer(text: str):
    text_norm = normalize(text)

    yes_match = process.extractOne(text_norm, YES_MAP.keys(), scorer=fuzz.ratio)
    if yes_match and yes_match[1] >= 75:
        return "yes"

    no_match = process.extractOne(text_norm, NO_MAP.keys(), scorer=fuzz.ratio)
    if no_match and no_match[1] >= 75:
        return "no"

    return "unknown"


def classify_stop(text: str):
    text_norm = normalize(text)
    match = process.extractOne(text_norm, STOP_MAP.keys(), scorer=fuzz.ratio)
    if match and match[1] >= 75:
        return True
    return False


# ==========================
# NLP: género y parsing
# ==========================

def get_article(word: str):
    """
    Devuelve el artículo correcto (el, la, los, las) según género y número.
    """
    nlp = get_nlp()
    doc = nlp(word)
    if not doc:
        return "el"  # fallback

    token = doc[0]

    gender = token.morph.get("Gender")
    number = token.morph.get("Number")

    if "Fem" in gender:
        return "las" if "Plur" in number else "la"
    elif "Masc" in gender:
        return "los" if "Plur" in number else "el"
    else:
        return "el"  # fallback neutro



def parse_command(text: str):
    text_norm = normalize(text)
    nlp = get_nlp()
    doc = nlp(text_norm)

    # Acción: primero por frase completa, luego por tokens
    action = map_action(text_norm)
    if not action:
        for token in doc:
            candidate = map_action(token.lemma_)
            if candidate:
                action = candidate
                break

    # Objeto: fuzzy por frase completa, luego por tokens
    obj = map_object(text_norm)
    if not obj:
        for token in doc:
            candidate = map_object(token.lemma_)
            if candidate:
                obj = candidate
                break

    # Lugar: por tokens
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
        "topic": text_norm,
    }
