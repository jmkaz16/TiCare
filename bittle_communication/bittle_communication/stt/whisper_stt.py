# stt/whisper_stt.py

import whisper

model = whisper.load_model("small", device="cpu")
def transcribe_audio(audio_data):
    
    result = model.transcribe(audio_data, language="es")
    
    text = result["text"]
    print("Transcripción:", text)
    return text
