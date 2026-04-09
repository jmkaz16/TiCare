import google.generativeai as genai
from gtts import gTTS
import pygame
import os
import time

# Configuración de Gemini
genai.configure(api_key="AIzaSyBcd0iXeIMcbjbjNMvbref0NYlzRfO6I2A")
model = genai.GenerativeModel('gemini-1.5-flash')

def chat_and_speak(text):
    try:
        # 1. Generar respuesta con Gemini
        # Le damos un "rol" para que no se enrolle mucho
        prompt = f"Eres Bittle, un perro robótico simpático. Responde en una sola frase corta a esto: {text}"
        response = model.generate_content(prompt)
        answer = response.text
        print(f"🤖 Bittle dice: {answer}")

        # 2. Convertir texto a voz (gTTS)
        tts = gTTS(text=answer, lang='es')
        filename = "response.mp3"
        tts.save(filename)

        # 3. Reproducir el audio con Pygame
        pygame.mixer.init()
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()

        # Esperar a que termine de hablar
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        
        pygame.mixer.quit()
        
        # 4. Limpiar el archivo de audio temporal
        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        print(f"❌ Error en el cerebro de Tiago: {e}")