# TiCare Vision Module

ROS 2 repository for the **Vision** module of the TiCare/TIAGo project.

This package runs a node called `vision_node`. The node implements a state machine that coordinates artificial vision, integration messages with the Communication and Navigation modules, object detection using YOLO, and TIAGo head movement.

The purpose of this `README` is to allow an external person to prepare the environment, understand the ROS 2 interfaces, install the required packages and run the code.

---

## 1. What this node does

The Vision node performs the following actions:

1. Receives commands from the Communication module through `/com2vis`.
2. Receives commands from the Navigation module through `/nav2vis`.
3. Subscribes to TIAGo's RGB camera topic: `/head_front_camera/rgb/image_raw`.
4. Converts ROS 2 `sensor_msgs/msg/Image` messages into OpenCV images using `cv_bridge`.
5. Runs YOLO inference using the `ultralytics` package and the trained model `weights.pt`.
6. Displays the camera image and the annotated YOLO detection image.
7. If the target object is detected, publishes `object_detected` to `/vis2com` and `/vis2nav`.
8. Moves TIAGo's head using the action `/head_controller/follow_joint_trajectory`.

The node does **not** create new integration topics. It only uses the agreed topics between the Communication, Navigation and Vision modules.

---

## 2. Recommended repository structure

```text
ticare_vision/
├── README.md
├── package.xml
├── setup.py
├── setup.cfg
├── requirements.txt
├── resource/
│   └── ticare_vision
├── ticare_vision/
│   ├── __init__.py
│   └── vision_node.py
├── launch/
│   └── vision.launch.py
├── config/
│   └── vision_params.yaml
├── data/
│   └── weights.pt              # usually not committed to Git; copied manually
├── docs/
│   ├── INTEGRATION_TOPICS.md
│   └── STATE_MACHINE.md
└── scripts/
    └── test_publish_sequence.sh
```

---

## 3. Full installation from scratch

Follow these steps in an Ubuntu 22.04 terminal.

### 3.1. Check Ubuntu version

```bash
lsb_release -a
```

The output should show Ubuntu 22.04 or equivalent.

---

### 3.2. Prepare Ubuntu repositories

```bash
sudo apt update
sudo apt install -y software-properties-common curl gnupg lsb-release locales git
sudo add-apt-repository universe -y
```

Configure locale, as recommended by ROS 2:

```bash
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
```

---

### 3.3. Add the official ROS 2 repository

```bash
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
```

```bash
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | \
  sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
```

Update packages:

```bash
sudo apt update
sudo apt upgrade -y
```

---

### 3.4. Install ROS 2 Humble and base tools

```bash
sudo apt install -y \
  ros-humble-desktop \
  ros-dev-tools
```

Activate ROS 2 in the current terminal:

```bash
source /opt/ros/humble/setup.bash
```

Make ROS 2 load automatically in future terminals:

```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
```

Check that ROS 2 is available:

```bash
ros2 --help
```

---

## 4. Install the specific packages required by this Vision node

Although `ros-humble-desktop` installs many packages, it is recommended to explicitly install the packages used by this Vision module.

```bash
sudo apt update
sudo apt install -y \
  python3-pip \
  python3-rosdep \
  python3-colcon-common-extensions \
  python3-opencv \
  python3-numpy \
  ros-humble-rclpy \
  ros-humble-std-msgs \
  ros-humble-sensor-msgs \
  ros-humble-control-msgs \
  ros-humble-trajectory-msgs \
  ros-humble-builtin-interfaces \
  ros-humble-cv-bridge \
  ros-humble-launch \
  ros-humble-launch-ros
```

These packages cover the ROS, action, image conversion and OpenCV imports required by the node.

---

## 5. Initialize rosdep

Run this once on the computer:

```bash
sudo rosdep init || true
rosdep update
```

The `|| true` part prevents the command from stopping if `rosdep` was already initialized.

---

## 6. Install Python dependencies for YOLO

Upgrade Python packaging tools:

```bash
python3 -m pip install --user --upgrade pip setuptools wheel
```

Install the packages listed in `requirements.txt`:

```bash
cd ~/ticare_ws
python3 -m pip install --user -r src/ticare_vision/requirements.txt
```

The `requirements.txt` file contains:

```text
ultralytics>=8.3.0
numpy>=1.23,<2.0
```

`ultralytics` usually installs additional dependencies such as `torch`, `torchvision`, `opencv-python`, `pillow`, `pyyaml`, `matplotlib`, `pandas` and other libraries needed to run YOLO.

Check that YOLO can be imported:

```bash
python3 - <<'PY'
from ultralytics import YOLO
import torch
print("Ultralytics imported correctly")
print("PyTorch:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())
PY
```

