import os
from datetime import datetime

from stt.record_audio import record_audio
from stt.whisper_stt import transcribe_audio
from stt.wake_word import listen_for_wake_word
from stt.tiago_spacy import process_file  # <-- IMPORTANTE

def main():
    print("Sistema listo. Di: 'Perro' para comenzar.")

    # Esperar palabra clave
    listen_for_wake_word()

    print("\nActivado. Grabando mensaje completo...")
    audio_file = record_audio(duration=5)

    # Transcribir
    text = transcribe_audio(audio_file)

    # Crear carpeta de transcripciones
    transcription_dir = "audio/transcriptions"
    os.makedirs(transcription_dir, exist_ok=True)

    # Crear nombre con fecha
    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
    transcription_path = os.path.join(transcription_dir, f"transcription_{fecha}.txt")

    # Guardar transcripción
    with open(transcription_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"\nTranscripción guardada en: {transcription_path}")
    print("Texto final:", text)

    # -------------------------------
    # PROCESAR CON TIAGO_SPACY_FILEPROCESSOR
    # -------------------------------
    topics_dir = "audio/topics"
    os.makedirs(topics_dir, exist_ok=True)

    topic_path = os.path.join(topics_dir, f"topic_{fecha}.txt")

    # Llamamos al procesador de spaCy
    process_file(transcription_path, topic_path)

    print(f"\nTopic generado en: {topic_path}")


if __name__ == "__main__":
    main()
