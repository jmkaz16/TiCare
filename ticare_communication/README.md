# 🤖 TiCare - Communication Module

This branch contains the core voice-interaction system for the TiCare project.

The Communication Module provides:

- Wake-word detection using the word **"Tiago"**
- Audio recording from ROS 2 audio topics
- Speech-to-text using **OpenAI Whisper**
- Natural-language command parsing
- Text-to-speech responses
- Emergency stop detection
- Communication with the Vision and Navigation modules through ROS 2 topics

---

## Prerequisites

- **Operating System:** Ubuntu 22.04 LTS
- **ROS 2 Distribution:** Humble Hawksbill
- **Python:** 3.10
- **Audio hardware:** Functional microphone
- **Internet connection:** Required for some Python packages and for `gTTS`
- **ffmpeg:** Required by Whisper to read audio files

This README assumes the workspace is located at:

```bash
~/ros2_ws
```

and the virtual environment is located at:

```bash
~/ticare_venv/venv
```

---

# Installation

## 1. Create the ROS 2 workspace and clone the repository

If the workspace does not exist yet:

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
```

Clone the TiCare repository or the required branch:

```bash
git clone https://github.com/jmkaz16/TiCare.git -b communication_2 .
```

If the repository is already cloned, skip this step.

---

## 2. Clone `audio_common`

The Communication Module uses ROS 2 audio utilities for microphone input.

Inside the `src` folder:

```bash
cd ~/ros2_ws/src
git clone https://github.com/ros-drivers/audio_common.git -b ros2
```

This provides packages such as:

- `audio_capture`
- `audio_common_msgs`
- `sound_play_msgs`

---

## 3. Install system dependencies

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip ffmpeg portaudio19-dev python3-all-dev libasound-dev
```

`ffmpeg` is especially important because Whisper uses it internally to load audio files.

Check that it is installed:

```bash
ffmpeg -version
```

Install ROS dependencies:

```bash
cd ~/ros2_ws
rosdep update
rosdep install --from-paths src --ignore-src -r -y
```

If `rosdep` is not installed:

```bash
sudo apt install -y python3-rosdep2
```

---

# Virtual Environment Setup

The virtual environment must be created outside the ROS 2 workspace to avoid problems with `colcon`.

In this project, the virtual environment is stored in:

```bash
~/ticare_venv/venv
```

## 4. Create the virtual environment

First, create the folder:

```bash
mkdir -p ~/ticare_venv
```

Then create the virtual environment using `--system-site-packages`:

```bash
python3 -m venv ~/ticare_venv/venv --system-site-packages
```

The `--system-site-packages` option is important because it allows the virtual environment to access ROS 2 Python packages such as `rclpy`.

Activate the environment:

```bash
source ~/ticare_venv/venv/bin/activate
```

Check that the active Python belongs to the virtual environment:

```bash
which python
```

Expected result:

```bash
/home/ingenia/ticare_venv/venv/bin/python
```

---

## 5. Install Python dependencies

With the virtual environment activated:

```bash
python -m pip install --upgrade pip setuptools wheel
```

Install the required Python packages:

```bash
python -m pip install "numpy==1.24.4"
python -m pip install "coverage>=7.6.1"
python -m pip install "numba==0.59.1"
python -m pip install openai-whisper
python -m pip install SpeechRecognition gTTS pygame spacy rapidfuzz pynput
python -m spacy download es_core_news_sm
```

Whisper is installed with:

```bash
python -m pip install openai-whisper
```

but it is imported in Python as:

```python
import whisper
```

---

## 6. Verify the installation

Run:

```bash
source ~/ticare_venv/venv/bin/activate

python -c "import rclpy; print('rclpy OK')"
python -c "import whisper; print('Whisper OK')"
python -c "import spacy; spacy.load('es_core_news_sm'); print('spaCy Spanish model OK')"
python -c "import pygame; print('pygame OK')"
python -c "import rapidfuzz; print('rapidfuzz OK')"
```

If all commands print `OK`, the virtual environment is correctly configured.

---

# Build the Workspace