CUDA is not mandatory. If no GPU is available, YOLO will run on CPU, although inference will be slower.

---

## 7. Check all important imports before building

Run:

```bash
source /opt/ros/humble/setup.bash
python3 - <<'PY'
import rclpy
0.

from std_msgs.msg import String
from sensor_msgs.msg import Image
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint
from builtin_interfaces.msg import Duration
from cv_bridge import CvBridge
import cv2
from ultralytics import YOLO
print("All required imports work correctly")
PY
```

If this command fails, one or more dependencies are still missing.

---

## 8. Install package dependencies with rosdep

```bash
cd ~/ticare_ws
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y --rosdistro humble
```

---

## 9. Run the node

Terminal 1:

```bash
cd ~/ticare_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch ticare_vision vision.launch.py
```

If the model path must be provided manually:

```bash
ros2 launch ticare_vision vision.launch.py model_path:=/home/alejandro/ticare_ws/src/ticare_vision/data/weights.pt
```

The node can also be run directly:

```bash
ros2 run ticare_vision vision_node --ros-args \
  -p model_path:=/home/alejandro/ticare_ws/src/ticare_vision/data/weights.pt
```

---

## 10. Minimum test sequence

Terminal 1, run the node:

```bash
cd ~/ticare_ws
source install/setup.bash
ros2 launch ticare_vision vision.launch.py
```

Terminal 2, listen to the output sent to Navigation:

```bash
source ~/ticare_ws/install/setup.bash
ros2 topic echo /vis2nav
```

Terminal 3, send commands simulating Communication and Navigation:

```bash
source ~/ticare_ws/install/setup.bash
ros2 topic pub --once /com2vis std_msgs/msg/String "{data: 'head_up'}"
ros2 topic pub --once /com2vis std_msgs/msg/String "{data: 'object_bottle'}"
ros2 topic pub --once /nav2vis std_msgs/msg/String "{data: 'start_vis'}"
```

When YOLO detects the target object, the node will publish:

```text
object_detected
```

on:

```text
/vis2com
/vis2nav
```

Manual stop of active vision:

```bash
ros2 topic pub --once /nav2vis std_msgs/msg/String "{data: 'stop_vis'}"
```

Move head down:

```bash
ros2 topic pub --once /com2vis std_msgs/msg/String "{data: 'head_down'}"
```

Emergency stop:

```bash
ros2 topic pub --once /com2vis std_msgs/msg/String "{data: 'PE'}"
```

---

## 11. State machine sequence

Normal sequence:

```text
ESPERANDO_ORDEN
  receives /com2vis: head_up
PREPARANDO_VISION
  receives /com2vis: object_tipoDeObjeto
ESPERANDO_OBJETO
  receives /nav2vis: start_vis
BUSQUEDA_ACTIVA
  detects target object or receives /nav2vis: stop_vis
VISION_DETENIDA
  receives /com2vis: head_down
ESPERANDO_ORDEN
```

Emergency sequence:

```text
Any state + PE -> EMERGENCIA
```

---

## 12. Quick installation summary

If ROS 2 Humble is already installed, the minimum installation summary is:

```bash
sudo apt update
sudo apt install -y \
  python3-pip \
  python3-rosdep \
  python3-colcon-common-extensions \
  python3-opencv \
  python3-numpy \
  ros-humble-rclpy \
  ros-humble-std-msgs \
  ros-humble-sensor-msgs \
  ros-humble-control-msgs \
  ros-humble-trajectory-msgs \
  ros-humble-builtin-interfaces \
  ros-humble-cv-bridge \
  ros-humble-launch \
  ros-humble-launch-ros

source /opt/ros/humble/setup.bash
sudo rosdep init || true
rosdep update

mkdir -p ~/ticare_ws/src
cd ~/ticare_ws/src
git clone <REPOSITORY_URL> ticare_vision

cd ~/ticare_ws
python3 -m pip install --user --upgrade pip setuptools wheel
python3 -m pip install --user -r src/ticare_vision/requirements.txt
rosdep install --from-paths src --ignore-src -r -y --rosdistro humble
colcon build --symlink-install --packages-select ticare_vision
source install/setup.bash
```

Then place the model here:

```text
~/ticare_ws/src/ticare_vision/data/weights.pt
```

And run:

```bash
ros2 launch ticare_vision vision.launch.py
```

---

## 13. Files that should be committed to Git

Commit:

```text
README.md
package.xml
setup.py
setup.cfg
requirements.txt
ticare_vision/
launch/
config/
docs/
scripts/
.gitignore
```

Do not usually commit:

```text
weights.pt
*.onnx
*.engine
*.bag
*.db3
```

If the team wants to version `weights.pt`, use Git LFS.
