# TiCare - Bittle
Este repositorio contiene el desarrollo de software para la integración del robot **Petoi Bittle** dentro del ecosistema **TiCare**, una startup creada en el marco de la asignatura **IngenIA Robótica del Máster en Ingeniería Industrial**.  TiCare diseña soluciones robóticas para el hogar, centradas en el acompañamiento, asistencia y mejora de la calidad de vida de personas mayores mediante el **robot TIAGo.**

## Descripción 

El objetivo principal es la **implementación de un sistema de control por voz para el robot Petoi Bittle.** El sistema utiliza **modelos de reconocimiento de voz avanzados como Whisper y spaCy** y una **arquitectura distribuida en nodos de ROS 2** para garantizar que el robot responda de manera robusta a comandos de lenguaje natural, gestionando sinónimos y colas de acciones.

## Arquitectura del Sistema

Se ha estructurado en los siguientes paquetes:

- [`bittle_communication`](https://github.com/jmkaz16/TiCare/tree/chucho/bittle_communication): Responsable de la captura de audio, el reconocimiento de voz, procesamiento del lenguaje natural y el mapeo de sinónimos. Publica las órdenes procesadas en el tópico `/bittle_raw`.
- [`bittle_manager`](https://github.com/jmkaz16/TiCare/tree/chucho/bittle_manager): Actúa como el núcleo lógico del sistema. Implementa una máquina de estados finita (FSM) que gestiona  la validación de comandos críticos y la organización de una cola de ejecución para órdenes múltiples. Se sucribe a `/bittle_raw` y publica en `bittle_cmd`.
- [`bittle_actions`](https://github.com/jmkaz16/TiCare/tree/chucho/bittle_manager): Gestiona la comunicación de bajo nivel con el hardware del robot. Se suscribe al tópico `/bittle_cmd` y traduce las instrucciones validadas en comandos serie específicos para el controlador de Petoi Bittle.
- [`bittle_bringup`](https://github.com/jmkaz16/TiCare/tree/chucho/bittle_bringup): Contiene los archivos de lanzamiento (`launch files`) y las configuraciones de parámetros (`.yaml`) necesarias para iniciar el sistema completo de manera coordinada.

## Contribuciones y reparto de responsabilidades


- **Catalina Morán:** Coordinación general, diseño de la arquitectura del sistema, implementación y desarrollo de los paquetes `bittle_actions` y `bittle_manager` e integración global del sistema.
- **Juan Martínez:** Diseño de la arquitectura del sistema, implementación y desarrollo de los paquetes `bittle_communication` y `bittle_bringup` e integración global del sistema.
- **Mario Guerra:** Desarrollo del módulo de reconocimiento de voz, implementación del sistema de mapeo de sinónimos y procesamiento de lenguaje natural (NLP).
- **Nour Maimouni:** Coordinación, integración y validación del módulo de voz.
- **Luis Gómez:** Desarrollo de la lógica de control de `bittle_manager`. (_Pendiente de validar_)
    

## Guía de Instalación y Configuración

### 1. Requisitos del Sistema Operativo

Es necesario instalar las dependencias de audio de Linux y las herramientas de gestión de entornos virtuales:

```bash
sudo apt update
sudo apt install python3-venv python3-pip portaudio19-dev libasound2-dev libportaudio2 ffmpeg
```

### 2. Configuración del Workspace

```bash
mkdir -p ticare_ws/src
cd ticare_ws/src
git clone -b chucho https://github.com/jmkaz16/ticare.git
```

### 3. Gestión del Entorno Virtual (.venv)

Para evitar conflictos con las librerías del sistema y gestionar dependencias pesadas (como **Whisper** o **spaCy**), se debe configurar un entorno aislado dentro del workspace:

```bash
cd ~/ticare_ws

# Crear entorno virtual
python3 -m venv .venv
touch .venv/COLCON_IGNORE

# Activar entorno virtual
source .venv/bin/activate
```

Se puede verificar si el entorno se ha activado correctamente mediante el comando `which python`, que debería devolver la ruta al intérprete en `.venv/bin/python`

### 5. Instalación de Dependencias de Python

Con el entorno activo, instale las librerías necesarias para el procesamiento de voz y lenguaje natural:

```bash
pip install -r src/bittle_communication/requirements.txt
```

## Compilación y Ejecución

Para que los nodos de ROS 2 se vinculen correctamente a las librerías del entorno virtual, se debe compilar el paquete manteniendo el entorno activo:

```bash
# Cargar el entorno de ROS 2 Humble
source /opt/ros/humble/setup.bash

# Compilación del workspace
cd ~/ticare_ws
colcon build --symlink-install

# Cargar el workspace de TiCare
source install/setup.bash
```

Para iniciar el sistema completo de Bittle, ejecute el archivo de lanzamiento principal y el script encargado de procesar las órdenes de voz:

```bash
ros2 launch bittle_bringup bittle_complete.launch.py
python src/bittle_communication/bittle_communication/audio_processor.py
```


## Enlaces

- 🌐 Web: [www.ticare.com](https://new-chat-n7ld.bolt.host/)
- 📸 Instagram: [@TiCare\_\_](https://instagram.com/TiCare__)
- 📧 Email: [ticare.ingenia@gmail.com](mailto:ticare.ingenia@gmail.com)
- 📍 Ubicación: [ETSII UPM](https://maps.app.goo.gl/VJqcJQks2CgoceWcA)
