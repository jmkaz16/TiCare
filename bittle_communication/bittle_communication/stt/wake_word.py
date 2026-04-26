import numpy as np
from rapidfuzz import fuzz
from stt.whisper_stt import transcribe_audio
from stt.record_audio import record_audio

TARGET_WAKE = "tiago"

def clean_wake_word(text):
    text = text.lower().strip()
    if TARGET_WAKE in text:
        cleaned = text.replace(TARGET_WAKE, "").strip(" ,.")
        return cleaned if cleaned else None
    return None

def is_wake_word(text):
    text = text.lower().strip()

    if TARGET_WAKE in text:
        print("Wake-word encontrada dentro de la frase.")
        return True

    score = fuzz.ratio(text, TARGET_WAKE)
    print(f"Similitud con wake-word: {score}")

    return score > 70

def listen_for_wake_word(duration=3, fs=16000):
    while True:
        print("Grabando fragmento ... ")
        fs, audio = record_audio(duration=duration, fs=fs)

        text = transcribe_audio(audio).lower().strip()
        print(f"Detectado: {text}")

        if is_wake_word(text):
            remaining = clean_wake_word(text)
            if remaining:
                print("Wake-word + orden detectada en la misma frase.")
                print(f"Orden detectada: {remaining}")
                return remaining

            print("¡Palabra clave detectada!")
            return ""