from pynput import keyboard
import time

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
from ticare_communication.scripts.command_map import COMMAND_MAP, PLACES_MAP

WAKE_WORD = "tiago"

WAKE_LISTEN_DURATION = 2
COMMAND_RECORD_DURATION = 5
CONFIRM_DURATION = 2

key_f_pressed = False
key_c_pressed = False


def on_press(key):
    global key_f_pressed, key_c_pressed
    try:
        if key.char == "f":
            key_f_pressed = True
        elif key.char == "c":
            key_c_pressed = True
    except:
        pass


listener = keyboard.Listener(on_press=on_press)
listener.start()


def main():
    global key_f_pressed, key_c_pressed

    state = 0
    command_text = ""
    parsed = None

    while True:

        if key_c_pressed:
            print("Saliendo del sistema.")
            break

        # ESTADO 0
        if state == 0:
            print("Sistema listo. Pulsa 'f' para activar. Pulsa 'c' para salir.")
            key_f_pressed = False
            while not key_f_pressed:
                time.sleep(0.1)
            state = 1

        # ESTADO 1 — Escucha wake-word
        elif state == 1:
            print("Escuchando wake-word...")

            result = listen_for_wake_word(WAKE_WORD, duration=WAKE_LISTEN_DURATION)

            if result is None:
                state = 0
                continue

            command_text = result
            state = 2

        # ESTADO 2 — ¿Wake-word + comando?
        elif state == 2:
            if command_text != "":
                state = 3
            else:
                state = 4

        # ESTADO 3 — Procesar comando
        elif state == 3:
            print("Transcribiendo mensaje...")
            # Aquí podrías permitir parada por voz si quieres:
            if classify_stop(command_text):
                speak_audio("De acuerdo, detengo la acción.")
                state = 0
                continue

            parsed = parse_command(command_text)
            state = 8

        # ESTADO 4 — Grabar mensaje completo
        elif state == 4:
            print("Grabando mensaje...")
            audio = record_audio(duration=COMMAND_RECORD_DURATION)
            command_text = transcribe_audio(audio)
            state = 5

        # ESTADO 5 — ¿Se escuchó algo?
        elif state == 5:
            if command_text.strip() == "" or command_text == "Errr":
                state = 7
            else:
                state = 3

        # ESTADO 7 — No se detectó nada
        elif state == 7:
            speak_audio("No he entendido bien, repite por favor.")
            state = 4

        # ESTADO 8 — Validación interna
        elif state == 8:
            if parsed["action"] is not None and parsed["object"] is not None:
                state = 9
            else:
                speak_audio("No he entendido bien, repite por favor.")
                state = 4

        # ESTADO 9 — Confirmación por voz (fuzzy)
        elif state == 9:
            action = parsed["action"]
            obj = parsed["object"]
            place = parsed["place"]

            speak_audio(f"¿Quieres que busque la {obj}?")

            audio = record_audio(duration=CONFIRM_DURATION)
            answer = transcribe_audio(audio).lower()
            print("Respuesta de confirmación:", answer)

            # Permitir parada también aquí si quieres
            if classify_stop(answer):
                speak_audio("De acuerdo, detengo la acción.")
                state = 0
                continue

            label = classify_answer(answer)

            if label == "yes":
                state = 10
            elif label == "no":
                speak_audio("De acuerdo, dime otra vez qué querías decir.")
                state = 4
            else:
                speak_audio("No he entendido tu respuesta, repite por favor.")

        # ESTADO 10 — Confirmación final
        elif state == 10:
            obj = parsed["object"]
            place = parsed["place"]

            art = get_article(obj) + " "

            if place:
                text = f"Perfecto, buscaré {art}{obj} en {place}."
            else:
                text = f"Perfecto, buscaré {art}{obj}."

            speak_audio(text)
            break

        else:
            state = 0


if __name__ == "__main__":
    main()
