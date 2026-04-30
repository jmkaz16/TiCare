# TiCare Navigation Architecture

## `ticare_interfaces`

- **Description:** Custom service and message definitions for the TiCare ecosystem.
    
- **Service:** `SavePose.srv`: 
    - Request: `string label` 
    - Response: `bool success`, `string message`
    
- **Dependencies:** `rosidl_default_generators` (buildtool_depend), `rosidl_default_runtime` (exec_depend), `rosidl_interface_packages` (member_of_group)
    

## `ticare_navigation`

- **Description:** Implementation of the navigation stack, pose recording, and state management.

- **Launch:** 
    - `ticare_navigation.launch.py`:  Main launch file. Aggregates both simulation and internal nodes.
    - `ticare_nodes.launch.py`: Launches the `nav_manager` and `pose_recorder` nodes.
    - `ticare_sim.launch.py`: Launches PAL Robotics packages simulation  with specific arguments.
    - `navigation_public_sim_ticare.launch.py`: Configures Tiago simulation with custom map.

- **Worlds:**

    - `car`: Original world.
    - `car_shifted_final_block`: Shifted world to match the spawning point with the real world location of TIAGo, using tables as blocks to ensure robust navigation.

    There are other iterations of the maps that have been obtained by hand editing or implementing python scripts.

- **Scripts:**
    - `modify_poses.py`: Shifts the original `car.world` by modifying the poses of each block.

- **Maps:**
    Each map is defined by a `.pgm` and a `.yaml` file:
    - `final_map`: Map used for navigation in the simulation, merge of `map` and `map_juan`.
    - `map`: Map of the entire CAR with some errors.
    - `map_juan`: Map of the Lab in the CAR.
    - `lab`: Map of the Lab, first iteration.


- **Node:** `nav_manager`

    - **Description:** High-level orchestrator that monitors localization quality (AMCL) and manages state transitions (Search, Navigation, Emergency).
        
    - **Interfaces:**
        - **Publishers:**
            
            - `/nav2vis` (`std_msgs/msg/String`): Sends commands (_"start_vis", "stop_vis"_) to the `ticare_vision` package to activate or deactivate the camera during the search phase.
            - `/nav2com` (`std_msgs/msg/String`): Communicates mission status (_"home"_, _"object_point"_) to the `ticare_communication` package.
            - `/cmd_vel` (`geometry_msgs/msg/Twist`): Sends velocity commands to rotate if the initial localization accuracy is insufficient. 
        
        - **Subscribers:**
            
            - `/vis2nav` (`std_msgs/msg/String`): Receives object detection status (_"object_detected"_) from `ticare_vision` package.
            - `/com2nav` (`std_msgs/msg/String`): Receives mission start commands (_"start_nav"_, _"return"_) from `ticare_communication` package.
                
        - **Service Clients:**
            
            - `/save_pose` (`ticare_interfaces/srv/SavePose`): Request to record start or target points.
                
        - **Action Clients:**
            
            - `/navigate_to_pose` (`nav2_msgs/action/NavigateToPose`): Sends the robot to the target using A* algorithm.
            - `/follow_waypoints` (`nav2_msgs/action/FollowWaypoints`): Executes coverage path planning.
                
    - **Entry Point:** `ticare_navigation.nav_manager:main`
        
    - **Dependencies:** `rclpy`, `ticare_interfaces`, `geometry_msgs`.
        

- **Node:** `pose_recorder`

    - **Description:** Persistence node responsible for receiving poses and storing them in YAML format.
        
    - **Interfaces:**
        - **Subscribers:**
        
            - `/amcl_pose` (`geometry_msgs/msg/PoseWithCovarianceStamped`): Catches the current pose for immediate saving.
        
        - **Service Servers:**
            
            - `/save_pose` (`ticare_interfaces/srv/SavePose`): Receives a label and saves the current pose.
                
    - **Entry Point:** `ticare_navigation.pose_recorder:main`
        
    - **Dependencies:** `rclpy`, `ticare_interfaces`, `geometry_msgs`, `rosidl_runtime_py`.





    
