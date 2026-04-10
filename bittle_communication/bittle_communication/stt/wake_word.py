import whisper
import sounddevice as sd
import numpy as np
from rapidfuzz import fuzz

TARGET_WAKE = "perro"


def clean_wake_word(text):
    """
    Si la frase contiene la wake-word, la elimina y devuelve el resto.
    Ejemplo:
    "perro, levanta el culo" → "levanta el culo"
    """
    text = text.lower().strip()

    if TARGET_WAKE in text:
        # Quitar la wake-word y limpiar comas/espacios
        cleaned = text.replace(TARGET_WAKE, "").strip(" ,.")
        return cleaned if cleaned else None  # None si no hay orden después

    return None


def is_wake_word(text):
    text = text.lower().strip()

    # 1) Si contiene la wake-word → activamos
    if TARGET_WAKE in text:
        print("Wake-word encontrada dentro de la frase.")
        return True

    # 2) Fuzzy matching como respaldo
    score = fuzz.ratio(text, TARGET_WAKE)
    print(f"Similitud con wake-word: {score}")

    return score > 70


def listen_for_wake_word(duration=3, fs=16000):
    # listen_for_wake_word puede devolver:
    # - None -> salida/abort
    # - "" (cadena vacía) -> wake-word detectada sin orden en la misma frase
    # - "texto de la orden" -> wake-word + orden en la misma frase
    print("Escuchando la palabra clave ... (pulsa 'Ctrl+C' para salir)")

    model = whisper.load_model("small", device="cpu")

    while True:

        print("Grabando fragmento ...")
        audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
        sd.wait()

        audio = audio.flatten().astype(np.float32)

        result = model.transcribe(audio, language="es")
        text = result["text"].lower().strip()
        print(f"Detectado: {text}")

        if is_wake_word(text):
            # Ver si hay orden dentro de la misma frase
            remaining = clean_wake_word(text)

            if remaining:
                print("Wake-word + orden detectada en la misma frase.")
                print(f"Orden detectada: {remaining}")
                return remaining  # devolvemos la orden directamente

            print("¡Palabra clave detectada!")
            return ""  # indica que debe grabar la orden completa
