## 🤖 TIAGo Robot: Operation Guide

### 1. Initializing the Robot
To ensure a safe startup, follow these steps:

*   **Initial State:** TIAGo must be powered off at its charging station, ensuring the two metallic triangles are in direct contact with its front base.
*   **Manual Deployment:** Before powering it on, manually move the robot away from the base to an open area with enough clearance for arm movement.
*   **Powering On:** 
    1. Press the **Power Button** (it will turn red).
    2. Press the **button to its right** (it will turn green).
    3. The robot’s screen will turn on, displaying the current battery level.
*   **Booting:** Wait a few seconds for the robot to "wake up" (motor initialization). Keep a safe distance during this process, until some red lights in the base are ON. 
*   **Connection:** Connect to TIAGo's Wi-Fi network (**tiago-162-Hotspot**). Note that this is a local hotspot without internet access.
    *   **Password:** `PAL-H0tsp0t` (default)
    *   **Robot IP:** `10.42.0.1`

---

### 2. Operation via WebGUI
This is the easiest way to perform basic movements and monitor the system:

1. Open your browser and go to: [http://10.42.0.1](http://10.42.0.1)
2. **Credentials:** Username: `pal` / Password: `pal`.
3. **Teleoperation:** Inside the **"Teleop"** folder, you can control the base using a virtual joystick, as well as move the head and the arm.
4. **Modules:** Use the right-side panel (click on TIAGo's image) to launch complex modules such as SLAM (mapping) or Navigation.

---

### 3. Operation via Terminal
To interact with ROS 2 from your own machine, you must configure your environment properly.

#### `.bashrc` Requirements
Add the following lines to the end of your `~/.bashrc` file:

```bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=29
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```
*Don't forget to run `source ~/.bashrc` after editing.*

#### Installing Dependencies
If you don't have Cyclone DDS installed, switch to a network with internet (like eduroam) and run:

```bash
sudo apt update
sudo apt install ros-humble-rmw-cyclonedds-cpp
```
*Switch back to the TIAGo hotspot once the installation is complete.*

#### Firewall and Connectivity
DDS relies on **multicast** messages, which are often blocked by default. You must disable the Linux firewall:

```bash
sudo ufw disable
```
> [!IMPORTANT]
> If you are using a **Virtual Machine**, disable the internal Linux firewall. Ensure your "Host" OS (Windows/Mac) is not blocking the VM's network traffic.

#### Interacting with ROS 2
To access the robot's internal terminal:
```bash
ssh pal@10.42.0.1
```

To view robot topics from **your local terminal** (without SSH), use:
```bash
ros2 topic list --no-daemon --spin-time 15
```
If new terminals only show a few local topics, use the `--spin-time` flag as shown above to force the discovery of nodes across the network.

---

### 4. Shutting Down the Robot
Follow this protocol to prevent damage to the motors or the arm:

1. **Safety Position:** Ensure the robot is near the base but maintains at least half a meter of lateral clearance.
2. **Home Posture:** In the WebGUI, click on **Motion Builder** (clapboard icon). Execute the **"Home"** action. This moves the robot to its safe default resting position.
3. **Motor Deactivation:** Press the **green button** on the base.
    *   **Warning:** Manually support the robot's arm. The motors will disengage in 5–10 seconds. Gently guide the arm down as it loses power to prevent it from hitting the torso.
4. **Final Power Off:** Once the arm is stable, press the **red button**.
5. **Charging:** Manually push the "sleeping" robot back into its charging station, ensuring the contacts are aligned as described at the beginning.
