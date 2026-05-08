# TiCare Vision V&V Test Plan

## Scope

These tests validate and verify the final TiCare vision module without requiring the physical TIAGo, Gazebo, the real camera or the real YOLO model. Hardware, OpenCV display windows and YOLO inference are replaced by test doubles so the tests are repeatable in `colcon test`.

## Requirements covered

| Requirement / interface | Evidence file |
|---|---|
| `/com2vis` accepts `head_up`, `object_<type>` and `head_down` | `test_vision_state_machine.py`, `test_vision_contract_static.py` |
| `/nav2vis` accepts `start_vis`, `stop_vis` and `PE` | `test_vision_state_machine.py`, `test_vision_contract_static.py` |
| The node subscribes to `/head_front_camera/rgb/image_raw` and does not create a new camera topic | `test_vision_contract_static.py` |
| When the target object is detected, the node publishes `object_detected` to `/vis2com` and `/vis2nav` | `test_vision_detection.py` |
| The node does not publish detection if the detected class is not the requested target | `test_vision_detection.py` |
| Bad image conversion is handled without crashing or publishing false positives | `test_vision_detection.py` |
| Head motion commands create a valid `FollowJointTrajectory` goal for `head_1_joint` and `head_2_joint` | `test_vision_head_goal.py` |

## How to run

From the ROS 2 workspace root:

```bash
source /opt/ros/humble/setup.bash
colcon build --packages-select ticare_vision
source install/setup.bash
colcon test --packages-select ticare_vision --event-handlers console_direct+
colcon test-result --verbose
```

To run only the functional validation tests and ignore style linters:

```bash
colcon test --packages-select ticare_vision --pytest-args -k "vision_"
colcon test-result --verbose
```
