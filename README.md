# TiCare - Navigation

This branch contains the core navigation system for the TiCare project.

## Prerequisites

- **Operating System:** Ubuntu 22.04 LTS (Jammy Jellyfish)
- **ROS 2 Distribution:** Humble Hawksbill

## Installation

Follow these steps to set up the TiCare workspace and install all necessary dependencies.

### 1. Create Workspace and Clone Repository

Open a terminal and run the following commands to create your workspace and clone the navigation branch:

```sh
mkdir -p ~/ticare_ws/src
cd ~/ticare_ws/src
git clone https://github.com/jmkaz16/TiCare.git -b navigation .
```

### 2. Import External Dependencies

TiCare relies on the PAL Robotics simulation environment. Use `vcs` to import the required public repositories:

```sh
vcs import --input https://raw.githubusercontent.com/pal-robotics/tiago_tutorials/humble-devel/tiago_public.repos
```

### 3. Patch Lidar Configuration

There is a known issue with the GPU lidar in the current simulation version. We provide a patch script to fix this:

```sh
chmod +x patch_lidar.sh
./patch_lidar.sh
```

_Verify that the output displays **"Lidar fixed!"**. If an error occurs, ensure you are in the correct directory._

### 4. Network Configuration (CycloneDDS)

For optimal performance in ROS 2 Humble, we use `cyclonedds`.

1. Install the RMW implementation:
    
    ```sh
    sudo apt update && sudo apt install ros-humble-rmw-cyclonedds-cpp
    ```
    
2. Configure your environment by adding the following line to your `~/.bashrc`:
    
    ```
    export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
    ```
    
3. Restart your terminal or run `source ~/.bashrc`.
    

### 5. Install ROS Dependencies

Navigate to the root of your workspace and use `rosdep` to install all missing system dependencies:

```sh
cd ~/ticare_ws
sudo rosdep init
rosdep update
rosdep install -i --from-paths src -y --rosdistro humble
```

### 6. Build the Workspace

Build the packages using `colcon`. Note that we explicitly allow overriding specific PAL packages to ensure compatibility:

```sh
source /opt/ros/humble/setup.bash
colcon build --symlink-install --allow-overriding pal_urdf_utils launch_pal
```

## Usage

### Environment Setup

Before running any application, you must source the TiCare workspace:

```sh
source ~/ticare_ws/install/local_setup.bash
```

_You can add this line to your `~/.bashrc` to source it automatically in every new terminal._

### Launching the Simulation

To start the TIAGo robot simulation in Gazebo with the TiCare navigation nodes:

```
ros2 launch ticare_navigation ticare_sim.launch.py
```

## Development & Credits

This branch is mantained and developed by the Navigation Team of the TiCare project, consisting of:

- **Catalina Morán** – Construction & Test Manager
- **Juan Martínez** –  Project, Documentation & Tool Manager
- **Lucas Goñi** – Assurance, Quality, Impact & Sustainability Manager

Detailed technical information about nodes and interfaces can be found in the [Architecture Guide](./docs/architecture.md).
