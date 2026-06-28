# TiCare - Bittle

This branch contains the software development for the integration of the **Petoi Bittle** robot within the TiCare ecosystem, a startup created in the framework of the **IngenIA Robótica** course of the Master's in Industrial Engineering. TiCare designs robotic solutions for the home, focusing on companionship, assistance, and improving the quality of life for the elderly using the **TIAGo robot** platform.

## Project Overview

The primary objective is the implementation of **a voice control system for the Petoi Bittle robot**. The system utilizes advanced **speech recognition models such as Whisper and spaCy** and a **distributed architecture in ROS 2 nodes** to ensure that the robot responds robustly to natural language commands, effectively managing synonyms and action queues.

## System Architecture

The system is structured into the following packages:  
- [`bittle_communication`](https://github.com/jmkaz16/TiCare/tree/bittle/bittle_communication): Responsible for audio capture, speech recognition, natural language processing (NLP), and synonym mapping. It publishes the processed commands to the `/bittle_raw` topic.
- [`bittle_manager`](https://github.com/jmkaz16/TiCare/tree/bittle/bittle_manager): Acts as the logical core of the system. It implements a Finite State Machine (FSM) that manages the validation of critical commands and organizes an execution queue for multiple orders. It subscribes to `/bittle_raw` and publishes to `bittle_cmd`.
- [`bittle_actions`](https://github.com/jmkaz16/TiCare/tree/bittle/bittle_manager): Manages low-level communication with the robot's hardware. It subscribes to the `/bittle_cmd` topic and translates validated instructions into specific serial commands for the Petoi Bittle controller.
- [`bittle_bringup`](https://github.com/jmkaz16/TiCare/tree/bittle/bittle_bringup): Contains the launch files and parameter configurations (`.yaml`) necessary to start the complete system in a coordinated manner.

## Prerequisites

- **Operating System:** Ubuntu 22.04 LTS (Jammy Jellyfish)
- **ROS 2 Distribution:** Humble Hawksbill

## Installation

Follow these steps to set up your workspace and install all necessary dependencies.

### 1. Install System Dependencies

It is necessary to install the Linux audio dependencies and environment management tools before proceeding:

```bash
sudo apt update
sudo apt install python3-venv python3-pip portaudio19-dev libasound2-dev libportaudio2 ffmpeg
```

### 2. Create Workspace and Clone Repository

Open a terminal and run the following commands to create your workspace and clone the Bittle branch:

```bash
mkdir -p ticare_ws/src
cd ticare_ws/src
git clone -b bittle https://github.com/jmkaz16/ticare.git
```

### 3. Virtual Environment Management (.venv)

To avoid conflicts with system libraries and manage heavy dependencies (such as **Whisper** or **spaCy**), an isolated environment must be configured within the workspace:

```bash
cd ~/ticare_ws

# Create virtual environment
python3 -m venv .venv
touch .venv/COLCON_IGNORE

# Activate virtual environment
source .venv/bin/activate
```

Verify if the environment has been successfully activated using the `which python` command, which should return the path to the interpreter inside `.venv/bin/python`.

### 4. Install Python Dependencies

With the virtual environment active, install the required libraries for speech and natural language processing:

```bash
pip install -r src/bittle_communication/requirements.txt
```

## Usage

### Building the Workspace

To ensure that the ROS 2 nodes correctly link to the virtual environment libraries, build the package while keeping the environment active:

```bash
# Load the ROS 2 Humble environment
source /opt/ros/humble/setup.bash

# Build the workspace
cd ~/ticare_ws
colcon build --symlink-install

# Load the TiCare workspace
source install/setup.bash
```

### Running the System

To start the complete Bittle system, execute the main launch file and the script responsible for processing voice commands:

```bash
ros2 launch bittle_bringup bittle_complete.launch.py
python src/bittle_communication/bittle_communication/audio_processor.py
```

## Development & Credits

This branch is developed and maintained by the Bittle Team:

- **Catalina Morán:** General coordination, system architecture design, implementation and development of the `bittle_actions` and `bittle_manager` packages, and global system integration.
- **Juan Martínez:** System architecture design, implementation and development of the `bittle_communication` and `bittle_bringup` packages, and global system integration.
- **Mario Guerra:** Development of the speech recognition module, implementation of the synonym mapping system, and natural language processing (NLP).
- **Nour Maimouni:** Coordination, integration, and validation of the voice module.
- **Luis Gómez:** Development of the control logic for `bittle_manager` (_Pending validation_).

