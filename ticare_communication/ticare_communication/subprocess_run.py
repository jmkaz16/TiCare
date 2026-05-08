import os
import subprocess
import signal
from ament_index_python.packages import get_package_share_directory
import speech_recognition as sr


def record_audio():
    # Ejecuta el nodo de ROS2 para grabar
    process = subprocess.Popen(["ros2", "run", "ticare_communication", "save_audio"])
    process.wait()  # Esperamos a que termine de grabar

    # Obtenemos la ruta completa del archivo
    package_share_path = get_package_share_directory("ticare_communication")
    ruta_archivo = os.path.join(package_share_path, "data", "audio1.wav")

    return ruta_archivo


def transcribe_audio(ruta_wav):
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


def main():
    # Flujo lógico
    ruta = record_audio()
    resultado = transcribe_audio(ruta)
    print(f"Resultado final: {resultado}")


if __name__ == "main":
    main()
