import os

from stt.stt_engine import listen_to_google
from input.commands import COMMAND_MAP


def main():
    print("🤖 TiCare System Active. Say 'STOP' to exit.")
    
    while True:
        text = listen_to_google()
        
        if text:
            text = text.lower() # Pasamos a minúsculas para comparar
            print(f"I heard: {text}")

            found_cmd= None

            sorted_phrases = sorted(COMMAND_MAP.keys(), key=len, reverse=True)

            for phrase in sorted_phrases:
                if phrase in text:
                    found_cmd = COMMAND_MAP[phrase]
                    break # En cuanto encontramos la coincidencia más larga, paramos


            if found_cmd:
                print(f"🎯 ORDEN RECONOCIDA: {found_cmd}")
                save_to_state(found_cmd)


            # BOTÓN DE SALIDA POR VOZ
            if "stop" in text or "exit" in text or "adiós" in text:
                print("👋 Closing TiCare. Goodbye!")
                break # Esto rompe el bucle y cierra el programa
            

            else:
                print("💬 Conversación general (No es una orden para Bittle)")
            
def save_to_state(command):
    """Guarda el código corto del comando en el archivo de estado"""
    folder = "state"
    if not os.path.exists(folder):
        os.makedirs(folder)
        
    file_path = os.path.join(folder, "order.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(command)
    print(f"💾 '{command}' escrito en {file_path}")



if __name__ == "__main__":
    main() 