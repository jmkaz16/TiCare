import speech_recognition as sr
from gtts import gTTS
import pygame
import io
import time
import unicodedata
import spacy
from rapidfuzz import process, fuzz

TARGET_WAKE = "tiago"
_nlp = None


# ============================================================
#  MICRÓFONO: DETECCIÓN AUTOMÁTICA (SOLUCIÓN PARA UBUNTU)
# ============================================================

def get_microphone_index():
    """Devuelve el índice del micrófono real evitando dispositivos fantasma de ALSA."""
    try:
        devices = sr.Microphone.list_microphone_names()
        print("\n=== Dispositivos detectados ===")
        for i, name in enumerate(devices):
            print(f"{i}: {name}")

        # Seleccionar el primer dispositivo que NO sea "Monitor"
        for i, name in enumerate(devices):
            if "monitor" not in name.lower():
                print(f"\nUsando micrófono: {name} (index {i})")
                return i

        print("\nNo se encontró un micrófono claro, usando index 0")
        return 0

    except Exception as e:
        print("Error detectando micrófono:", e)
        return None


# ============================================================
#  STT — TRANSCRIPCIÓN
# ============================================================

def transcribe_audio(audio_data):
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


# ============================================================
#  TTS — SÍNTESIS DE VOZ
# ============================================================

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


# ============================================================
#  GRABACIÓN DE AUDIO 
# ============================================================

def record_audio(duration=3):
    r = sr.Recognizer()

    r.energy_threshold = 300
    r.dynamic_energy_threshold = True

    mic_index = get_microphone_index()

    sample_rates = [44100, 48000, 32000, 22050, 16000]

    for rate in sample_rates:
        try:
            with sr.Microphone(device_index=mic_index, sample_rate=rate) as source:
                r.adjust_for_ambient_noise(source, duration=0.5)
                print(f"Grabando {duration}s")
                audio = r.record(source, duration=duration)
                return audio

        except Exception as e:
            print(f"Falló sample_rate={rate}: {e}")
            continue

    print("ERROR: No se pudo abrir el micrófono con ningún sample_rate.")
    return None


# ============================================================
#  WAKE WORD
# ============================================================

def clean_wake_word(text):
    text = text.lower().strip()
    if TARGET_WAKE in text:
        cleaned = text.replace(TARGET_WAKE, "").strip(" ,.")
        return cleaned or ""
    return ""

def is_wake_word(text):
    text = text.lower().strip()

    if TARGET_WAKE in text:
        print("Wake-word encontrada dentro de la frase.")
        return True

    score = fuzz.ratio(text, TARGET_WAKE)
    print(f"Similitud con wake-word: {score}")

    return score > 70

def listen_for_wake_word(duration=3):
    while True:
        print("Grabando fragmento ... ")
        audio = record_audio(duration=duration)

        text = transcribe_audio(audio)
        if not text or text == "Errr":
            print("No se entendió nada.")
            continue

        text = text.lower().strip()
        print(f"Detectado: {text}")

        if is_wake_word(text):
            remaining = clean_wake_word(text)
            if remaining:
                print("Wake-word + orden detectada en la misma frase.")
                print(f"Orden detectada: {remaining}")
                return remaining

            print("¡Palabra clave detectada!")
            return ""


# ============================================================
#  NLP — spaCy
# ============================================================

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


# ============================================================
#  NORMALIZACIÓN
# ============================================================

def normalize(s: str) -> str:
    s = s.lower().strip()
    s = unicodedata.normalize("NFD", s)
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn")


# ============================================================
#  MAPEOS
# ============================================================

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


# ============================================================
#  DETECCIÓN DE GÉNERO
# ============================================================

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


# ============================================================
#  PARSER DE COMANDOS
# ============================================================

def parse_command(text: str):
    text_norm = normalize(text)
    nlp = get_nlp()
    doc = nlp(text_norm)

    # Acción por frase completa
    print(f"Text normalized: {text_norm}")
    action = map_action(text_norm)
    # Acción por palabra
    if not action:
        for token in doc:
            candidate = map_action(token.lemma_)
            if candidate:
                action = candidate
                break

    # Objeto → primer sustantivo
    obj = None
    for token in doc:
        if token.pos_ == "NOUN":
            obj = token.lemma_
            break

    # Lugar → fuzzy matching
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
