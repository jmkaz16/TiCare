"""
TiCare Communication Module - State Manager.

This module implements a 13‑state machine that coordinates wake‑word detection,
speech recognition, natural language parsing, and robot behavior through Vision
and Navigation subsystems.

The state machine listens for the wake word, processes user commands, performs
object parsing, communicates with perception and navigation, and handles
emergency stop conditions.
"""

import os
import subprocess

from ament_index_python.packages import get_package_share_directory

import threading
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

import whisper
from gtts import gTTS
import pygame
import io
import time
import unicodedata
import spacy
from rapidfuzz import process, fuzz

WAKE_WORD = "Robot"

_nlp = None
_cached_mic_index = None
_cached_sample_rate = None


# ==========================
# COMMAND MAPS (fuzzy matching)
# ==========================

COMMAND_MAP = {
    "buscar": "buscar",
    "busca": "buscar",
    "encuentra": "buscar",
    "localiza": "buscar",
}

OBJECTS_MAP = {
    "botella": {"say": "botella", "send": "bottle"},
    "taza": {"say": "taza", "send": "mug"},
    "pelota": {"say": "pelota", "send": "tennisball"},
    "manzana": {"say": "manzana", "send": "apple"},
    "gafas": {"say": "gafas", "send": "glasses"},
}

STOP_MAP = {
    "para": "stop",
    "detente": "stop",
    "stop": "stop",
    "quieto": "stop",
    "basta": "stop",
    "cancela": "stop",
}


def normalize(s: str) -> str:
    """
    Normalize a string by lowercasing, trimming whitespace, and removing accents.

    Args:
        s (str): Input string.

    Returns:
        str: Normalized string without diacritics.
    """
    s = s.lower().strip()
    s = unicodedata.normalize("NFD", s)
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn")


def get_nlp():
    """
    Load and cache the Spanish spaCy model.

    Returns:
        Language: spaCy language model instance.
    """
    global _nlp
    if _nlp is not None:
        return _nlp
    try:
        _nlp = spacy.load("es_core_news_sm")
    except Exception as e:
        print("spaCy unavailable, using blank model:", e)
        _nlp = spacy.blank("es")
    return _nlp


# ==========================
# Microphone / audio
# ==========================


def record_audio():
    """
    Record audio by launching the ROS2 save_audio node.

    Returns:
        str: Path to the recorded WAV file.
    """
    process = subprocess.Popen(["ros2", "run", "ticare_communication", "save_audio_TIAGo"])
    process.wait()

    package_share_path = get_package_share_directory("ticare_communication")
    ruta_archivo = os.path.join(package_share_path, "data", "audio.wav")

    return ruta_archivo

model = whisper.load_model("small", device="cpu")
def transcribe_audio(
    ruta_wav=os.path.join(get_package_share_directory("ticare_communication"), "data", "audio.wav")
):
    """
    Transcribe a WAV file using Whisper.
    """
    if ruta_wav is None or not os.path.exists(ruta_wav):
        return "Errr"

    try:
        result = model.transcribe(
            ruta_wav,
            language="es",
            fp16=False
        )

        text = result["text"].strip()
        print("Transcription:", text)

        if not text:
            return "Errr"

        return text

    except Exception as e:
        print(f"Recognition error: {e}")
        return "Errr"


def speak_audio(texto):
    """
    Convert text to speech using gTTS and play it with pygame.

    Args:
        texto (str): Text to be spoken aloud.
    """
    tts = gTTS(text=texto, lang="es")
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)

    pygame.mixer.init()
    pygame.mixer.music.load(fp)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        time.sleep(0.1)


# ==========================
# Wake word
# ==========================


def clean_wake_word(text, wake_word):
    """
    Remove the wake word from a detected phrase.

    Args:
        text (str): Input phrase.
        wake_word (str): Wake word to remove.

    Returns:
        str: Remaining text after removing the wake word.
    """
    text = text.lower().strip()
    if wake_word in text:
        cleaned = text.replace(wake_word, "").strip(" ,.")
        return cleaned or ""
    return ""


def is_wake_word(text, wake_word):
    """
    Determine whether a phrase contains or resembles the wake word.

    Args:
        text (str): Input phrase.
        wake_word (str): Wake word to detect.

    Returns:
        bool: True if wake word is detected or fuzzy‑matched.
    """
    text = text.lower().strip()
    if wake_word in text:
        print("Wake‑word found inside phrase.")
        return True

    score = fuzz.ratio(text, wake_word)
    print(f"Wake‑word similarity: {score}")
    return score > 70


