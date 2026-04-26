# stt/google_stt.py

import speech_recognition as sr
from gtts import gTTS
import pygame
import io


def transcribe_audio(audio_data):
    r = sr.Recognizer()
    try:
        text = r.recognize_google(audio_data, language='es-ES')
        print("Transcripción:", text)
        return text
    except Exception as e:
        print("Error en Google STT:", e)
        return ""

def generate_audio(texto):
    tts = gTTS(text=texto, lang='es')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    return fp


def reproduce_audio(audio_buffer):
    pygame.mixer.init()
    pygame.mixer.music.load(audio_buffer)
    pygame.mixer.music.play()

    # Esperar a que termine
    while pygame.mixer.music.get_busy():
        continue
