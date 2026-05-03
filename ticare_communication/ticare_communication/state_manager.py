"""
TiCare Communication Module - State Manager.

This node implements a 13-state machine to coordinate voice recognition,
natural language processing, and robot behavior via Vision and Navigation.
"""

import threading
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor

# === IMPORTAMOS LAS FUNCIONES EXACTAMENTE COMO EN LA OLD STATE MACHINE ===
from ticare_communication.scripts.stt_communication import (
    transcribe_audio,
    speak_audio,
    record_audio,
    listen_for_wake_word,
    parse_command,
    get_article,
    classify_answer,
    classify_stop,
)

from ticare_communication.scripts.command_map import (
    COMMAND_MAP,
    PLACES_MAP,
)

WAKE_WORD = "tiago"


class TiagoStateMachine(Node):

    def __init__(self):
        super().__init__("state_machine_node")

        self.group = ReentrantCallbackGroup()

        # --- PUBLISHERS ---
        self.vis_pub = self.create_publisher(String, "/com2vis", 10)
        self.nav_pub = self.create_publisher(String, "/com2nav", 10)

        # --- SUBSCRIBERS ---
        self.vis_sub = self.create_subscription(
            String,
            "/vis2com",
            self.vision_callback,
            10,
            callback_group=self.group,
        )

        self.nav_sub = self.create_subscription(
            String,
            "/nav2com",
            self.navigation_callback,
            10,
            callback_group=self.group,
        )

        # --- INTERNAL VARIABLES ---
        self.state = "IDLE"
        self.object_name = ""
        self.command_text = ""
        self.parsed_data = None

        # --- TIMER ---
        self.timer = self.create_timer(0.1, self.run_machine, callback_group=self.group)

        # --- EMERGENCY LISTENER THREAD ---
        threading.Thread(target=self.emergency_listener, daemon=True).start()

        self.get_logger().info("TiCare State Manager: Logic engine started (Spanish mode).")

    # ============================================================
    # EMERGENCY HANDLING
    # ============================================================

    def emergency_listener(self):
        """
        Escucha continuamente palabras de parada usando fuzzy logic.
        """
        while rclpy.ok() and self.state != "EMERGENCY_STOP":
            text = listen_for_wake_word(WAKE_WORD, duration=1)

            if text and classify_stop(text):
                self.send_emergency()
                break

    def send_emergency(self):
        self.state = "EMERGENCY_STOP"
        msg = String(data="emergency_stop")
        self.vis_pub.publish(msg)
        self.nav_pub.publish(msg)
        speak_audio("Parada de emergencia activada.")
        self.get_logger().error("emergency_stop sent to Vision and Navigation.")

    def check_stop(self, text: str) -> bool:
        if classify_stop(text):
            self.send_emergency()
            return True
        return False

    # ============================================================
    # MAIN STATE MACHINE
    # ============================================================

    def run_machine(self):

        if self.state == "EMERGENCY_STOP":
            return

        # --- STATE 1: IDLE ---
        if self.state == "IDLE":
            result = listen_for_wake_word(WAKE_WORD, duration=2)

            if result is not None:
                if self.check_stop(result):
                    return
                self.state = "WAKE_WORD_DETECTED"

        # --- STATE 2: WAKE WORD DETECTED ---
        elif self.state == "WAKE_WORD_DETECTED":
            self.vis_pub.publish(String(data="head_up"))
            self.state = "GREETING"

        # --- STATE 3: GREETING ---
        elif self.state == "GREETING":
            speak_audio("¿Te puedo ayudar en algo?")
            self.state = "LISTENING"

        # --- STATE 4: LISTENING ---
        elif self.state == "LISTENING":
            audio = record_audio(duration=5)
            text = transcribe_audio(audio)

            if self.check_stop(text):
                return

            if text == "Errr" or not text:
                self.state = "RETRY_SPEECH"
            else:
                self.command_text = text
                self.state = "PROCESSING_REQUEST"

        # --- STATE 5: PROCESSING REQUEST ---
        elif self.state == "PROCESSING_REQUEST":
            self.parsed_data = parse_command(self.command_text)

            if self.parsed_data["object"]:
                self.object_name = self.parsed_data["object"]
                self.state = "OBJECT_FOUND"
            else:
                self.state = "ERROR_NOT_FOUND"

        # --- STATE 6: RETRY SPEECH ---
        elif self.state == "RETRY_SPEECH":
            speak_audio("No he entendido, ¿puedes repetirlo?")
            self.state = "LISTENING"

        # --- STATE 9: OBJECT FOUND ---
        elif self.state == "OBJECT_FOUND":
            article = get_article(self.object_name)
            speak_audio(f"Ok, iré a buscar {article} {self.object_name}.")
            self.state = "SEND_TO_VISION"

        # --- STATE 7: SEND TO VISION ---
        elif self.state == "SEND_TO_VISION":
            self.vis_pub.publish(String(data=f"object_{self.object_name}"))
            self.nav_pub.publish(String(data="start_nav"))
            self.state = "SEARCHING"

        # --- STATE 8: SEARCHING ---
        elif self.state == "SEARCHING":
            pass

        # --- STATE 10: ERROR NOT FOUND ---
        elif self.state == "ERROR_NOT_FOUND":
            speak_audio("No he encontrado el objeto.")
            self.state = "IDLE"

    # ============================================================
    # CALLBACKS
    # ============================================================

    def vision_callback(self, msg: String):
        if msg.data == "object_detected":
            self.nav_pub.publish(String(data="return"))

    def navigation_callback(self, msg: String):
        if msg.data == "object_point":
            self.state = "POINTING"
            speak_audio("Aquí está.")

        elif msg.data == "home":
            self.state = "GOING_HOME"
            speak_audio("Ya lo he encontrado, ¿me acompañas?")
            self.vis_pub.publish(String(data="head_down"))
            self.state = "IDLE"


def main(args=None):
    rclpy.init(args=args)
    node = TiagoStateMachine()
    executor = MultiThreadedExecutor()
    executor.add_node(node)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
