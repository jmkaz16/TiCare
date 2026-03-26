import os
from datetime import datetime

from stt.record_audio import record_audio
from stt.whisper_stt import transcribe_audio
from stt.wake_word import listen_for_wake_word
from stt.tiago_spacy import process_file


def main():
    print("Sistema listo. Di: 'Perro' para comenzar.")

    # ============================
    # 1. Esperar palabra clave
    # ============================
    listen_for_wake_word()

    print("\nActivado. Grabando mensaje completo ... ")
    audio_file = record_audio(duration=5)

    # ============================
    # 2. Transcribir audio
    # ============================
    text = transcribe_audio(audio_file)

    # Crear carpeta de transcripciones
    transcription_dir = "audio/transcriptions"
    os.makedirs(transcription_dir, exist_ok=True)

    # Crear nombre con fecha
    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
    transcription_path = os.path.join(
        transcription_dir,
        f"transcription_{fecha}.txt"
    )

    # Guardar transcripción
    with open(transcription_path, "w", encoding="utf-8") as f:
        f.write(text)

    print("Texto final:", text)

    # ============================
    # 3. Procesar con spaCy (topic)
    # ============================
    topics_dir = "audio/topics"
    os.makedirs(topics_dir, exist_ok=True)

    topic_path = os.path.join(topics_dir, f"topic_{fecha}.txt")

    process_file(transcription_path, topic_path)

    # ============================
    # 4. Generar archivo de ORDEN
    # ============================
    orders_dir = "audio/orders"
    os.makedirs(orders_dir, exist_ok=True)

    # Leer el topic generado
    with open(topic_path, "r", encoding="utf-8") as f:
        topic_text = f.read().strip()

    # Extraer Acción, Objeto y Topic
    accion = None
    objeto = None
    topic_line = None

    for line in topic_text.splitlines():
        if line.lower().startswith("acción:"):
            accion = line.split(":", 1)[1].strip()
        elif line.lower().startswith("objeto:"):
            objeto = line.split(":", 1)[1].strip()
        elif line.lower().startswith("topic:"):
            topic_line = line.split(":", 1)[1].strip()

    # Crear archivo de orden con fecha
    order_path = os.path.join(orders_dir, f"order_{fecha}.txt")

    with open(order_path, "w", encoding="utf-8") as f:
        f.write(f"Acción: {accion}\n")
        f.write(f"Objeto: {objeto}\n")
        f.write(f"Topic: {topic_line}\n")

    print(f"\nOrden generada")


if __name__ == "__main__":
    main()
