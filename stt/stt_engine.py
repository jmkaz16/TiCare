import speech_recognition as sr

def listen_to_google():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=0.5)
        audio = r.listen(source)
    try:
        # Usamos 'es-ES' o 'en-US' según prefieras
        return r.recognize_google(audio, language='es-ES')
    except:
        return None