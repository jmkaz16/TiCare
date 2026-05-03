# TiCare Communication Architecture

## ticare_communication

### Description
The *TiCare Communication* package implements the high‑level interaction layer between the user and the robot.  
It integrates:

- Wake‑word detection  
- Speech‑to‑Text (STT)  
- Natural Language Processing (NLP)  
- Text‑to‑Speech (TTS)  
- Coordination with Vision and Navigation modules  
- Emergency stop monitoring  

This package acts as the **entry point** for human‑robot interaction in the TiCare ecosystem.

---

## Package Structure

```
ticare_communication/
│
├── config/                 # STT/NLP configuration files
├── data/                   # Temporary audio files, logs
├── docs/                   # Documentation (architecture.md)
├── launch/                 # Launch files for the communication stack
├── resource/               # Package metadata
├── scripts/                # Helper scripts
│   └── stt_communitation   # Speech processing modules
├── ticare_communication/   # Python source code
│   ├── __init__.py
│   ├── state_manager.py    # Main communication node
├── package.xml
├── setup.py
├── setup.cfg
└── requirements.txt
```

---

## Launch Files

### communication_launch.py
Main launch file for the communication subsystem.

Responsibilities:

- Starts the `state_manager` node  
- Ensures multi‑threaded execution for emergency monitoring  
- Loads STT/NLP configuration parameters  
- Synchronizes with Vision and Navigation modules  

---

## Node: state_manager

### Description
High‑level orchestrator that manages:

- Wake‑word activation  
- Speech recording  
- Speech‑to‑Text  
- NLP command extraction  
- Object request handling  
- Coordination with Vision and Navigation  
- Emergency stop detection (parallel thread)  

This node implements a **13‑state finite state machine** that governs the entire communication workflow.

---

## Interfaces

### Publishers

#### `/com2vis` (std_msgs/msg/String)
Commands sent to the Vision module:

- `"head_up"` — Activate camera  
- `"head_down"` — Deactivate camera  
- `"object_<name>"` — Request object detection  
- `"emergency_stop"` — Global emergency stop  

#### `/com2nav` (std_msgs/msg/String)
Commands sent to the Navigation module:

- `"start_nav"` — Begin navigation to search area  
- `"return"` — Guide robot back to the object  
- `"emergency_stop"` — Global emergency stop  

---

### Subscribers

#### `/vis2com` (std_msgs/msg/String)
Feedback from Vision:

- `"object_detected"` — Object found → triggers navigation return  

#### `/nav2com` (std_msgs/msg/String)
Feedback from Navigation:

- `"object_point"` — Robot reached the object  
- `"home"` — Robot returned to initial position  

---

## Internal Threads

### Emergency Listener Thread
A dedicated parallel thread continuously monitors wake‑word audio input to detect emergency keywords such as:

- `"robot para"`  
- `"stop"`  
- `"emergency"`  

This thread ensures immediate interruption of:

- STT  
- NLP  
- Navigation  
- Vision  
- Any active state  

It triggers:

```
state = "EMERGENCY_STOP"
publish("emergency_stop") → /com2vis
publish("emergency_stop") → /com2nav
```

---

## State Machine Overview

The communication node implements a **13‑state FSM**:

1. IDLE  
2. WAKE_WORD_DETECTED  
3. GREETING  
4. LISTENING  
5. PROCESSING_REQUEST  
6. RETRY_SPEECH  
7. SEND_TO_VISION  
8. SEARCHING  
9. OBJECT_FOUND  
10. ERROR_NOT_FOUND  
11. GOING_HOME  
12. POINTING  
13. EMERGENCY_STOP  

Transitions are triggered by:

- STT results  
- NLP parsing  
- Vision feedback  
- Navigation feedback  
- Emergency listener thread  

---

## Entry Point

```
ticare_communication.state_manager:main
```

---

## Dependencies

### Runtime
- rclpy  
- std_msgs  
- numpy  
- sounddevice  
- speech_recognition  
- spacy  
- google-cloud-speech  

### Build
- ament_python  
- ament_cmake  
- rosidl_default_runtime  

---

## Summary
The *TiCare Communication* package provides the foundational interaction layer for the TiCare robot.  
It bridges human speech with autonomous robot behavior, coordinating Vision and Navigation through a robust state machine and a continuous emergency monitoring system.
