# stt/whisper_stt.py

import speech_recognition as sr


def transcribe_audio(audio_data):
    
    result = sr.Recognizer().recognize_google(audio_data, language='es-ES')
    
    text = result["text"]
    print("Transcripción:", text)
    return text
