# stt/record_audio.py

import speech_recognition as sr

def record_audio(duration=3):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=0.5)
        audio = r.record(source, duration=duration)
    return audio


if __name__ == "__main__":
    record_audio()
