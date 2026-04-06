# main.py
# Programa principal que:
# 1) Detecta la wake-word (o recibe la orden directamente si viene en la misma frase)
# 2) Graba audio si es necesario
# 3) Transcribe con Whisper
# 4) Aplica semantic chunking para dividir la frase en múltiples órdenes
# 5) Procesa cada chunk con el parser (tiago_spacy.parse_command)
# 6) Guarda el resultado en archivos dentro de state/ para que otros módulos los consuman

import os
import json

# Importar módulos del proyecto
from stt.record_audio import record_audio
from stt.whisper_stt import transcribe_audio
from stt.wake_word import listen_for_wake_word
from stt.tiago_spacy import parse_command
from stt.semantic_chunk import semantic_chunk

def ensure_state_dir():
    """
    Asegura que exista la carpeta 'state' donde guardamos archivos
    persistentes (audio, transcripción, topic, order).
    """
    os.makedirs("state", exist_ok=True)

def save_transcription(text: str, path: str = "state/transcription.txt"):
    """
    Guarda la transcripción en un archivo de texto (sobrescribe siempre).
    """
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def save_topic(result: dict, path: str = "state/topic.txt"):
    """
    Guarda un resumen legible del parseo del primer chunk (útil para debugging).
    Si hay múltiples resultados, se guarda el primero y el topic original.
    """
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"Acción: {result.get('action')}\n")
        f.write(f"Objeto: {result.get('object')}\n")
        f.write(f"Dirección: {result.get('direction')}\n")
        f.write(f"Topic: {result.get('topic')}\n")

def save_orders_list(results: list, path_txt: str = "state/order.txt", path_json: str = "state/orders.json"):
    """
    Guarda la lista de órdenes (una por línea) en order.txt y además
    en formato JSON en orders.json con más detalle.
    Cada elemento de results es el diccionario devuelto por parse_command.
    """
    # Guardar solo las acciones en order.txt (una por línea). Si action es None,
    # escribimos 'None' para que el consumidor sepa que no se detectó acción.
    with open(path_txt, "w", encoding="utf-8") as f:
        for r in results:
            action = r.get("action") if r else None
            f.write(f"{action}\n")

    # Guardar JSON con más detalle (lista de dicts)
    with open(path_json, "w", encoding="utf-8") as f:
        json.dump({"orders": results}, f, ensure_ascii=False, indent=2)

def main():
    """
    Flujo principal:
    - Espera wake-word
    - Si la orden viene junto con la wake-word, la procesa directamente
    - Si no, graba audio, transcribe y procesa
    - Aplica semantic_chunk para dividir en múltiples órdenes
    - Procesa cada chunk con parse_command
    - Guarda resultados en state/
    """
    print("Sistema listo. Di: 'Perro' para comenzar.")

    ensure_state_dir()

    # 1) Detectar wake-word (puede devolver:
    #    - None -> no activado (por ejemplo, usuario pulsó 's' para salir)
    #    - "" (cadena vacía) -> wake-word detectada, pero sin orden en la misma frase
    #    - "texto de la orden" -> wake-word + orden en la misma frase
    wake_result = listen_for_wake_word()

    if wake_result is None:
        # Salida controlada por el usuario o error en la escucha
        print("No se detectó activación. Saliendo.")
        return

    if wake_result:
        # Caso: wake-word y orden en la misma frase
        print("\nOrden detectada dentro de la frase de activación.")
        text = wake_result
    else:
        # Caso: solo wake-word -> grabamos la orden completa
        print("\nActivado. Grabando mensaje completo ... ")
        audio_file = record_audio(duration=5)

        # Normalizamos la ubicación del audio para el pipeline
        audio_path = "state/audio.wav"
        # Reemplazamos (mueve/renombra) el archivo grabado a state/audio.wav
        os.replace(audio_file, audio_path)

        # 3) Transcribir audio
        text = transcribe_audio(audio_path)

        # 4) Guardar transcripción
        save_transcription(text)

    # Mostrar texto final por consola para debugging
    print("Texto final:", text)

    # 5) Semantic chunking: dividir la frase en múltiples órdenes
    chunks = semantic_chunk(text)

    # 6) Procesar cada chunk con el parser (tiago_spacy.parse_command)
    results = []
    for ch in chunks:
        # parse_command devuelve un dict con keys: action, object, direction, topic
        parsed = parse_command(ch)
        # Si parse_command devolviera None, normalizamos a un dict vacío
        if parsed is None:
            parsed = {"action": None, "object": None, "direction": None, "topic": ch}
        results.append(parsed)

    # 7) Guardar topic y órdenes
    # Guardamos el primer resultado en topic.txt para compatibilidad con el sistema anterior
    if results:
        save_topic(results[0])
    else:
        save_topic({"action": None, "object": None, "direction": None, "topic": text})

    # Guardar todas las órdenes en order.txt (una por línea) y en orders.json
    save_orders_list(results)

    print("\nÓrdenes generadas y guardadas en state/ (order.txt y orders.json).")

if __name__ == "__main__":
    main()