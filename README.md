# TiCare - Communication

This branch contains the core voice-interaction and audio communication system for the TIAGo robot within the TiCare project. The Communication Module enables human-robot interaction by processing vocal instructions, managing text-to-speech locutions, and coordinating actions with the Vision and Navigation modules through ROS 2 topics.

The module provides the following core capabilities:
* **Wake-word detection** using the designated word **"Tiago"**.
* **Audio recording** stream processing directly from ROS 2 audio topics.
* **Speech-to-text transcription** powered by **OpenAI Whisper**.
* **Natural language processing (NLP)** for command parsing and Spanish fuzzy matching.
* **Text-to-speech (TTS) responses** and locutions for robot feedback.
* **Emergency stop detection** for safety overrides.
* **Cross-module coordination** sending commands to Vision and Navigation systems.

## Prerequisites

Before proceeding with the installation, ensure your system meets the following requirements:
* **Operating System:** Ubuntu 22.04 LTS
* **ROS 2 Distribution:** Humble Hawksbill
* **Python Version:** 3.10
* **Audio Hardware:** A fully functional microphone setup
* **Network Status:** Active internet connection (required for certain Python packages and `gTTS`)
* **System Tools:** `ffmpeg` installed (required internally by Whisper to process audio streams)

This guide assumes the following standard workspace and environment paths:
* **ROS 2 Workspace:** `~/ros2_ws`
* **Virtual Environment:** `~/ticare_venv/venv`

## Installation

Follow these step-by-step instructions to set up the workspace, configure the Python virtual environment, and download the necessary dependencies.

### 1. Create Workspace and Clone Repository

If you do not have a workspace set up yet, create the directory and clone the communication branch:

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
git clone https://github.com/jmkaz16/TiCare.git -b communication_2 .
```

### 2. Import External Audio Dependencies

The module relies on the standard ROS 2 audio utilities for microphone capture. Navigate to your source folder and clone the repository:

```bash
cd ~/ros2_ws/src
git clone https://github.com/ros-drivers/audio_common.git -b ros2
```

### 3. Install System and ROS Dependencies

Update your system packages and install the audio processing libraries along with `ffmpeg`:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip ffmpeg portaudio19-dev python3-all-dev libasound-dev
```

Verify that `ffmpeg` is successfully configured:

```bash
ffmpeg -version
```

Initialize and run `rosdep` to download missing system dependencies across the workspace:

```bash
cd ~/ros2_ws
rosdep update
rosdep install --from-paths src --ignore-src -r -y
```

### 4. Configure Virtual Environment (.venv)

To isolate heavy speech recognition packages and avoid conflicts with `colcon`, a virtual environment must be created outside the ROS 2 workspace:

```bash
mkdir -p ~/ticare_venv
python3 -m venv ~/ticare_venv/venv --system-site-packages
```

*Note: The `--system-site-packages` flag is mandatory to grant the environment access to central ROS 2 Python bindings like `rclpy`.*

Activate the environment and verify the active Python path:

```bash
source ~/ticare_venv/venv/bin/activate
which python
```

### 5. Install Python Libraries

With the virtual environment activated, upgrade the core packaging utilities and install the required speech and NLP dependencies:

```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install "numpy==1.24.4"
python -m pip install "coverage>=7.6.1"
python -m pip install "numba==0.59.1"
python -m pip install openai-whisper
python -m pip install SpeechRecognition gTTS pygame spacy rapidfuzz pynput
python -m spacy download es_core_news_sm
```

### 6. Verify the Environment Installation

Run the following sanity checks to ensure all modules are accessible inside the virtual environment:

```bash
source ~/ticare_venv/venv/bin/activate

python -c "import rclpy; print('rclpy OK')"
python -c "import whisper; print('Whisper OK')"
python -c "import spacy; spacy.load('es_core_news_sm'); print('spaCy Spanish model OK')"
python -c "import pygame; print('pygame OK')"
python -c "import rapidfuzz; print('rapidfuzz OK')"
```

### 7. Build the Workspace

Ensure both your ROS 2 overlay and the virtual environment are sourced before compiling:

```bash
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
source ~/ticare_venv/venv/bin/activate

colcon build --symlink-install
source install/setup.bash
```

If you only want to build changes specific to this module, use package selection:

