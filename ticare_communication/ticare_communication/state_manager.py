"""
TiCare Communication Module - State Manager.

This node implements a 13-state machine to coordinate voice recognition,
natural language processing, and robot behavior via Vision and Navigation.
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

import speech_recognition as sr
from gtts import gTTS
import pygame
import io
import time
import unicodedata
import spacy
from rapidfuzz import process, fuzz

WAKE_WORD = "tiago"

_nlp = None
_cached_mic_index = None
_cached_sample_rate = None


# ==========================
# COMMAND MAPS (fuzzy matching)
# ==========================

# Acciones
COMMAND_MAP = {
    "buscar": "buscar",
    "busca": "buscar",
    "encuentra": "buscar",
    "localiza": "buscar",
    # añade aquí más verbos si quieres
}

# Lugares
PLACES_MAP = {
    "cocina": "la cocina",
    "salon": "el salón",
    "salón": "el salón",
    "habitacion": "la habitación",
    "habitación": "la habitación",
    "baño": "el baño",
    # etc.
}

# Objetos (para fuzzy de objetos)
OBJECTS_MAP = {
    "botella": "bottle",
    "manzana": "apple",
    "taza": "mug",
    "pelota": "tennisball",
    "gafas": "glasses",
}

# Respuestas afirmativas / negativas para confirmación
YES_MAP = {
    "sí": "yes",
    "si": "yes",
    "claro": "yes",
    "vale": "yes",
    "correcto": "yes",
    "afirmativo": "yes",
}

NO_MAP = {
    "no": "no",
    "negativo": "no",
    "para": "no",
    "me he equivocado": "no",
    "cancela": "no",
}

# Palabras de parada (stop) por voz
STOP_MAP = {
    "para": "stop",
    "detente": "stop",
    "stop": "stop",
    "quieto": "stop",
    "basta": "stop",
    "cancela": "stop",
}

# ==========================
# Utilidades generales
# ==========================


def normalize(s: str) -> str:
    s = s.lower().strip()
    s = unicodedata.normalize("NFD", s)
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn")


def get_nlp():
    global _nlp
    if _nlp is not None:
        return _nlp
    try:
        _nlp = spacy.load("es_core_news_sm")
    except Exception as e:
        print("spaCy no disponible, usando modelo en blanco:", e)
        _nlp = spacy.blank("es")
    return _nlp


# ==========================
# Micrófono / audio
# ==========================


def record_audio():
    # Ejecuta el nodo de ROS2 para grabar
    process = subprocess.Popen(["ros2", "run", "ticare_communication", "save_audio"])
    process.wait()  # Esperamos a que termine de grabar

    # Obtenemos la ruta completa del archivo
    package_share_path = get_package_share_directory("ticare_communication")
    ruta_archivo = os.path.join(package_share_path, "data", "audio.wav")

    return ruta_archivo


# ==========================
# STT / TTS
# ==========================


def transcribe_audio(
    ruta_wav=os.path.join(get_package_share_directory("ticare_communication"), "data", "audio.wav")
):
    if ruta_wav is None or not os.path.exists(ruta_wav):
        return "Errr"

    r = sr.Recognizer()

    try:
        # Cargamos el archivo WAV directamente con speech_recognition
        with sr.AudioFile(ruta_wav) as source:
            audio_data = r.record(source)  # Esto lee el archivo y lo convierte al formato correcto

        text = r.recognize_google(audio_data, language="es-ES")
        print("Transcripción:", text)
        return text

    except sr.UnknownValueError:
        print("No se entendió el audio")
        return "Errr"
    except Exception as e:
        print(f"Error en reconocimiento: {e}")
        return "Errr"


def speak_audio(texto):
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
# Wake word (parametrizada)
# ==========================


def clean_wake_word(text, wake_word):
    text = text.lower().strip()
    if wake_word in text:
        cleaned = text.replace(wake_word, "").strip(" ,.")
        return cleaned or ""
    return ""


def is_wake_word(text, wake_word):
    text = text.lower().strip()
    if wake_word in text:
        print("Wake-word encontrada dentro de la frase.")
        return True

    score = fuzz.ratio(text, wake_word)
    print(f"Similitud con wake-word: {score}")
    return score > 70


def listen_for_wake_word(wake_word, duration=3):
    while True:
        print("Grabando fragmento ... ")
        ruta = record_audio()
        text = transcribe_audio(ruta)

        if not text or text == "Errr":
            print("No se entendió nada.")
            continue

        text = text.lower().strip()
        print(f"Detectado: {text}")

        if is_wake_word(text, wake_word):
            remaining = clean_wake_word(text, wake_word)
            if remaining:
                print("Wake-word + orden detectada en la misma frase.")
                print(f"Orden detectada: {remaining}")
                return remaining
            print("¡Palabra clave detectada!")
            return ""


# ==========================
# Fuzzy mapeos
# ==========================


def map_action(text: str):
    choices = list(COMMAND_MAP.keys())
    match = process.extractOne(text, choices, scorer=fuzz.ratio)
    if match and match[1] >= 75:
        return COMMAND_MAP[match[0]]
    return None


def map_place(word: str):
    choices = list(PLACES_MAP.keys())
    match = process.extractOne(word, choices, scorer=fuzz.ratio)
    if match and match[1] >= 75:
        return PLACES_MAP[match[0]]
    return None


def map_object(text: str):
    choices = list(OBJECTS_MAP.keys())
    match = process.extractOne(text, choices, scorer=fuzz.ratio)
    if match and match[1] >= 75:
        return OBJECTS_MAP[match[0]]
    return None


def classify_answer(text: str):
    text_norm = normalize(text)

    yes_match = process.extractOne(text_norm, YES_MAP.keys(), scorer=fuzz.ratio)
    if yes_match and yes_match[1] >= 75:
        return "yes"

    no_match = process.extractOne(text_norm, NO_MAP.keys(), scorer=fuzz.ratio)
    if no_match and no_match[1] >= 75:
        return "no"

    return "unknown"


def classify_stop(text: str):
    text_norm = normalize(text)
    match = process.extractOne(text_norm, STOP_MAP.keys(), scorer=fuzz.ratio)
    if match and match[1] >= 75:
        return True
    return False


# ==========================
# NLP: género y parsing
# ==========================


def get_article(word: str):
    """
    Devuelve el artículo correcto (el, la, los, las) según género y número.
    """
    nlp = get_nlp()
    doc = nlp(word)
    if not doc:
        return "el"  # fallback

    token = doc[0]

    gender = token.morph.get("Gender")
    number = token.morph.get("Number")

    if "Fem" in gender:
        return "las" if "Plur" in number else "la"
    elif "Masc" in gender:
        return "los" if "Plur" in number else "el"
    else:
        return "el"  # fallback neutro


def parse_command(text: str):
    text_norm = normalize(text)
    nlp = get_nlp()
    doc = nlp(text_norm)

    # Acción: primero por frase completa, luego por tokens
    action = map_action(text_norm)
    if not action:
        for token in doc:
            candidate = map_action(token.lemma_)
            if candidate:
                action = candidate
                break

    # Objeto: fuzzy por frase completa, luego por tokens
    obj = map_object(text_norm)
    if not obj:
        for token in doc:
            candidate = map_object(token.lemma_)
            if candidate:
                obj = candidate
                break

    # Lugar: por tokens
    place = None
    for token in doc:
        candidate = map_place(token.lemma_)
        if candidate:
            place = candidate
            break

    return {
        "action": action,
        "object": obj,
        "place": place,
        "topic": text_norm,
    }


class TiagoStateMachine(Node):

    def __init__(self):
        super().__init__("state_machine_node")

        self.group = MutuallyExclusiveCallbackGroup()

        # --- PUBLISHERS ---
        self.vis_pub = self.create_publisher(String, "/com2vis", 5)
        self.nav_pub = self.create_publisher(String, "/com2nav", 5)

        # Create a profile of QoS with Best Effort a Depth of 5
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT, history=HistoryPolicy.KEEP_LAST, depth=5
        )

        # --- SUBSCRIBERS ---
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

        # --- INTERNAL VARIABLES ---
        self.state = "IDLE"
        self.object_name = ""
        self.command_text = ""
        self.parsed_data = None
        self.object_detected: float = False

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
            ruta = record_audio()
            text = transcribe_audio(ruta)

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
                self.state = "OBJECT_NOT_LISTED"

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

        elif self.state == "RETURN_TO_OBJECT":
            pass

        # --- STATE 11: OBJECT NOT LISTED ---
        elif self.state == "OBJECT_NOT_LISTED":
            speak_audio("El objeto a buscar no está en la lista.")
            self.state = "IDLE"

    # ============================================================
    # CALLBACKS
    # ============================================================

    def vision_callback(self, msg: String):
        if self.state == "SEARCHING" and msg.data == "object_detected":
            self.object_detected = True

    def navigation_callback(self, msg: String):
        if msg.data == "home":
            if self.object_detected:
                speak_audio("Ya lo he encontrado, ¿me acompañas?")
                self.vis_pub.publish(String(data="head_down"))
                self.state = "RETURN_TO_OBJECT"

            if not self.object_detected:
                self.vis_pub.publish(String(data="head_down"))
                speak_audio("No he encontrado el objeto.")
                return

        elif self.state == "RETURN_TO_OBJECT" and msg.data == "object_point":
            speak_audio("Aquí está.")
            return


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