def listen_for_wake_word(wake_word, duration=3):
    """
    Continuously record audio until the wake word is detected.

    Args:
        wake_word (str): Wake word to detect.
        duration (int): Recording duration per attempt.

    Returns:
        str: Remaining text after wake word, or empty string.
    """
    while True:
        print("Recording fragment...")
        ruta = record_audio()
        text = transcribe_audio(ruta)

        if not text or text == "Errr":
            print("Nothing understood.")
            continue

        text = text.lower().strip()
        print(f"Detected: {text}")

        if is_wake_word(text, wake_word):
            remaining = clean_wake_word(text, wake_word)
            if remaining:
                print("Wake‑word + command detected.")
                print(f"Command: {remaining}")
                return remaining
            print("Wake‑word detected.")
            return ""


# ==========================
# Fuzzy mappings
# ==========================


def map_action(text: str):
    """
    Fuzzy‑match an action verb.

    Args:
        text (str): Input text.

    Returns:
        str | None: Canonical action or None.
    """
    choices = list(COMMAND_MAP.keys())
    match = process.extractOne(text, choices, scorer=fuzz.ratio)
    if match and match[1] >= 75:
        return COMMAND_MAP[match[0]]
    return None



def map_object(text: str):
    """
    Fuzzy‑match an object.

    Args:
        text (str): Input text.

    Returns:
        dict | None: Object metadata or None.
    """
    choices = list(OBJECTS_MAP.keys())
    match = process.extractOne(text, choices, scorer=fuzz.ratio)
    if match and match[1] >= 75:
        return OBJECTS_MAP[match[0]]
    return None

def classify_stop(text: str):
    """
    Determine whether a phrase indicates a stop command.

    Args:
        text (str): Input phrase.

    Returns:
        bool: True if stop command detected.
    """
    text_norm = normalize(text)
    match = process.extractOne(text_norm, STOP_MAP.keys(), scorer=fuzz.ratio)
    if match and match[1] >= 75:
        return True
    return False


# ==========================
# NLP parsing
# ==========================


def get_article(word: str):
    """
    Determine the correct Spanish article for a noun.

    Args:
        word (str): Noun to analyze.

    Returns:
        str: Appropriate article ("el", "la", "los", "las").
    """
    nlp = get_nlp()
    doc = nlp(word)
    if not doc:
        return "el"

    token = doc[0]

    gender = token.morph.get("Gender")
    number = token.morph.get("Number")

    if "Fem" in gender:
        return "las" if "Plur" in number else "la"
    elif "Masc" in gender:
        return "los" if "Plur" in number else "el"
    else:
        return "el"


def parse_command(text: str):
    """
    Parse a natural language command into action, object, and place.

    Args:
        text (str): Input command.

    Returns:
        dict: Parsed components including action, object, place, and topic.
    """
    text_norm = normalize(text)
    nlp = get_nlp()
    doc = nlp(text_norm)

    action = map_action(text_norm)
    if not action:
        for token in doc:
            candidate = map_action(token.lemma_)
            if candidate:
                action = candidate
                break

    obj = map_object(text_norm)
    if not obj:
        for token in doc:
            candidate = map_object(token.lemma_)
            if candidate:
                obj = candidate
                break

    return {
        "action": action,
        "object": obj,
        "topic": text_norm,
    }


