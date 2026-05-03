# TiCare Communication FSM

This document outlines the high‑level logic and state transitions for the `state_manager` node.  
The system follows a **Black Box integration model** using ROS 2 topics to coordinate with the Vision and Navigation packages.

---

# State Definitions

## **1. IDLE**
**Description:**  
The system is initialized and passively listening for the wake‑word (“Tiago”).

**Actions:**  
- Call `listen_for_wake_word()` every cycle.  
- Monitor emergency thread in parallel.

**Transition:**  
- Move to **WAKE_WORD_DETECTED** when the wake‑word is detected.

---

## **2. WAKE_WORD_DETECTED**
**Description:**  
Wake‑word detected; the robot prepares for interaction.

**Actions:**  
- Publish `"head_up"` to `/com2vis` to activate the camera.

**Transition:**  
- Move to **GREETING** immediately.

---

## **3. GREETING**
**Description:**  
Robot initiates verbal interaction.

**Actions:**  
- Speak: “¿Te puedo ayudar en algo?”

**Transition:**  
- Move to **LISTENING**.

---

## **4. LISTENING**
**Description:**  
Robot records and transcribes user speech.

**Actions:**  
- Record 5 seconds of audio.  
- Transcribe using Google STT.  
- Check for emergency keywords.

**Transition A:**  
- If valid text → **PROCESSING_REQUEST**  
**Transition B:**  
- If unclear speech → **RETRY_SPEECH**

---

## **5. PROCESSING_REQUEST**
**Description:**  
NLP module extracts the object name from the user command.

**Actions:**  
- Call `parse_command()`  
- Extract `object` field  
- Detect grammatical gender for TTS

**Transition A:**  
- If object found → **OBJECT_FOUND**  
**Transition B:**  
- If no object → **ERROR_NOT_FOUND**

---

## **6. RETRY_SPEECH**
**Description:**  
User speech was unclear.

**Actions:**  
- Speak: “No he entendido, ¿puedes repetirlo?”

**Transition:**  
- Return to **LISTENING**

---

## **7. SEND_TO_VISION**
**Description:**  
Robot initiates the search protocol.

**Actions:**  
- Publish `"object_<name>"` to `/com2vis`  
- Publish `"start_nav"` to `/com2nav`

**Transition:**  
- Move to **SEARCHING**

---

## **8. SEARCHING**
**Description:**  
Passive waiting state while Vision and Navigation operate.

**Actions:**  
- No internal actions  
- Await callbacks from `/vis2com` or `/nav2com`

**Transition A:**  
- If `/vis2com` sends `"object_detected"` → Navigation return triggered  
**Transition B:**  
- If `/nav2com` sends `"object_point"` → **POINTING**  
**Transition C:**  
- If `/nav2com` sends `"home"` → **GOING_HOME**

---

## **9. OBJECT_FOUND**
**Description:**  
Robot confirms the object name to the user.

**Actions:**  
- Speak: “Ok, iré a buscar el/la <objeto>”

**Transition:**  
- Move to **SEND_TO_VISION**

---

## **10. ERROR_NOT_FOUND**
**Description:**  
NLP failed to extract an object.

**Actions:**  
- Speak: “No he encontrado el objeto”

**Transition:**  
- Return to **IDLE**

---

## **11. GOING_HOME**
**Description:**  
Navigation reports that the robot has returned to the starting point.

**Actions:**  
- Speak: “Ya lo he encontrado, ¿me acompañas?”  
- Publish `"head_down"` to `/com2vis`

**Transition:**  
- Return to **IDLE**

---

## **12. POINTING**
**Description:**  
Robot has reached the object location.

**Actions:**  
- Speak: “Aquí está.”

**Transition:**  
- Return to **IDLE**

---

## **13. EMERGENCY_STOP**
**Description:**  
Global override triggered by emergency keywords (“robot para”, “stop”, etc.).

**Actions:**  
- Publish `"emergency_stop"` to `/com2vis`  
- Publish `"emergency_stop"` to `/com2nav`  
- Speak: “Parada de emergencia activada.”

**Transition:**  
- No transitions. System remains halted.

---

# Emergency Listener (Parallel Thread)

A dedicated thread continuously monitors wake‑word audio input for emergency keywords.

**Triggers:**  
- `"robot para"`  
- `"stop"`  
- `"emergency"`  

**Effect:**  
Immediately forces transition to **EMERGENCY_STOP**, overriding all other states.

---

# ROS 2 Interfaces

## Publishers

### `/com2vis`
- `"head_up"`  
- `"head_down"`  
- `"object_<name>"`  
- `"emergency_stop"`

### `/com2nav`
- `"start_nav"`  
- `"return"`  
- `"emergency_stop"`

---

## Subscribers

### `/vis2com`
- `"object_detected"`

### `/nav2com`
- `"object_point"`  
- `"home"`

---

# Future Improvements

- **Timeout Handling:** Add timeouts for LISTENING and SEARCHING.  
- **Error State:** Implement a dedicated recovery state for STT/NLP failures.  
- **Debug Interface:** Add `/state_manager/debug_set_state` for manual testing.  
- **Context Memory:** Allow multi‑turn conversations (e.g., “¿Qué objeto?”).  

---

# Summary

The Communication FSM provides a structured and reliable interaction pipeline between the user and the robot, coordinating Vision and Navigation through a robust state machine and a continuous emergency monitoring system.
