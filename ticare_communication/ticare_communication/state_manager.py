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
    "botella": "botella",
    "llaves": "llaves",
    "cartera": "cartera",
    "mando": "mando",
    "gafas": "gafas",
    # añade los que quieras
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


def get_microphone_index():
    global _cached_mic_index
    if _cached_mic_index is not None:
        return _cached_mic_index

    try:
        devices = sr.Microphone.list_microphone_names()
        print("\n=== Dispositivos detectados ===")
        for i, name in enumerate(devices):
            print(f"{i}: {name}")

        for i, name in enumerate(devices):
            if "monitor" not in name.lower():
                print(f"\nUsando micrófono: {name} (index {i})")
                _cached_mic_index = i
                return _cached_mic_index

        print("\nNo se encontró un micrófono claro, usando index 0")
        _cached_mic_index = 0
        return _cached_mic_index

    except Exception as e:
        print("Error detectando micrófono:", e)
        _cached_mic_index = None
        return None


def record_audio(duration=3):
    global _cached_sample_rate

    r = sr.Recognizer()
    r.energy_threshold = 300
    r.dynamic_energy_threshold = True

    mic_index = get_microphone_index()
    if mic_index is None:
        print("No hay micrófono disponible.")
        return None

    # Si ya tenemos un sample_rate válido, úsalo directamente
    if _cached_sample_rate is not None:
        try:
            with sr.Microphone(device_index=mic_index, sample_rate=_cached_sample_rate) as source:
                print(f"Usando micrófono index {mic_index} con sample_rate={_cached_sample_rate}")
                r.adjust_for_ambient_noise(source, duration=0.5)
                print(f"Grabando {duration} segundos...")
                audio = r.record(source, duration=duration)
                return audio
        except Exception as e:
            print(f"Falló sample_rate cacheado ({_cached_sample_rate}): {e}")
            _cached_sample_rate = None  # forzar re-detección

    # Detectar sample_rate válido
    sample_rates = [44100, 48000, 32000, 22050, 16000]
    for rate in sample_rates:
        try:
            print(f"Intentando abrir micrófono {mic_index} con sample_rate={rate}...")
            with sr.Microphone(device_index=mic_index, sample_rate=rate) as source:
                r.adjust_for_ambient_noise(source, duration=0.5)
                print(f"Grabando {duration} segundos con sample_rate={rate}...")
                audio = r.record(source, duration=duration)
                _cached_sample_rate = rate
                return audio
        except Exception as e:
            print(f"Falló sample_rate={rate}: {e}")
            continue

    print("ERROR: No se pudo abrir el micrófono con ningún sample_rate.")
    return None


# ==========================
# STT / TTS
# ==========================


def transcribe_audio(audio_data):
    if audio_data is None:
        return "Errr"
    r = sr.Recognizer()
    try:
        text = r.recognize_google(audio_data, language="es-ES")
        print("Transcripción:", text)
        return text
    except sr.UnknownValueError:
        return "Errr"
    except Exception as e:
        print("Error en reconocimiento:", e)
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
        audio = record_audio(duration=duration)
        if audio is None:
            print("No se pudo grabar audio, reintentando...")
            continue

        text = transcribe_audio(audio)
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
