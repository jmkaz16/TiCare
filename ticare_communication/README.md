# 🤖 TiCare - Communication Module

This branch contains the core voice‑interaction system for the TiCare project.  
It provides wake‑word detection, speech recognition, natural‑language processing, text‑to‑speech, and a 13‑state interaction manager that coordinates with the Vision and Navigation modules.

## Prerequisites

- **Operating System:** Ubuntu 22.04 LTS (Jammy Jellyfish) or Windows 10/11  
- **ROS 2 Distribution:** Humble Hawksbill  
- **Python:** 3.10+  
- **Audio Hardware:** Functional microphone (PyAudio compatible)

# Installation

Follow these steps to set up the TiCare workspace and install all necessary dependencies.

---

### 1. Create Workspace and Clone Repository

Open a terminal and run the following commands to create your workspace and clone the communication branch:

```sh
mkdir -p ~/ticare_ws/src
cd ~/ticare_ws/src
git clone https://github.com/jmkaz16/TiCare.git -b communication_2 .
```
---

### 2. Clone audio_common (Required for audio recording)
The Communication Module depends on ROS 2 audio utilities. Clone the `audio_common` repository inside the `src` folder:

```sh
cd ~/ticare_ws/src
git clone https://github.com/ros-drivers/audio_common.git -b ros2
```
This provides the `audio_capture` and `audio_play` nodes used internally for microphone handling.


### 3. Install System Dependencies
```sh
cd ..
rosdep update
rosdep install --from-paths src --ignore-src -r -y
```
If `rosdep` is not install:
```sh
sudo apt install python3-rosdep2
```

---

### 4. Install Python Dependencies
It is advisable to install all libraries within a virtual enviroment to avoid conflict.
### 4.1. Create a venv
Skip this section if the `venv` has already been created in `ticare_ws/src`.

If `python3` is not install:
```sh
sudo apt update
sudo apt install python3-venv
```

Create the `venv`:
```sh
cd ~/ticare_ws
python3 -m venv venv
```

### 4.2. Install requirements.txt
Activate your `venv` and update the pip inside:
```sh
source venv/bin/activate
python3 -m pip install --upgrade pip
```

Inside the communication package:
```sh
cd ~/ticare_ws/src/ticare_communication
pip install -r requirements.txt
sudo apt install portaudio19-dev python3-all-dev libasound-dev
```
This installs:
- **SpeechRecognition (STT)**
- **PyAudio**
- **gTTS + pygame (TTS)**
- **spaCy + Spanish model**
- **rapidfuzz (fuzzy matching)**
- **pynput**

---

### 5. Build the Workspace
Build the packages using colcon. Note that the venv has to be deactivated for the colcon to be done properly:
```sh
source /opt/ros/humble/setup.bash
deactivate
colcon build --symlink-install
source venv/bin/activate
```

### 6. Libraries verification
Run the following script in terminal to ensure all libraries and models are successfully installed:
```sh
python3 - << 'EOF'
import importlib.util, subprocess, os, sys

def check_lib(name):
    spec = importlib.util.find_spec(name)
    print(f"{'✓' if spec else '✗'} {name}")

print(f"--- Entorno: {sys.prefix} ---")
libs = ["speech_recognition", "pyaudio", "gtts", "pygame", "spacy", "rapidfuzz", "pynput"]
[check_lib(l) for l in libs]

try:
    import spacy
    spacy.load('es_core_news_sm')
    print("✓ spaCy model (es_core_news_sm)")
except:
    print("✗ spaCy model (es_core_news_sm)")

has_ros2 = subprocess.call(["which","ros2"], stdout=subprocess.DEVNULL) == 0
print(f"{'✓' if has_ros2 else '✗'} ROS2 CLI")

if has_ros2:
    pkgs = subprocess.run(["ros2","pkg","list"], stdout=subprocess.PIPE, text=True).stdout
    print(f"{'✓' if 'ticare_communication' in pkgs else '✗'} ticare_communication (colcon or source error) ")
EOF
```
If any errors are detected, the libraries would have to be install manually (just the ones not already installed):
```sh
source venv/bin/activate
pip install SpeechRecognition gTTS pygame pynput
pip install numpy==1.26.4
pip install rapidfuzz==3.14.3
pip install spacy==3.7.5
```
Specially important is the `spacy`. If not install:
```sh
python3 -m spacy download es_core_news_sm
```
Return to the point 5 and then rerun the verification script.

---

## Usage

### Environment Setup

Before running any application, source the workspace:

```bash
source install/setup.bash
```

You can add this line to your `~/.bashrc` to source it automatically.
```bash
source ~/ticare_ws/install/setup.bash
```

---

### Launching the Communication Node

To start the TiCare Communication module:

```bash
ros2 launch ticare_communication communication_launch.py
```

This will start:
- Wake‑word detection  
- Speech‑to‑Text  
- NLP processing  
- State machine  
- Emergency listener thread  
- Communication with Vision and Navigation  

Before recording, check if the microphone has been succesfully open. A microphone icon has to appear in the right corner of the screen, close to the shut down one.

---

## Features

- Wake‑word activation (“Tiago”)  
- Speech‑to‑Text using Google Cloud  
- NLP command extraction using spaCy  
- Object request handling  
- Coordination with Vision and Navigation 
- 13‑state finite state machine  
- ROS 2 multi‑threaded executor  

---

## Development & Credits

This branch is maintained and developed by the **Communication Team** of the TiCare project, consisting of:

- Nour — Communication & Interaction Manager  
- Mario — Implantation of the IA models 

Detailed technical information about nodes and interfaces can be found in the **Architecture Guide** located in:

```
ticare_communication/docs/architecture.md
```

