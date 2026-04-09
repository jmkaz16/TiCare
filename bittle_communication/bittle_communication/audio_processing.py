import os
import time
from typing import List, Optional

from stt.record_audio import record_audio
from stt.whisper_stt import transcribe_audio
from stt.wake_word import listen_for_wake_word
from stt.tiago_spacy import parse_command
from stt.semantic_chunk import semantic_chunk

from ament_index_python.packages import get_package_share_directory

# -------------------------
# Configuración / utilidades
# -------------------------
STATE_DIR = os.path.join(get_package_share_directory("bittle_communication"), "state")
AUDIO_PATH = os.path.join(STATE_DIR, "audio.wav")
TOPIC_PATH = os.path.join(STATE_DIR, "topic.txt")
ORDER_PATH = os.path.join(STATE_DIR, "order.txt")

# Duración de la grabación en segundos.
DURATION = 5  # segundos


def ensure_state_dir() -> None:
    """
    Asegura que exista la carpeta 'state' donde guardamos artefactos mínimos.
    """
    os.makedirs(STATE_DIR, exist_ok=True)


def save_topic_chunks(chunks: List[str], path: str = TOPIC_PATH) -> None:
    """
    Guarda todos los chunks detectados en topic.txt, uno por línea.
    Si la lista está vacía, escribe la transcripción original pasada como único elemento.
    """
    with open(path, "w", encoding="utf-8") as f:
        for c in chunks:
            line = c.strip()
            if line:
                f.write(line + "\n")


def save_orders(actions: List[Optional[str]], path: str = ORDER_PATH) -> None:
    """
    Guarda únicamente la acción de cada chunk en order.txt, una por línea.
    Si una acción es None o vacía, escribe una línea vacía para mantener la correspondencia.
    """
    while os.path.exists(os.path.join(STATE_DIR, "order.lock")):
        time.sleep(0.1)  # Espera a que el lock se libere

    open(os.path.join(STATE_DIR, "order.lock"), "w").close()
    with open(path, "w", encoding="utf-8") as f:
        for a in actions:
            if a is None:
                f.write("\n")
            else:
                f.write(str(a).strip() + "\n")
    os.remove(os.path.join(STATE_DIR, "order.lock"))


# -------------------------
# Flujo principal
# -------------------------
def main() -> None:
    """
    Flujo principal:
    1) Espera wake-word (o recibe orden en la misma frase).
    2) Si la orden no viene en la activación, graba audio y lo transcribe.
    3) Aplica semantic_chunk para dividir la frase en órdenes (chunks).
    4) Procesa cada chunk con parse_command y guarda:
       - topic.txt: todos los chunks (uno por línea)
       - order.txt: solo la acción de cada chunk (uno por línea)
    """
    print("Sistema listo. Di la wake-word para comenzar.")

    ensure_state_dir()  # Aseguramos que exista la carpeta para guardar archivos

    # 1) Detectar wake-word
    wake_result = listen_for_wake_word()

    if wake_result is None:
        print("No se detectó activación o se solicitó salida. Terminando.")
        return

    if wake_result:
        # Wake-word y orden en la misma frase
        print("\nOrden detectada en la frase de activación.")
        text = wake_result
    else:
        # Solo wake-word -> grabamos la orden completa
        print(f"\nActivado. Grabando mensaje durante {DURATION} segundos...")
        audio_file = record_audio(duration=DURATION)  # usa la variable DURATION

        # Intentar mover/renombrar el audio al path dentro de state
        try:
            os.replace(audio_file, AUDIO_PATH)
            audio_path = AUDIO_PATH
        except Exception:
            audio_path = audio_file

        # Transcribir audio (no se guarda en disco)
        text = transcribe_audio(audio_path)

    # Mostrar la transcripción en consola para debugging
    print(f"\nTranscripción detectada: {repr(text)}")

    # 4) Semantic chunking
    chunks = semantic_chunk(text)  # lista de strings (puede ser 1 elemento con todo el texto)

    # 5) Procesar cada chunk con parse_command y extraer la acción
    parsed_results = []
    actions: List[Optional[str]] = []
    for ch in chunks:
        parsed = parse_command(ch)
        if parsed is None:
            parsed = {"action": None, "object": None, "direction": None, "topic": ch}
        parsed_results.append(parsed)
        # Extraer la acción; si no existe, guardamos None para escribir línea vacía
        action = parsed.get("action") if isinstance(parsed, dict) else None
        actions.append(action)

    # Si no se detectaron chunks (lista vacía), tratamos el texto completo como único chunk
    if not chunks:
        # Guardar topic con la transcripción completa
        save_topic_chunks([text])
        # Intentar parsear la transcripción completa y guardar su acción
        parsed_full = parse_command(text)
        action_full = parsed_full.get("action") if isinstance(parsed_full, dict) else None
        save_orders([action_full])
    else:
        # Guardar todos los chunks en topic.txt
        save_topic_chunks(chunks)
        # Guardar solo las acciones en order.txt (una por línea)
        save_orders(actions)

    print("\nProceso completado.")


if __name__ == "__main__":
    main()