## 7. Build all packages

Use this order:

```bash
cd ~/ros2_ws

source /opt/ros/humble/setup.bash
source ~/ticare_venv/venv/bin/activate

colcon build --symlink-install

source install/setup.bash
```

If the build finishes correctly, check that the package exists:

```bash
ros2 pkg list | grep ticare
```

Check the available executables:

```bash
ros2 pkg executables ticare_communication
```

Expected executables include:

```bash
ticare_communication state_manager_TIAGo
ticare_communication state_manager_simulation
ticare_communication save_audio_TIAGo
ticare_communication save_audio_simulation
```

---

## 8. Build only the Communication Module

If only the Communication Module has changed, build only this package:

```bash
cd ~/ros2_ws

source /opt/ros/humble/setup.bash
source ~/ticare_venv/venv/bin/activate

colcon build --symlink-install --packages-select ticare_communication

source install/setup.bash
```

This is useful while debugging Python files such as:

- `state_manager_TIAGo.py`
- `state_manager_simulation.py`
- `audio_saver_TIAGo.py`
- `audio_saver_simulation.py`

---

# Usage

## 9. Source the environment

Every time a new terminal is opened, run:

```bash
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
source ~/ticare_venv/venv/bin/activate
source install/setup.bash
```

---

## 10. Launch the TIAGo version

Use `ros2 launch`, not `ros2 run`, because `com_launch_TIAGo.py` is a launch file.

```bash
ros2 launch ticare_communication com_launch_TIAGo.py
```

This launch file starts:

- `audio_capture_node`
- `state_manager_TIAGo`

---

## 11. Launch the simulation version

```bash
ros2 launch ticare_communication com_launch_simulation.py
```

This launch file starts:

- `audio_capture_node`
- `state_manager_simulation`

---

## 12. Run individual nodes

To run only the TIAGo state manager:

```bash
ros2 run ticare_communication state_manager_TIAGo
```

To run only the TIAGo audio saver:

```bash
ros2 run ticare_communication save_audio_TIAGo
```

To run only the simulation state manager:

```bash
ros2 run ticare_communication state_manager_simulation
```

To run only the simulation audio saver:

```bash
ros2 run ticare_communication save_audio_simulation
```

---

# Audio and Whisper Testing

## 13. Test Whisper with the recorded audio file

The audio saver stores the recorded file in:

```bash
/home/ingenia/ros2_ws/install/ticare_communication/share/ticare_communication/data/audio.wav
```

Create a quick Whisper test script:

```bash
nano ~/test_whisper_audio.py
```

Paste:

```python
import os
import whisper

AUDIO_PATH = "/home/ingenia/ros2_ws/install/ticare_communication/share/ticare_communication/data/audio.wav"

def main():
    if not os.path.exists(AUDIO_PATH):
        print(f"ERROR: File does not exist: {AUDIO_PATH}")
        return

    print(f"Loading audio from: {AUDIO_PATH}")
    print("Loading Whisper model...")

    model = whisper.load_model("base", device="cpu")

    print("Transcribing...")
    result = model.transcribe(
        AUDIO_PATH,
        language="es",
        fp16=False
    )

    print("\n===== TRANSCRIPTION =====")
    print(result["text"])
    print("=========================\n")

if __name__ == "__main__":
    main()
```

Run:

```bash
source ~/ticare_venv/venv/bin/activate
python ~/test_whisper_audio.py
```

If Whisper is working correctly, the transcription will be printed in the terminal.

---

## 14. Available Whisper models

The model is loaded in the code with:

```python
model = whisper.load_model("base", device="cpu")
```

Recommended models:

| Model | Speed | Accuracy | Recommended use |
|---|---|---|---|
| `tiny` | Very fast | Low | Quick tests |
| `base` | Fast | Medium | Recommended for demos |
| `small` | Medium | Good | Better accuracy |
| `medium` | Slow | Very good | Not ideal for real time on CPU |
| `large` | Very slow | Best | Not recommended on CPU |
| `turbo` | Fast | Very good | Better with GPU |

