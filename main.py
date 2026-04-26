import os
from stt.stt_engine import listen_to_google
from stt.gpt_engine import chat_and_speak  
from input.command_map import COMMAND_MAP

# def main():
#     print("🤖 TiCare Active. Di una orden o di 'Tiago' para hablar conmigo.")
    
#     while True:
#         text = listen_to_google()
        
#         if text:
#             text = text.lower().strip()
#             print(f"He oído: '{text}'")

#             # 1. Buscamos si es una orden exacta
#             found_cmd = None
#             for phrase, cmd_code in COMMAND_MAP.items():    #cambiar a lista de objetos
#                 if phrase in text:
#                     found_cmd = cmd_code
#                     break
            
#             if found_cmd:
#                 print(f"🎯 ORDEN DETECTADA: {found_cmd}")
#                 save_to_state(found_cmd)
                
#             # 2. EL NUEVO FILTRO: ¿Ha dicho mi nombre?
#             elif "tiago" in text:
#                 print("💬 ¡Me ha llamado a mí! Pensando respuesta...")
#                 # Quitamos el nombre para que a Gemini solo le llegue la pregunta
#                 texto_limpio = text.replace("tiago", "").replace("perro", "").strip()
#                 if texto_limpio == "":
#                     texto_limpio = "¡Dime hola!" # Por si solo dices "Tiago" y te callas
                
#                 chat_and_speak(texto_limpio)
                
#             # 3. Si no es orden ni me llama por mi nombre...
#             else:
#                 print("☁️ (Ignorando ruido de fondo...)")

# def save_to_state(command):
#     if not os.path.exists("state"): os.makedirs("state")
#     with open("state/order.txt", "w", encoding="utf-8") as f:
#         f.write(command)
#     print(f"💾 '{command}' guardado.")

# if __name__ == "__main__":
#     main()

def main():
    print("---------------------------------------")
    print("🚀 TIAGO ESTÁ ESCUCHANDO...")
    print(" (Habla ahora y él te responderá) ")
    print("---------------------------------------")

    while True:
            # 1. Llamamos a la función que escucha por el micro
            text = listen_to_google()
            
            # 2. Si el micro ha pillado algo de texto...
            if text:
                print(f"👤 Tú dijiste: {text}")
                
                # 3. Llamamos a la función de Gemini para que interprete y responda
                chat_and_speak(text)

if __name__ == "__main__":
    main()