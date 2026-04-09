import os
import time
from typing import List, Optional

import rclpy
from rclpy.node import Node

from bittle_communication.stt.record_audio import record_audio
from bittle_communication.stt.whisper_stt import transcribe_audio
from bittle_communication.stt.wake_word import listen_for_wake_word
from bittle_communication.stt.tiago_spacy import parse_command
from bittle_communication.stt.semantic_chunk import semantic_chunk


class AudioProcessor(Node):
    def __init__(self):
        super().__init__("audio_processor")

        # Configuración de rutas y parámetros
        self.declare_parameter("recording_duration", 5)  # duración de la grabación en segundos

        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.get_logger().info(f"AudioProcessor iniciado. Current directory: {self.current_dir}")
        self.state_dir = os.path.join(self.current_dir, "..", "state")

        self.audio_path = os.path.join(self.state_dir, "audio.wav")
        self.topic_path = os.path.join(self.state_dir, "topic.txt")
        self.order_path = os.path.join(self.state_dir, "order.txt")

        self.duration = self.get_parameter("recording_duration").get_value()

    def ensure_state_dir(self) -> None:
        """
        Asegura que exista la carpeta 'state' donde guardamos artefactos mínimos.
        """
        os.makedirs(self.state_dir, exist_ok=True)

    def save_topic_chunks(self, chunks: List[str], path: str = self.topic_path) -> None:
        """
        Guarda todos los chunks detectados en topic.txt, uno por línea.
        Si la lista está vacía, escribe la transcripción original pasada como único elemento.
        """
        with open(path, "w", encoding="utf-8") as f:
            for c in chunks:
                line = c.strip()
                if line:
                    f.write(line + "\n")

    def save_orders(self, actions: List[Optional[str]], path: str = self.order_path) -> None:
        """
        Guarda únicamente la acción de cada chunk en order.txt, una por línea.
        Si una acción es None o vacía, escribe una línea vacía para mantener la correspondencia.
        """
        while os.path.exists(os.path.join(self.state_dir, "order.lock")):
            time.sleep(0.1)  # Espera a que el lock se libere

        open(os.path.join(self.state_dir, "order.lock"), "w").close()
        with open(path, "w", encoding="utf-8") as f:
            for a in actions:
                if a is None:
                    f.write("\n")
                else:
                    f.write(str(a).strip() + "\n")
        os.remove(os.path.join(self.state_dir, "order.lock"))

    # -------------------------
    # Flujo principal
    # -------------------------

    def run_loop(self) -> None:
        """
        Flujo principal:
        1) Espera wake-word (o recibe orden en la misma frase).
        2) Si la orden no viene en la activación, graba audio y lo transcribe.
        3) Aplica semantic_chunk para dividir la frase en órdenes (chunks).
        4) Procesa cada chunk con parse_command y guarda:
        - topic.txt: todos los chunks (uno por línea)
        - order.txt: solo la acción de cada chunk (uno por línea)
        """
        self.get_logger().info("Sistema listo. Di la wake-word para comenzar.")

        self.ensure_state_dir()  # Aseguramos que exista la carpeta para guardar archivos

        # 1) Detectar wake-word
        wake_result = listen_for_wake_word()

        if wake_result is None:
            self.get_logger().warn("No se detectó activación o se solicitó salida. Terminando.")
            return

        if wake_result:
            # Wake-word y orden en la misma frase
            self.get_logger().info("Orden detectada en la frase de activación.")
            text = wake_result
        else:
            # Solo wake-word -> grabamos la orden completa
            self.get_logger().info(f"\nActivado. Grabando mensaje durante {self.duration} segundos...")
            audio_file = record_audio(duration=self.duration)  # usa la variable DURATION

            # Intentar mover/renombrar el audio al path dentro de state
            try:
                os.replace(audio_file, self.audio_path)
                audio_path = audio_path
            except Exception:
                audio_path = audio_file

            # Transcribir audio (no se guarda en disco)
            text = transcribe_audio(audio_path)

        # Mostrar la transcripción en consola para debugging
        self.get_logger().info(f"Transcripción detectada: {repr(text)}")

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
            self.save_topic_chunks([text])
            # Intentar parsear la transcripción completa y guardar su acción
            parsed_full = parse_command(text)
            action_full = parsed_full.get("action") if isinstance(parsed_full, dict) else None
            self.save_orders([action_full])
        else:
            # Guardar todos los chunks en topic.txt
            self.save_topic_chunks(chunks)
            # Guardar solo las acciones en order.txt (una por línea)
            self.save_orders(actions)

        self.get_logger().info("\nProceso completado.")


def main(args=None):
    rclpy.init(args=args)
    audio_processor = AudioProcessor()

    try:
        audio_processor.run_loop()
    except KeyboardInterrupt:
        pass
    finally:
        audio_processor.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
