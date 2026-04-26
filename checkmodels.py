from google import genai
import os
from dotenv import load_dotenv

# Cargamos tu llave segura
load_dotenv()
MI_CLAVE = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=MI_CLAVE)

print("🔍 Buscando modelos disponibles en tu cuenta...\n")

# Le preguntamos a Google la lista oficial
try:
    for model in client.models.list():
        # Filtramos para que solo muestre los de tipo "generateContent" (los que hablan)
        if "generateContent" in model.supported_actions:
            # Quitamos el "models/" del principio para que te sea más fácil copiarlo
            nombre_limpio = model.name.replace("models/", "")
            print(f"✅ Modelo disponible: {nombre_limpio}")
            
    print("\n💡 COPIA el nombre de uno que empiece por 'gemini-1.5-flash' y pégalo en tu gpt_engine.py")
except Exception as e:
    print(f"Error al conectar: {e}")