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
        - **Publishers:**
            
            - `/nav2vis` (`std_msgs/msg/String`): Sends commands (_"start_vis"_) to the `ticare_vision` package to activate the camera during the search phase.
            - `/nav2com` (`std_msgs/msg/String`): Communicates mission status (_"home"_, _"object_point"_) to the `ticare_communication` package.
        - **Subscribers:**
            
            - `/amcl_pose` (`geometry_msgs/msg/PoseWithCovarianceStamped`): Monitor localization metrics.
            - `/vis2nav` (`std_msgs/msg/String`): Receives object detection status (_"object_detected"_) from `ticare_vision` package.
            - `/com2nav` (`std_msgs/msg/String`): Receives mission start commands (_"start_nav"_, _"return"_) from `ticare_communication` package.
                
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

- **Maps:**
    This folder contains the various iterations of maps that have been created. Each map is defined by a `.pgm` and a `.yaml` file:

    - **.pgm:** A grayscale occupancy grid image representing the environment, where pixels denote obstacles (black), free space (white), or unknown areas (gray).
    - **.yaml:** A metadata file defining the map's scale (resolution), origin, and thresholds to map image pixels to real-world coordinates.

    The final iteration of the map, hence the one used for navigation in the simulation is `final_map` for both the `.pgm` and the `.yaml` files.

- **Worlds:**
    This folder contains the Gazebo environment definitions used to synchronize the simulation with reality and ensure safe navigation:

    - **`original` / `shifted_car`**: Aligns the simulation coordinate system with the physical lab environment, ensuring the TIAGo robot spawns at its exact real-world starting coordinates.
    
    - **`shifted_block`**: The primary world used for simulation and mapping. It replaces tables with solid blocks to ensure the LIDAR detects them as impassable obstacles, preventing the robot from attempting to plan paths underneath them.


    
