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

from .stt.google_stt import transcribe_audio, speak_audio
from .stt.record_audio import record_audio
from .stt.wake_word import listen_for_wake_word, INTERRUPT_WORDS
from .stt.tiago_spacy import parse_command, detect_gender


class TiagoStateMachine(Node):
    """
    Main State Machine for the TiCare Communication package.

    Orchestrates the robot's lifecycle by publishing commands to /com2vis and /com2nav
    based on voice input and module feedback.

    Attributes:
        vis_pub (Publisher): Publisher for Vision commands.
        nav_pub (Publisher): Publisher for Navigation commands.
        state (str): Current state of the state machine.
        object_name (str): Name of the object extracted from NLP.
        command_text (str): Raw transcribed user command.
        parsed_data (dict): Parsed NLP structure.
    """

    def __init__(self):
        """Initialize publishers, subscribers, timers, and emergency thread."""
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

        self.get_logger().info("TiCare State Manager: Logic engine started (English mode).")

    # -------------------------------------------------------------------------
    # EMERGENCY HANDLING
    # -------------------------------------------------------------------------

    def emergency_listener(self):
        """
        Continuously listens for emergency stop keywords in a parallel thread.

        This thread runs independently from the main ROS executor to ensure
        that emergency commands are detected even during audio recording,
        navigation, or other blocking operations.
        """
        while rclpy.ok() and self.state != "EMERGENCY_STOP":
            text = listen_for_wake_word(duration=1)

            if text and any(word in text.lower() for word in INTERRUPT_WORDS):
                self.send_emergency()
                break

    def send_emergency(self):
        """
        Trigger the EMERGENCY_STOP state and notify all modules.

        Sends the emergency_stop command to both Vision and Navigation modules.
        """
        self.state = "EMERGENCY_STOP"
        msg = String(data="emergency_stop")

        self.vis_pub.publish(msg)
        self.nav_pub.publish(msg)

        speak_audio("Parada de emergencia activada.")
        self.get_logger().error("emergency_stop sent to Vision and Navigation.")

    def check_stop(self, text: str) -> bool:
        """
        Check if the given text contains any emergency keywords.

        Args:
            text (str): Transcribed audio text.

        Returns:
            bool: True if an emergency keyword is detected.
        """
        if any(word in text.lower() for word in INTERRUPT_WORDS):
            self.send_emergency()
            return True
        return False

    # -------------------------------------------------------------------------
    # MAIN STATE MACHINE
    # -------------------------------------------------------------------------

    def run_machine(self):
        """Execute the state machine logic transitions."""
        if self.state == "EMERGENCY_STOP":
            return

        # --- STATE 1: IDLE ---
        if self.state == "IDLE":
            result = listen_for_wake_word(duration=2)
            if result is not None:
                if self.check_stop(result):
                    return
                self.state = "WAKE_WORD_DETECTED"

        # --- STATE 2: WAKE_WORD_DETECTED ---
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

        # --- STATE 5: PROCESSING_REQUEST ---
        elif self.state == "PROCESSING_REQUEST":
            self.parsed_data = parse_command(self.command_text)

            if self.parsed_data["object"]:
                self.object_name = self.parsed_data["object"]
                self.state = "OBJECT_FOUND"
            else:
                self.state = "ERROR_NOT_FOUND"

        # --- STATE 6: RETRY_SPEECH ---
        elif self.state == "RETRY_SPEECH":
            speak_audio("No he entendido, ¿puedes repetirlo?")
            self.state = "LISTENING"

        # --- STATE 9: OBJECT_FOUND ---
        elif self.state == "OBJECT_FOUND":
            gender = detect_gender(self.object_name)
            article = "el" if gender == "masculino" else "la"
            speak_audio(f"Ok, iré a buscar {article} {self.object_name}")
            self.state = "SEND_TO_VISION"

        # --- STATE 7: SEND_TO_VISION ---
        elif self.state == "SEND_TO_VISION":
            self.vis_pub.publish(String(data=f"object_{self.object_name}"))
            self.nav_pub.publish(String(data="start_nav"))
            self.state = "SEARCHING"

        # --- STATE 8: SEARCHING ---
        elif self.state == "SEARCHING":
            pass

        # --- STATE 10: ERROR_NOT_FOUND ---
        elif self.state == "ERROR_NOT_FOUND":
            speak_audio("No he encontrado el objeto")
            self.state = "IDLE"

    # -------------------------------------------------------------------------
    # CALLBACKS
    # -------------------------------------------------------------------------

    def vision_callback(self, msg: String):
        """
        Process incoming feedback from /vis2com.

        Args:
            msg (String): Vision module message.
        """
        if msg.data == "object_detected":
            self.nav_pub.publish(String(data="return"))

    def navigation_callback(self, msg: String):
        """
        Process incoming feedback from /nav2com.

        Args:
            msg (String): Navigation module message.
        """
        if msg.data == "object_point":
            self.state = "POINTING"
            speak_audio("Aquí está.")

        elif msg.data == "home":
            self.state = "GOING_HOME"
            speak_audio("Ya lo he encontrado, ¿me acompañas?")
            self.vis_pub.publish(String(data="head_down"))
            self.state = "IDLE"


def main(args=None):
    """Entry point for the state manager node."""
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
