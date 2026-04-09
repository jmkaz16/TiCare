import sounddevice as sd
from scipy.io.wavfile import write
import os
from datetime import datetime


def record_audio(duration=5, fs=44100):
    # Crear carpeta recordings si no existe
    recordings_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "recordings"))
    os.makedirs(recordings_dir, exist_ok=True)

    # Nombre único basado en fecha y hora
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(recordings_dir, f"audio_{timestamp}.wav")

    print("Grabando audio...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()

    write(filename, fs, audio)
    print(f"Audio guardado en: {filename}")

    return filename


def get_latest_recording():
    recordings_dir = "audio\\recordings"

    # Si no existe la carpeta o está vacía
    if not os.path.exists(recordings_dir):
        raise FileNotFoundError("La carpeta 'recordings' no existe.")

    files = [f for f in os.listdir(recordings_dir) if f.endswith(".wav")]

    if not files:
        raise FileNotFoundError("No hay archivos .wav en la carpeta 'recordings'.")

    # Ordenar por fecha de modificación
    files.sort(key=lambda f: os.path.getmtime(os.path.join(recordings_dir, f)))

    latest_file = os.path.join(recordings_dir, files[-1])
    print(f"Última grabación encontrada: {latest_file}")
    return latest_file


if __name__ == "__main__":
    record_audio()
