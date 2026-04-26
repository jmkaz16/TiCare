# State_machine.py

import keyboard
import time
import numpy as np

from stt.whisper_stt import transcribe_audio
from stt.record_audio import record_audio
from stt.wake_word import listen_for_wake_word
from stt.tiago_spacy import parse_command
from input.command_map import COMMAND_MAP, PLACES_MAP


WAKE_WORD = "tiago"
INTERRUPT_WORDS = ["para", "detente", "stop", "quieto", "basta"]

# ---------------------------
# DURACIONES CONFIGURABLES
# ---------------------------

WAKE_LISTEN_DURATION = 2      # Duración de cada fragmento mientras escucha la wake-word
COMMAND_RECORD_DURATION = 7   # Duración de la grabación del comando completo
CONFIRM_DURATION = 2          # Duración de la confirmación por voz


# ---------------------------
# Máquina de estados
# ---------------------------

def main():

    state = 0
    command_text = ""
    parsed = None

    while True:

        # Salida manual
        if keyboard.is_pressed("c"):
            print("Saliendo del sistema.")
            break

        # ---------------------------
        # ESTADO 0
        # ---------------------------
        if state == 0:
            print("Sistema listo. Pulsa 'f' para activar. Pulsa 'c' para salir.")
            while not keyboard.is_pressed("f"):
                time.sleep(0.1)
            state = 1

        # ---------------------------
        # ESTADO 1 — Escucha continua de wake-word
        # ---------------------------
        elif state == 1:
            print("Escuchando wake-word...")

            result = listen_for_wake_word(duration=WAKE_LISTEN_DURATION)

            if result is None:
                state = 0
                continue 

            command_text = result
            state = 2


        # ---------------------------
        # ESTADO 2 — ¿Wake-word + comando?
        # ---------------------------
        elif state == 2:
            if command_text != "":
                state = 3
            else:
                state = 4

        # ---------------------------
        # ESTADO 3 — Procesar comando 
        # ---------------------------
        elif state == 3:
            print("Transcribiendo mensaje...")
            parsed = parse_command(command_text)
            state = 8

        # ---------------------------
        # ESTADO 4 — Grabar mensaje completo
        # ---------------------------
        elif state == 4:
            print("Grabando mensaje...")
            fs, audio = record_audio(duration=COMMAND_RECORD_DURATION)
            command_text = transcribe_audio(audio)
            state = 5

        # ---------------------------
        # ESTADO 5 — ¿Se escuchó algo?
        # ---------------------------
        elif state == 5:
            if command_text.strip() == "":
                state = 7
            else:
                state = 3

        # ---------------------------
        # ESTADO 7 — No se detectó nada
        # ---------------------------
        elif state == 7:
            print("No he entendido bien, repite por favor.")
            state = 4

        # ---------------------------
        # ESTADO 8 — Validación interna
        # ---------------------------
        elif state == 8:
            if parsed["action"] is not None and parsed["object"] is not None:
                state = 9
            else:
                print("No he entendido bien, repite por favor.")
                state = 4

        # ---------------------------
        # ESTADO 9 — Confirmación por voz
        # ---------------------------
        elif state == 9:
            print("¿Es correcto? (di 'sí' o 'no')")

            fs, audio = record_audio(duration=CONFIRM_DURATION)
            answer = transcribe_audio(audio).lower()

            if "sí" in answer or "si" in answer:
                state = 10
            elif "no" in answer:
                print("De acuerdo, dime otra vez qué querías decir.")
                state = 4

        # ---------------------------
        # ESTADO 10 — Confirmación final
        # ---------------------------
        elif state == 10:
            action = parsed["action"]
            obj = parsed["object"]
            place = parsed["place"]

            if place:
                print(f"Perfecto, buscaré {obj} en {place}.")
            else:
                print(f"Perfecto, ejecutaré la acción {action} con {obj}.")

            state = 0

        else:
            state = 0


if __name__ == "__main__":
    main()