```bash
colcon build --symlink-install --packages-select ticare_communication
```

---

## Usage

### Environment Setup

Every time a new terminal session is started, you must source the workspace and the virtual environment:

```bash
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
source ~/ticare_venv/venv/bin/activate
source install/setup.bash
```

<h3>Launching the Module</h3>

Depending on whether you are running on the physical TIAGo robot or inside a simulation environment, execute the corresponding launch file:

* **For the Physical TIAGo Robot:**
  ```bash
  ros2 launch ticare_communication com_launch_TIAGo.py
  ```
* **For the Gazebo Simulation:**
  ```bash
  ros2 launch ticare_communication com_launch_simulation.py
  ```

### Running Individual Nodes

Alternatively, individual components can be executed manually:

```bash
# TIAGo Executables
ros2 run ticare_communication state_manager_TIAGo
ros2 run ticare_communication save_audio_TIAGo

# Simulation Executables
ros2 run ticare_communication state_manager_simulation
ros2 run ticare_communication save_audio_simulation
```

---

## Audio and Whisper Testing

To isolate and test audio recording capabilities alongside Whisper transcription without launching the full ROS 2 state machines, you can run a local test script.

The recorded audio is typically stored at:
`~/ros2_ws/install/ticare_communication/share/ticare_communication/data/audio.wav`

Create a test script named `~/test_whisper_audio.py` and execute it within the activated virtual environment to verify CPU-based transcription accuracy:

```bash
source ~/ticare_venv/venv/bin/activate
python ~/test_whisper_audio.py
```

### Available Whisper Models

The model can be adjusted within your configuration files. The following reference table lists the performance profiles on CPU devices:

| Model | Speed | Accuracy | Recommended Use |
|---|---|---|---|
| `tiny` | Very Fast | Low | Quick structural testing |
| `base` | Fast | Medium | **Default choice for live demos** |
| `small` | Medium | Good | Balanced choice for better precision |
| `medium` | Slow | Very Good | Not ideal for real-time CPU deployment |
| `large` | Very Slow | Best | Not recommended for CPU real-time systems |
| `turbo` | Fast | Very Good | Optimized for GPU architectures |

---

## ROS 2 Interfaces

### Publishers

* **`/com2vis` (`std_msgs/msg/String`):** Sends target instructions and camera state modifiers to the Vision module. *(e.g., `head_up`, `head_down`, `object_bottle`, `object_mug`, `emergency_stop`)*
* **`/com2nav` (`std_msgs/msg/String`):** Dispatches target coordinates triggers to the Navigation module. *(e.g., `start_nav`, `return`, `emergency_stop`)*

### Subscribers

* **`/vis2com` (`std_msgs/msg/String`):** Receives state updates from the Vision system. *(e.g., `object_detected`)*
* **`/nav2com` (`std_msgs/msg/String`):** Receives feedback signals from the Navigation architecture. *(e.g., `home`, `object_point`)*

---

## Troubleshooting

### `No executable found`
Ensure you are using `ros2 launch` rather than `ros2 run` when executing launch scripts:
```bash
ros2 launch ticare_communication com_launch_TIAGo.py
```

### `ModuleNotFoundError: No module named 'whisper'`
The virtual environment has either been deactivated or wasn't built correctly. Activate the `.venv` and install the package:
```bash
source ~/ticare_venv/venv/bin/activate
python -m pip install openai-whisper
```

### `FileNotFoundError: No such file or directory: 'ffmpeg'`
Whisper depends on the system binary of `ffmpeg`. Install it via `apt`:
```bash
sudo apt update && sudo apt install -y ffmpeg
```

### `failed to create symbolic link`
If `colcon build` fails due to safe symbolic linking constraints, clean your workspace build caches and rebuild:
```bash
cd ~/ros2_ws
rm -rf build/ install/ log/
colcon build --symlink-install
```

---

## Development & Credits

This branch is maintained and developed by the **Communication Team** of the TiCare project:

- **Nour Maimouni** - Communication & Liaisons Manager (Interaction Design)
- **Mario Guerra** - Simulation & Control Manager (AI Models Implementation)

Detailed technical information about nodes and interfaces can be found in the [Architecture Guide](./ticare_communication/docs/architecture.md).