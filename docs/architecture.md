# TiCare Navigation Architecture

### `ticare_interfaces`

- **Description:** Custom service and message definitions for the TiCare ecosystem.
    
- **Service:** `SavePose.srv`: 
    - Request: `string label` 
    - Response: `bool success`, `string message`
    
- **Dependencies:** `rosidl_default_generators` (buildtool_depend), `rosidl_default_runtime`(exec_depend), `rosidl_interface_packages` (member_of_group)
    

### `ticare_navigation`

- **Description:** Implementation of the navigation stack, pose recording, and state management.

- **Launch Files:** 
    - `ticare_navigation.launch.py`:  Main launch file. Aggregates both simulation and internal nodes.
    - `ticare_nodes.launch.py:` Launches the `nav_manager` and `pose_recorder` nodes.
    - `ticare_sim.launch.py`: Launches Pal Robotics packages simulation  with specific arguments. 
    

- **Node:** `nav_manager`

    - **Description:** High-level orchestrator that monitors localization quality (AMCL) and manages state transitions (Search, Navigation, Emergency).
        
    - **Interfaces:**
        
        - **Subscribers:**
            
            - `/amcl_pose` (`geometry_msgs/msg/PoseWithCovarianceStamped`): Monitor localization metrics.
                
        - **Service Clients:**
            
            - `save_pose` (`ticare_interfaces/srv/SavePose`): Request to record start or target points.
                
            - `/map_server/load_map` (`nav2_msgs/srv/LoadMap`): Loads the map prior to search initialization.
                
        - **Action Clients:**
            
            - `/navigate_to_pose` (`nav2_msgs/action/NavigateToPose`): Sends the robot to the target using A* algorithm.
                
            - `/follow_waypoints` (`nav2_msgs/action/FollowWaypoints`): Executes coverage path planning.
                
    - **Entry Point:** `ticare_navigation.nav_manager:main`
        
    - **Dependencies:** `rclpy`, `ticare_interfaces`, `geometry_msgs`.
        

- **Node:** `pose_recorder`

    - **Description:** Persistence node responsible for receiving poses and storing them in YAML format.
        
    - **Interfaces:**
        - **Subscribers:**
        
            - `amcl_pose` (`geometry_msgs/msg/PoseWithCovarianceStamped`): Caches the current pose for immediate saving.
        
        - **Service Servers:**
            
            - `save_pose` (`ticare_interfaces/srv/SavePose`): Receives a label and saves the current pose.
                
    - **Entry Point:** `ticare_navigation.pose_recorder:main`
        
    - **Dependencies:** `rclpy`, `ticare_interfaces`, `geometry_msgs`, `rosidl_runtime_py`.