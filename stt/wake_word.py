import whisper
import sounddevice as sd
import numpy as np
import keyboard
from rapidfuzz import fuzz

TARGET_WAKE = "Paicaché"  # la palabra clave que quieres detectar

def is_wake_word(text):
    text = text.lower().strip()
    score = fuzz.ratio(text, TARGET_WAKE)
    print(f"Similitud con wake-word: {score}")

    return score > 70  # puedes ajustar este umbral

def listen_for_wake_word(duration=3, fs=16000):
    print("Escuchando la palabra clave... (pulsa 's' para salir)")

    model = whisper.load_model("small")  # más preciso que tiny

    while True:
        if keyboard.is_pressed("s"):
            print("Detenido por el usuario. Saliendo...")
            return False

        print("Grabando fragmento...")
        audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
        sd.wait()

        audio = audio.flatten().astype(np.float32)

        result = model.transcribe(audio, language="es")
        text = result["text"].lower().strip()

        print(f"Detectado: {text}")

        if is_wake_word(text):
            print("¡Palabra clave detectada!")
            return True
