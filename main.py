import os
from datetime import datetime

from stt.record_audio import record_audio
from stt.whisper_stt import transcribe_audio
from stt.wake_word import listen_for_wake_word
from stt.tiago_spacy import parse_command


def main():
    print("Sistema listo. Di: 'Perro' para comenzar.")

    # ============================
    # 1. Detectar wake-word
    # ============================
    wake_result = listen_for_wake_word()

    # Si wake_result contiene texto → ya es la orden
    if wake_result:
        print("\nOrden detectada dentro de la frase de activación.")
        text = wake_result

    else:
        # ============================
        # 2. Grabar mensaje completo
        # ============================
        print("\nActivado. Grabando mensaje completo ... ")
        audio_file = record_audio(duration=5)

        # ============================
        # 3. Transcribir audio
        # ============================
        text = transcribe_audio(audio_file)

    # Crear timestamp
    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ============================
    # 4. Guardar transcripción
    # ============================
    transcription_dir = "audio/transcriptions"
    os.makedirs(transcription_dir, exist_ok=True)

    transcription_path = os.path.join(
        transcription_dir,
        f"transcription_{fecha}.txt"
    )

    with open(transcription_path, "w", encoding="utf-8") as f:
        f.write(text)

    print("Texto final:", text)

    # ============================
    # 5. Procesar con spaCy + fuzzy
    # ============================
    topics_dir = "audio/topics"
    os.makedirs(topics_dir, exist_ok=True)

    topic_path = os.path.join(topics_dir, f"topic_{fecha}.txt")

    result = parse_command(text)

    with open(topic_path, "w", encoding="utf-8") as f:
        f.write(f"Acción: {result['action']}\n")
        f.write(f"Objeto: {result['object']}\n")
        f.write(f"Topic: {result['topic']}\n")

    # ============================
    # 6. Guardar ORDEN final
    # ============================
    orders_dir = "audio/orders"
    os.makedirs(orders_dir, exist_ok=True)

    order_path = os.path.join(orders_dir, f"order_{fecha}.txt")

    with open(order_path, "w", encoding="utf-8") as f:
        f.write(f"Acción: {result['action']}\n")
        f.write(f"Objeto: {result['object']}\n")
        f.write(f"Topic: {result['topic']}\n")


if __name__ == "__main__":
    main()