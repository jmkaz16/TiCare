# TiCare – Communication

This branch contains the core communication system for the TiCare project.  
It provides the speech interface, NLP processing, wake‑word detection, and coordination with Vision and Navigation modules.

---

## Prerequisites

**Operating System:** Ubuntu 22.04 LTS (Jammy Jellyfish)  
**ROS 2 Distribution:** Humble Hawksbill  
**Python Version:** 3.10+  

---

## Installation

Follow these steps to set up the TiCare workspace and install all necessary dependencies.

---

### 1. Create Workspace and Clone Repository

Open a terminal and run:

```bash
mkdir -p ~/ticare_ws/src
cd ~/ticare_ws/src
git clone https://github.com/jmkaz16/TiCare.git -b communication .
```

This will clone the Communication branch directly into your workspace.

---

### 2. Install Python Dependencies

The Communication module relies on external Python libraries for STT, TTS, and NLP.

From the root of the package:

```bash
cd ~/ticare_ws/src/ticare_communication
pip3 install -r requirements.txt
```

If `pip3` is not installed:

```bash
sudo apt install python3-pip
```

---

### 3. Network Configuration (CycloneDDS)

For optimal ROS 2 performance, TiCare uses CycloneDDS.

Install the RMW implementation:

```bash
sudo apt update && sudo apt install ros-humble-rmw-cyclonedds-cpp
```

Add this line to your `~/.bashrc`:

```bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

Reload your environment:

```bash
source ~/.bashrc
```

---

### 4. Install ROS Dependencies

Navigate to the root of your workspace and install missing system dependencies:

```bash
cd ~/ticare_ws
sudo rosdep init
rosdep update
rosdep install -i --from-paths src -y --rosdistro humble
```

---

### 5. Build the Workspace

Build the packages using colcon:

```bash
source /opt/ros/humble/setup.bash
cd ~/ticare_ws
colcon build --symlink-install
```

---

## Usage

### Environment Setup

Before running any application, source the workspace:

```bash
source ~/ticare_ws/install/local_setup.bash
```

You can add this line to your `~/.bashrc` to source it automatically.

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

---

## Features

- Wake‑word activation (“Tiago”)  
- Speech‑to‑Text using Google Cloud  
- NLP command extraction using spaCy  
- Object request handling  
- Coordination with Vision and Navigation  
- Continuous emergency stop monitoring  
- 13‑state finite state machine  
- ROS 2 multi‑threaded executor  

---

## Development & Credits

This branch is maintained and developed by the **Communication Team** of the TiCare project, consisting of:

- Nour — Communication & Interaction Manager  
- (Añade aquí a tus compañeros si quieres)

Detailed technical information about nodes and interfaces can be found in the **Architecture Guide** located in:

```
ticare_communication/docs/architecture.md
```

---

## Contact

For issues, improvements, or contributions, please open a Pull Request or contact the TiCare Communication Team.

