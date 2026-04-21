# stt/whisper_stt.py

import whisper

def transcribe_audio(audio_data):
    print("Cargando modelo Whisper...")
    model = whisper.load_model("base", device="cpu")
    print("Transcribiendo audio...")
    result = model.transcribe(audio_data, language="es")
    text = result["text"]
    print("Transcripción:", text)
    return text
