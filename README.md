# TiCare – Communication Module

This branch contains the core voice‑interaction system for the TiCare project.  
It provides wake‑word detection, speech recognition, natural‑language processing, text‑to‑speech, and a 13‑state interaction manager that coordinates with the Vision and Navigation modules.

## Prerequisites

- **Operating System:** Ubuntu 22.04 LTS (Jammy Jellyfish) or Windows 10/11  
- **ROS 2 Distribution:** Humble Hawksbill  
- **Python:** 3.10+  
- **Audio Hardware:** Functional microphone (PyAudio compatible)

## Installation

Follow these steps to set up the TiCare workspace and install all necessary dependencies.

---

### 1. Create Workspace and Clone Repository

Open a terminal and run:

```sh
mkdir -p ~/ticare_ws/src
cd ~/ticare_ws/src
git clone https://github.com/jmkaz16/TiCare.git -b communication_2 .
```
---

### 2. Clone audio_common (Required for audio recording)

The Communication Module depends on ROS 2 audio utilities. Clone the audio_common repository inside the src folder:

```sh
cd ~/ticare_ws/src
git clone https://github.com/ros-drivers/audio_common.git -b ros2
cd..
```
This provides the audio_capture and audio_play nodes used internally for microphone handling.


### 3. Install System Dependencies
```sh
cd..
rosdep install --from-paths src --ignore-src -r -y
```

### 4. Install Python Dependencies
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

### 5. Install spaCy Spanish Model (with verification)
Before downloading the model, you can verify if it is already installed:
```sh
python -c "import spacy; 
import pkgutil; 
print('Model installed' if pkgutil.find_loader('es_core_news_sm') else 'Model NOT installed')"
```
If the output is Model NOT installed, install it manually:
```sh
python -m spacy download es_core_news_sm
```

### 6. Build the Workspace
```sh
source /opt/ros/humble/setup.bash
colcon build --symlink-install
```

- 🌐 Web: [www.ticare.com](https://new-chat-n7ld.bolt.host/)
- 📸 Instagram: [@TiCare\_\_](https://instagram.com/TiCare__)
- 📧 Email: [ticare.ingenia@gmail.com](mailto:ticare.ingenia@gmail.com)
- 📍 Ubicación: [ETSII UPM](https://maps.app.goo.gl/VJqcJQks2CgoceWcA)
