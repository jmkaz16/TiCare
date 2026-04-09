from google import genai
from gtts import gTTS
import pygame
import os
import time

# 1. Configuración con el nuevo SDK
client = genai.Client(api_key="API.txt")
MODEL_ID = "gemini-2.0-flash" # El modelo más rápido de 2026

def chat_and_speak(text):
    try:
        # 2. Generar respuesta (Sintaxis nueva)
        prompt = f"Responde en una sola frase corta como un perro robótico simpático: {text}"
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt
        )
        answer = response.text
        print(f"🤖 Bittle dice: {answer}")

        # 3. Voz (gTTS sigue igual, funciona perfecto)
        tts = gTTS(text=answer, lang='es')
        filename = "response.mp3"
        tts.save(filename)

        # 4. Reproducir
        pygame.mixer.init()
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        
        pygame.mixer.quit()
        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        print(f"❌ Error en el cerebro de Tiago: {e}")