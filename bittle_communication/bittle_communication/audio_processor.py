# audio_processor.py

import warnings
from stt.record_audio import record_audio
from stt.whisper_stt import transcribe_audio
from stt.wake_word import listen_for_wake_word
from stt.tiago_spacy import parse_command

# Duración de la grabación en segundos
DURATION = 5

# Suprimir avisos de Whisper
warnings.filterwarnings("ignore", message="Performing inference on CPU when CUDA is available")
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

def main() -> None:
    print("Sistema listo. Di la wake-word para comenzar.")

    # 1) Detectar wake-word
    wake_result = listen_for_wake_word()

    if wake_result is None:
        print("No se detectó activación o se solicitó salida. Terminando.")
        return

    if wake_result:
        # Wake-word + orden en la misma frase
        print("\nOrden detectada en la frase de activación.")
        text = wake_result
    else:
        # Solo wake-word → grabamos la orden completa
        print(f"\nActivado. Grabando mensaje durante {DURATION} segundos...")
        fs, audio_data = record_audio(duration=DURATION)

        # Transcribir audio en memoria
        text = transcribe_audio(audio_data)

    # Mostrar transcripción
    print(f"\nTranscripción detectada: {repr(text)}")

    # Interpretar con el parser final
    parsed = parse_command(text)
    action = parsed.get("action")
    obj = parsed.get("object")
    place = parsed.get("place")

    # Mostrar resultados por consola
    print("\n --- ACCIÓN DETECTADA --- ")
    print(".", action)

    print("\n --- OBJETO DETECTADO --- ")
    print(".", obj)

    print("\n --- LUGAR DETECTADO --- ")
    print(".", place)

    print("\nProceso completado.")

if __name__ == "__main__":
    main()