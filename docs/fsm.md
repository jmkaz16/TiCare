# TiCare Navigation FSM

This document outlines the high-level logic and state transitions for the `nav_manager` node. The system follows a "Black Box" integration model using ROS 2 topics for inter-package communication.

## State Definitions

### 1. IDLE

- **Description:** System is initialized and waiting for a mission.
    
- **Actions:** Load the environment map (CAR model) via `/map_server/load_map`.
    
- **Transition:** Move to **LOCALIZING** upon receiving the `"start_nav"` message on the `/com2nav` topic.
    

### 2. LOCALIZING

- **Description:** Ensures the robot is properly situated in the environment.
    
- **Actions:** Monitor the `/amcl_pose` topic.
    
- **Transition:** Move to **SAVING_START_POSE** once the pose covariance falls below the predefined safety threshold.
    

### 3. SAVING_START_POSE

- **Description:** Records the starting position for the "Return Home" phase.
    
- **Actions:** Send an asynchronous request to the `pose_recorder` service with the label `"start_point"`. Once confirmed, publish `"start_vis"` to `/nav2vis` to activate the camera.
    
- **Transition:** Move to **SEARCHING**.
    

### 4. SEARCHING

- **Description:** Executes the search pattern in the target room.
    
- **Actions:** Start the `/follow_waypoints` action using points from `coverage_points.yaml`.
    
- **Transition A:** If `"object_detected"` is received from `/vis2nav`, cancel navigation and move to **SAVING_OBJECT_POSE**.
    
- **Transition B:** If the search timer expires (Timeout), move to **RETURNING_HOME**.
    

### 5. SAVING_OBJECT_POSE

- **Description:** Records the exact location of the identified object.
    
- **Actions:** Request the `pose_recorder` service to save the current pose as `"object_point"`. Publish `"object_point"` to `/nav2com` to notify the Communication module.
    
- **Transition:** Move to **RETURNING_HOME**.
    

### 6. RETURNING_HOME

- **Description:** Robot returns to the mission starting point.
    
- **Actions:** Execute the `/navigate_to_pose` action toward the stored `"start_point"`. Upon arrival, publish `"home"` to `/nav2com`.
    
- **Transition A:** If an `"object_point"` was successfully saved during this mission, move to **AWAITING_RETURN**.
    
- **Transition B:** If no object was found (Search Timeout), reset mission data and return to **IDLE**.
    

### 7. AWAITING_RETURN

- **Description:** Passive state waiting for user confirmation to guide them to the object.
    
- **Actions:** Wait for the `"return"` message on the `/com2nav` topic.
    
- **Transition:** Upon receiving `"return"`, move to **NAV_TO_OBJECT**.
    

### 8. NAV_TO_OBJECT

- **Description:** Robot guides the user to the detected object's location.
    
- **Actions:** Execute `/navigate_to_pose` using the stored `"object_point"`.
    
- **Transition:** Once the goal is reached, reset mission context and return to **IDLE**.
    

## TO-DO / Future Improvements

- [ ] **Error/Recovery State:** Implement a dedicated state to handle failures in linear flow (e.g., navigation goal unreachable, service timeout, or localization loss).
    
- [ ] **Dynamic Re-localization:** Add a recovery behavior in the **LOCALIZING** state if the robot remains static with high covariance for too long.