For the TiCare demo, the recommended models are:

```python
model = whisper.load_model("base", device="cpu")
```

or:

```python
model = whisper.load_model("small", device="cpu")
```

---

# ROS 2 Interfaces

## Publishers

The Communication Module publishes commands to Vision and Navigation.

### `/com2vis`

Used to send commands to the Vision module.

Examples:

```text
head_up
head_down
object_bottle
object_mug
object_tennisball
object_apple
object_glasses
emergency_stop
```

### `/com2nav`

Used to send commands to the Navigation module.

Examples:

```text
start_nav
return
emergency_stop
```

---

## Subscribers

### `/vis2com`

Used to receive messages from Vision.

Expected messages:

```text
object_detected
```

### `/nav2com`

Used to receive messages from Navigation.

Expected messages:

```text
home
object_point
```

---

# Features

- Wake-word activation with **"Tiago"**
- Voice recording through ROS 2 audio topics
- Speech-to-text using **OpenAI Whisper**
- Spanish command parsing
- Fuzzy matching for actions and object names
- Text-to-speech using `gTTS` and `pygame`
- Emergency stop detection
- Coordination with Vision and Navigation
- ROS 2 multi-threaded executor
- TIAGo and simulation launch files

---

# Common Problems

## `No executable found`

This usually happens when trying to run a launch file with `ros2 run`.

Incorrect:

```bash
ros2 run ticare_communication com_launch_TIAGo.py
```

Correct:

```bash
ros2 launch ticare_communication com_launch_TIAGo.py
```

---

## `ModuleNotFoundError: No module named 'whisper'`

Install Whisper inside the virtual environment:

```bash
source ~/ticare_venv/venv/bin/activate
python -m pip install openai-whisper
```

Then rebuild:

```bash
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
source ~/ticare_venv/venv/bin/activate
colcon build --symlink-install --packages-select ticare_communication
source install/setup.bash
```

---

## `FileNotFoundError: No such file or directory: 'ffmpeg'`

Install `ffmpeg`:

```bash
sudo apt update
sudo apt install -y ffmpeg
```

Check:

```bash
ffmpeg -version
```

---

## `NameError: name 'sr' is not defined`

This means the code is still using the old `speech_recognition` transcription logic.

For Whisper, the transcription function must call:

```python
result = model.transcribe(ruta_wav, language="es", fp16=False)
```

Whisper should receive the path to the `.wav` file, not a `speech_recognition` audio object.

---

## `SyntaxError: unterminated string literal`

This is usually caused by a broken string in one of the Python files.

For example, this is incorrect:

```python
self.sub = self.create_subscription(AudioData, "/audio, self.audio_callback, 5)
```

Correct version:

```python
self.sub = self.create_subscription(AudioData, "/audio", self.audio_callback, 5)
```

---

## `failed to create symbolic link`

If `colcon` fails with a symbolic link error, clean the affected packages:

```bash
cd ~/ros2_ws

rm -rf build/sound_play_msgs install/sound_play_msgs
rm -rf build/audio_common_msgs install/audio_common_msgs
rm -rf log

source /opt/ros/humble/setup.bash
source ~/ticare_venv/venv/bin/activate

colcon build --symlink-install
source install/setup.bash
```

If needed, clean the entire workspace:

```bash
cd ~/ros2_ws

rm -rf build install log

source /opt/ros/humble/setup.bash
source ~/ticare_venv/venv/bin/activate

colcon build --symlink-install
source install/setup.bash
```

---

## NumPy/SciPy warning

This warning may appear:

```text
A NumPy version >=1.17.3 and <1.25.0 is required
```

If the program still works, it can be ignored temporarily.

To reduce compatibility problems, this README installs:

```bash
numpy==1.24.4
```

inside the virtual environment.

---

# Development & Credits

This branch is maintained and developed by the **Communication Team** of the TiCare project.

Team members:

- Nour — Communication & Interaction Manager
- Mario — AI Models Implementation

Detailed technical information about nodes and interfaces can be found in:

```bash
ticare_communication/docs/architecture.md