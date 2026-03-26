import os
from stt.record_audio import record_audio
from stt.whisper_stt import transcribe_audio
from stt.wake_word import listen_for_wake_word
from stt.tiago_spacy import parse_command


def main():
    print("Sistema listo. Di: 'Perro' para comenzar.")

    # Crear carpeta state si no existe
    os.makedirs("state", exist_ok=True)

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

        # Guardar audio siempre como el mismo archivo
        audio_path = "state/audio.wav"
        os.replace(audio_file, audio_path)

        # ============================
        # 3. Transcribir audio
        # ============================
        text = transcribe_audio(audio_path)

    # ============================
    # 4. Guardar transcripción (SIEMPRE MISMO ARCHIVO)
    # ============================
    transcription_path = "state/transcription.txt"

    with open(transcription_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"\nTranscripción guardada en: {transcription_path}")
    print("Texto final:", text)

    # ============================
    # 5. Procesar con spaCy + fuzzy
    # ============================
    topic_path = "state/topic.txt"

    result = parse_command(text)

    # Si parse_command devolvió None, creamos un resultado vacío
    if result is None:
        result = {
            "action": None,
            "object": None,
            "topic": text
        }

    with open(topic_path, "w", encoding="utf-8") as f:
        f.write(f"Acción: {result['action']}\n")
        f.write(f"Objeto: {result['object']}\n")
        f.write(f"Topic: {result['topic']}\n")

    print(f"\nTopic generado en: {topic_path}")

    # ============================
    # 6. Guardar ORDEN final (SIEMPRE MISMO ARCHIVO)
    # ============================
    order_path = "state/order.txt"

    with open(order_path, "w", encoding="utf-8") as f:
        f.write(f"Acción: {result['action']}\n")
        f.write(f"Objeto: {result['object']}\n")
        f.write(f"Topic: {result['topic']}\n")

    print(f"\nOrden generada en: {order_path}")


if __name__ == "__main__":
    main()