from google import genai
import os
from dotenv import load_dotenv

# 1. Cargamos llave
with open("stt/API.txt", "r") as f:
    MI_CLAVE = f.read().strip()

# 2. Configurar el cliente y el modelo más estable/rápido
client = genai.Client(api_key=MI_CLAVE)


#MODEL_ID = "gemini-3.1-flash-live-preview" # Sigue sin funcionar

def chat_and_speak(text):
    try:
# 3. Gemini que interpreta y responde
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=f"Responde de forma muy breve y simpática: {text}"
        )
        print(f"\n🤖 Tiago: {response.text}\n")
    except Exception as e:
        print(f"❌ Error en Gemini: {e}")    

# def chat_and_speak(text): # Mantenemos el nombre para no tener que tocar main.py
#     try:
#         # Solo generamos texto y lo imprimimos
#         prompt = f"Responde en una sola frase corta como un perro robótico simpático: {text}"
#         response = client.models.generate_content(
#             model=MODEL_ID,
#             contents=prompt
#         )
#         print(f"\n🤖 Tiago dice: {response.text}\n")

#     except Exception as e:
#         print(f"\n❌ Error en el cerebro de Tiago: {e}\n")