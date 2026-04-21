# stt/record_audio.py

import sounddevice as sd

def record_audio(duration=5, fs=44100):
    print("Grabando audio...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    print("Grabación completada.")
    return fs, audio.flatten()

if __name__ == "__main__":
    record_audio()
