# stt/record_audio.py

import sounddevice as sd
import numpy as np

def record_audio(duration=5, fs=16000):
    print("Grabando audio...")
    audio = sd.rec(
        int(duration * fs),
        samplerate=fs,
        channels=1,
        dtype='float32'
    )
    sd.wait()
    print("Grabación completada.")

    # Asegurar formato correcto
    audio = audio.flatten().astype(np.float32)

    return fs, audio


if __name__ == "__main__":
    record_audio()