class TiagoStateMachine(Node):
    """
    Main state machine for the TiCare communication module.

    This class manages wake‑word detection, speech recognition, command parsing,
    and communication with Vision and Navigation subsystems.
    """

    def __init__(self):
        """
        Initialize publishers, subscribers, timers, and internal state.
        """
        super().__init__("state_machine_node")

        self.group = MutuallyExclusiveCallbackGroup()

        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=5,
        )

        self.vis_pub = self.create_publisher(String, "/com2vis", qos_profile)
        self.nav_pub = self.create_publisher(String, "/com2nav", qos_profile)

        self.vis_sub = self.create_subscription(
            String,
            "/vis2com",
            self.vision_callback,
            qos_profile,
            callback_group=self.group,
        )

        self.nav_sub = self.create_subscription(
            String,
            "/nav2com",
            self.navigation_callback,
            qos_profile,
            callback_group=self.group,
        )

        self.state = "IDLE"
        self.object_name = ""
        self.object_send = ""
        self.object_data = ""
        self.command_text = ""
        self.parsed_data = None
        self.object_detected = False

        self.timer = self.create_timer(0.1, self.run_machine, callback_group=self.group)

        threading.Thread(target=self.emergency_listener, daemon=True).start()

        self.get_logger().info("TiCare State Manager: Logic engine started (Spanish mode).")

    # ============================================================
    # EMERGENCY HANDLING
    # ============================================================

    def emergency_listener(self):
        """
        Continuously listen for emergency stop commands using fuzzy logic.
        """
        while rclpy.ok() and self.state != "EMERGENCY_STOP":
            text = listen_for_wake_word(WAKE_WORD, duration=1)

            if text and classify_stop(text):
                self.send_emergency()
                break

    def send_emergency(self):
        """
        Trigger an emergency stop and notify Vision and Navigation.
        """
        self.state = "EMERGENCY_STOP"
        msg = String(data="emergency_stop")
        self.vis_pub.publish(msg)
        self.nav_pub.publish(msg)
        speak_audio("Parada de emergencia activada.")
        self.get_logger().error("emergency_stop sent to Vision and Navigation.")

    def check_stop(self, text: str) -> bool:
        """
        Check whether a phrase contains a stop command.

        Args:
            text (str): Input phrase.

        Returns:
            bool: True if emergency stop triggered.
        """
        if classify_stop(text):
            self.send_emergency()
            return True
        return False

    # ============================================================
    # MAIN STATE MACHINE
    # ============================================================

    def run_machine(self):
        """
        Execute one iteration of the state machine.
        """
        if self.state == "EMERGENCY_STOP":
            return

        if self.state == "IDLE":
            result = listen_for_wake_word(WAKE_WORD, duration=2)

            if result is not None:
                if self.check_stop(result):
                    return
                self.state = "WAKE_WORD_DETECTED"

        elif self.state == "WAKE_WORD_DETECTED":
            self.vis_pub.publish(String(data="head_up"))
            self.state = "GREETING"

        elif self.state == "GREETING":
            speak_audio("¿Te puedo ayudar en algo?")
            self.state = "LISTENING"

        elif self.state == "LISTENING":
            ruta = record_audio()
            text = transcribe_audio(ruta)

            if self.check_stop(text):
                return

            if text == "Errr" or not text:
                self.state = "RETRY_SPEECH"
            else:
                self.command_text = text
                self.state = "PROCESSING_REQUEST"

        elif self.state == "PROCESSING_REQUEST":
            self.parsed_data = parse_command(self.command_text)

            if self.parsed_data["object"]:
                self.object_data = self.parsed_data["object"]
                self.object_name = self.object_data["say"]
                self.object_send = self.object_data["send"]
                self.state = "OBJECT_FOUND"
            else:
                self.state = "OBJECT_NOT_LISTED"

        elif self.state == "RETRY_SPEECH":
            speak_audio("No he entendido, ¿puedes repetirlo?")
            self.state = "LISTENING"

        elif self.state == "OBJECT_FOUND":
            article = get_article(self.object_name)
            if self.object_name=="botella":
                article="la"
            speak_audio(f"Ok, iré a buscar {article} {self.object_name}.")
            self.state = "SEND_TO_VISION"

        elif self.state == "SEND_TO_VISION":
            self.vis_pub.publish(String(data=f"object_{self.object_send}"))
            self.nav_pub.publish(String(data="start_nav"))
            self.state = "SEARCHING"

        elif self.state == "SEARCHING":
            pass

        elif self.state == "RETURN_TO_OBJECT":
            pass

        elif self.state == "OBJECT_NOT_LISTED":
            speak_audio("El objeto a buscar no está en la lista.")
            self.state = "IDLE"

        else:
            self.state = "IDLE"

    # ============================================================
    # CALLBACKS
    # ============================================================

    def vision_callback(self, msg: String):
        """
        Handle messages from the Vision subsystem.

        Args:
            msg (String): Incoming message.
        """
        if self.state == "SEARCHING" and msg.data == "object_detected":
            self.object_detected = True
            self.state = "RETURN_TO_USER"

    def navigation_callback(self, msg: String):
        """
        Handle messages from the Navigation subsystem.

        Args:
            msg (String): Incoming message.
        """
        if self.state == "SEARCHING" and msg.data == "home":
            if self.object_detected:
                speak_audio("Ya lo he encontrado, ¿me acompañas?")
                self.nav_pub.publish(String(data="return"))
                self.state = "RETURN_TO_OBJECT"

            else:
                speak_audio("No he encontrado el objeto.")
                self.vis_pub.publish(String(data="head_down"))
                return

        elif self.state == "RETURN_TO_OBJECT" and msg.data == "object_point":
            speak_audio("Aquí está tu objeto.")
            self.vis_pub.publish(String(data="head_down"))
            return


def main(args=None):
    """
    Entry point for the TiagoStateMachine node.

    Args:
        args (list | None): Optional command‑line arguments.
    """
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
