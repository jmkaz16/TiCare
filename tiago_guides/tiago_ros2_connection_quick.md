# TIAGo ROS 2 Quick Connect

Robot:

- Domain: `29`
- Wi-Fi IP: `10.42.0.1`
- Wired IP: `10.68.0.1`

## PC

Bashrc Configuration:

source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=29 #choose a numer of your choice, between 1 and 101
unset ROS_LOCALHOST_ONLY
source ~/ros2_ws/install/local_setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
source /usr/share/gazebo/setup.sh
source ~/ticare_ws/install/local_setup.bash
source ~/ticare_ws/src/tiago_guides/tiago_ros2_auto_env.sh

```bash
source /opt/ros/humble/setup.bash   # or /opt/ros/jazzy/setup.bash
source ~/ticare_ws/src/tiago_guides/tiago_ros2_auto_env.sh
ros2 topic list --no-daemon --spin-time 20
```

The script auto-detects Wi-Fi or wired and creates:

```bash
~/.ros/cyclonedds_tiago_auto.xml
```

Force one mode:

```bash
TIAGO_MODE=wifi source ~/ticare_ws/src/tiago_guides/tiago_ros2_auto_env.sh
TIAGO_MODE=wired source ~/ticare_ws/src/tiago_guides/tiago_ros2_auto_env.sh
```

## Test PC To Robot

Robot terminal:

```bash
ssh pal@10.42.0.1   # Wi-Fi
# or: ssh pal@10.68.0.1

source /opt/pal/alum/setup.bash
export ROS_DOMAIN_ID=29
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
unset ROS_LOCALHOST_ONLY

ros2 topic echo /test_from_pc std_msgs/msg/String \
  --qos-reliability best_effort --qos-depth 5 --once
```

PC terminal:

```bash
ros2 topic pub -r 1 /test_from_pc std_msgs/msg/String "{data: hello from pc}" \
  --qos-reliability best_effort --qos-depth 5
```

## Docker

```bash
docker --context default exec -it --user user tiago-162-dev bash
source /opt/pal/alum/setup.bash
source /home/zzh/tiago_ros2_auto_env.sh
ros2 topic list --no-daemon --spin-time 20
```

## If It Fails

Check route:

```bash
ip route get 10.42.0.1   # Wi-Fi
ip route get 10.68.0.1   # wired
```

If only a few statistics topics appear, reboot the robot after switching
Wi-Fi/wired mode. Running ROS processes do not reload DDS config.

`Failed to parse type hash` warnings are usually harmless Jazzy/Humble noise.
