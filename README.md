# TiCare - Vision

This branch contains the final vision system for the TiCare project.

The `ticare_vision` package receives commands from the Communication and Navigation modules, processes the TIAGo RGB camera image with a YOLO model, detects the requested object and publishes `object_detected` when the object is found.

## Prerequisites

Operating System: Ubuntu 22.04 LTS (Jammy Jellyfish)  
ROS 2 Distribution: Humble Hawksbill  

This README assumes ROS 2 Humble is already installed on the computer.

## Installation

Follow these steps to set up the TiCare workspace and install all necessary dependencies.

### 1. Create Workspace and Clone Repository

Open a terminal and run the following commands to create your workspace and clone the vision branch:

```bash
mkdir -p ~/ticare_ws/src
cd ~/ticare_ws/src
git clone https://github.com/jmkaz16/TiCare.git -b vision .
```

### 2. Install ROS Dependencies

Install the ROS packages required by the Vision module:

```bash
sudo apt update
sudo apt install -y \
  python3-pip \
  python3-opencv \
  ros-humble-cv-bridge \
  ros-humble-control-msgs \
  ros-humble-trajectory-msgs \
  ros-humble-sensor-msgs \
  ros-humble-std-msgs
```

Then install any missing dependencies with `rosdep`:

```bash
cd ~/ticare_ws
rosdep update
rosdep install -i --from-paths src -y --rosdistro humble
```

If `rosdep` has never been initialized on the computer, run this once before the previous commands:

```bash
sudo rosdep init
rosdep update
```

### 3. Install Python Requirements

The package includes a `requirements.txt` file to simplify the Python installation.

```bash
cd ~/ticare_ws
python3 -m pip install --user -r ticare_vision/requirements.txt
```

The current requirements file includes:

```text
ultralytics>=8.3.0
numpy>=1.23,<2.0
```

OpenCV is installed with `apt` as `python3-opencv` to avoid conflicts with ROS 2 and `cv_bridge`.

### 4. Network Configuration (CycloneDDS)

For integration with the rest of the TiCare modules, we use CycloneDDS.

Install the RMW implementation:

```bash
sudo apt update && sudo apt install ros-humble-rmw-cyclonedds-cpp
```

Configure your environment by adding the following line to your `~/.bashrc`:

```bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

Restart your terminal or run:

```bash
source ~/.bashrc
```

### 5. Build the Workspace

Build the package using `colcon`:

```bash
cd ~/ticare_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select ticare_vision
```

## Usage

### Environment Setup

Before running the Vision module, source the TiCare workspace:

```bash
source ~/ticare_ws/install/local_setup.bash
```

You can add this line to your `~/.bashrc` to source it automatically in every new terminal.

### Launching the Vision Module on TIAGo

To start the Vision node using the real TIAGo camera:

```bash
ros2 launch ticare_vision vision_launch.launch.py
```

The node subscribes to the TIAGo camera topic:

```text
/head_front_camera/rgb/image_raw
```

The trained model must be located at:

```text
ticare_vision/data/weights.pt
```

### Launching the Vision Module with a Webcam

To test the Vision module without the real TIAGo camera:

```bash
ros2 launch ticare_vision vision_launch_sim.launch.py
```

By default, this uses camera `0`. To use another camera:

```bash
ros2 launch ticare_vision vision_launch_sim.launch.py camera_id:=1
```

## Integration Topics

All integration messages use:

```text
std_msgs/msg/String
```

### Inputs

| Topic | Message | Description |
|---|---|---|
| `/com2vis` | `head_up` | Raises the head and activates the Vision module. |
| `/com2vis` | `object_<object_name>` | Defines the object to search for, for example `object_bottle`. |
| `/com2vis` | `head_down` | Lowers the head and deactivates the Vision module. |
| `/com2vis` | `PE` | Emergency stop. |
| `/nav2vis` | `start_vis` | Starts visual search. |
| `/nav2vis` | `stop_vis` | Stops visual search. |
| `/nav2vis` | `PE` | Emergency stop. |

### Outputs

| Topic | Message | Description |
|---|---|---|
| `/vis2com` | `object_detected` | Object detected message for Communication. |
| `/vis2nav` | `object_detected` | Object detected message for Navigation. |

## Manual Integration Test

Run the Vision node in one terminal:

```bash
source ~/ticare_ws/install/local_setup.bash
ros2 launch ticare_vision vision_launch.launch.py
```

Listen to the output topics in two other terminals:

```bash
source ~/ticare_ws/install/local_setup.bash
ros2 topic echo /vis2com
```

```bash
source ~/ticare_ws/install/local_setup.bash
ros2 topic echo /vis2nav
```

Send the normal command sequence from another terminal:

```bash
source ~/ticare_ws/install/local_setup.bash

ros2 topic pub --once /com2vis std_msgs/msg/String "{data: 'head_up'}"
ros2 topic pub --once /com2vis std_msgs/msg/String "{data: 'object_bottle'}"
ros2 topic pub --once /nav2vis std_msgs/msg/String "{data: 'start_vis'}"
```

When the requested object is detected, the expected output is:

```text
data: object_detected
```

on both `/vis2com` and `/vis2nav`.

## Tests

To run the Vision module tests:

```bash
cd ~/ticare_ws
source /opt/ros/humble/setup.bash
source ~/ticare_ws/install/local_setup.bash
colcon test --packages-select ticare_vision --event-handlers console_direct+
colcon test-result --verbose
```

If a `pytest` plugin error appears, run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 colcon test --packages-select ticare_vision --event-handlers console_direct+
colcon test-result --verbose
```

## Development & Credits

This branch is maintained and developed by the Vision Team of the TiCare project, consisting of:

Daniel Franco – CEO & Requirements Manager  
Luis Gómez – CTO & Product Manager  
Marco Muñoz – Design & Modeling Manager  

The Vision module is designed to integrate with the Communication and Navigation modules through the agreed TiCare ROS 2 topics.
