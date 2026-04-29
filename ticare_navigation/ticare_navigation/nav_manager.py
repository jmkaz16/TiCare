import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

from enum import Enum
from std_msgs.msg import String
from geometry_msgs.msg import Twist
from ticare_interfaces.srv import SavePose
from nav2_msgs.action import NavigateToPose
from nav2_msgs.action import FollowWaypoints


class NavigationState(Enum):
    """
    Defines the states for the TiCare Navigation FSM.

    Attributes:
        IDLE: System is initialized and waiting for a mission.
        LOCALIZING: Checks if a recovery rotation is needed to improve AMCL localization before 
        proceeding.
        SAVING_START_POSE: Records the starting position for the "Returning Home" phase.
        SEARCHING: Executes the search pattern in the target room.
        SAVING_OBJECT_POSE: Records the exact location of the identified object.
        RETURNING_HOME: Robot returns to the mission starting point.
        AWAITING_RETURN: Passive state waiting for the user confirmation to guide them to the
        object.
        NAV_TO_OBJECT: Robot guides the user to the detected object's location.
    """

    IDLE = 1
    LOCALIZING = 2
    SAVING_START_POSE = 3
    SEARCHING = 4
    SAVING_OBJECT_POSE = 5
    RETURNING_HOME = 6
    AWAITING_RETURN = 7
    NAV_TO_OBJECT = 8

class VisionCommand(Enum):
    """
    Defines the vision commands sent from NavManager to the ticare_vision package.

    Attributes:
        START_VIS: The robot has localized itself and activates the camera to start the search 
        protocol.
        STOP_VIS: The search protocol has finished, deactivate the camera.
    """
    
    START_VIS = "start_vis"
    STOP_VIS = "stop_vis"

class ComStatus(Enum):
    """
    Defines the communication statuses sent from NavManager to the ticare_communication package.

    Attributes:
        HOME: The robot has returned to the starting point.
        OBJECT_POINT: The robot has reached the location of the identified object.
    """

    HOME = "home"
    OBJECT_POINT = "object_point"

class SavePoseLabel(Enum):
    """
    Defines the labels for the poses saved by the SavePose service.

    Attributes:
        START_POSE: The starting position of the robot at the beginning of the mission.
        OBJECT_POSE: The position of the identified object after the search phase.
    """

    START_POSE = "start_pose"
    OBJECT_POSE = "object_pose"

class NavManager(Node):
    """
    High-level orchestrator that monitors localization quality (AMCL) and manages state transitions
    (Search, Navigation, Emergency).

    Attributes:
        state (NavigationState): The current state of the navigation FSM.

        vision_pub (Publisher): Sends commands ("start_vis", "stop_vis") to the ticare_vision
        package to activate or deactivate the camera during the search phase.
        communication_pub (Publisher): Communicates mission status ("home", "object_point") to the
        ticare_communication package.

        vision_sub (Subscription): Receives object detection status ("object_detected") from
        ticare_vision package.
        communication_sub (Subscription): Receives mission start commands ("start_nav", "return")
        from ticare_communication package.

        save_pose_client (Client): Request to record start or target points.

        nav_to_pose_client (ActionClient): Sends the robot to the target using A* algorithm.
        follow_waypoints_client (ActionClient): Executes coverage path planning.
    """

    def __init__(self) -> None:
        """Initializes the NavManager node, sets up publishers, subscribers, services, action
        clients and timers."""
        super().__init__("nav_manager")

        self.state : NavigationState = NavigationState.IDLE
        self.control_loop_period : float = 0.1 # [s] Period for the main control loop timer

        self.recovery_rotation_active : bool = False # Flag to indicate if recovery rotation needed
        self.recovery_rotation_duration : float = 30.0 # [s] Duration for the recovery rotation
        self.recovery_rotation_start_time : float = 0.0 # [s] Timestamp when the recovery starts
        self.recovery_rotation_speed : float = 0.5 # [rad/s] Angular speed during recovery rotation

        self.object_detected : bool = False # Flag to track if the object has been detected 

        self.search_duration : float = 300.0 # [s] Max duration for the search phase
        self.search_start_time : float = 0.0 # [s] Timestamp when the search phase starts


        self.vision_pub = self.create_publisher(String, "nav2vis", 10)
        self.communication_pub = self.create_publisher(String, "nav2com", 10)
        self.cmd_vel_pub = self.create_publisher(Twist, "cmd_vel", 10)

        self.vision_sub = self.create_subscription(String, "vis2nav", self.vision_callback, 10)
        self.communication_sub = self.create_subscription(
            String, "com2nav", self.communication_callback, 10
        )

        self.save_pose_client = self.create_client(SavePose, "save_pose")

        self.nav_to_pose_client = ActionClient(self, NavigateToPose, "navigate_to_pose")
        self.follow_waypoints_client = ActionClient(self, FollowWaypoints, "follow_waypoints")

        self.timer = self.create_timer(self.control_loop_period, self.control_loop_callback)

        self.get_logger().info(f"Navigation Manager initialized. Current state: {self.state.name}")
    
    def control_loop_callback(self) -> None:
        """Main control loop that orchestrates FSM transitions based on the current state."""
        match self.state:
            case NavigationState.IDLE:
                pass

            case NavigationState.LOCALIZING:
                if self.recovery_rotation_active:
                    self.perform_recovery_rotation()

                else:
                    self.send_save_pose_request(SavePoseLabel.START_POSE)
                    self.get_logger().info("Moving to SAVING_START_POSE.")
                    self.state = NavigationState.SAVING_START_POSE

            case NavigationState.SAVING_START_POSE:
                pass

            case NavigationState.SEARCHING:
                now = self.get_clock().now()
                elapsed_time = (now - self.search_start_time).nanoseconds / 1e9

                if elapsed_time > self.search_duration:

                    self.search_start_time = 0.0
                    self.publish_vision_command(VisionCommand.STOP_VIS)

                    self.get_logger().info("Search duration exceeded: Moving to RETURNING_HOME.")
                    self.state = NavigationState.RETURNING_HOME
                    
                # TODO: Implement cancel active search goal and send home goal

            case NavigationState.SAVING_OBJECT_POSE:
                pass

            case NavigationState.RETURNING_HOME:
                pass
            
            case NavigationState.AWAITING_RETURN:
                pass

            case NavigationState.NAV_TO_OBJECT:
                pass
    
    def perform_recovery_rotation(self) -> None:
        """Executes a recovery rotation to improve AMCL localization."""
        now = self.get_clock().now()
    
        if self.recovery_rotation_start_time == 0.0:
            self.recovery_rotation_start_time = now
            self.get_logger().info("Starting recovery rotation for localization.")
            return

        elapsed = (now - self.recovery_rotation_start_time).nanoseconds / 1e9
        
        if elapsed < (self.recovery_rotation_duration / 2):
            self.publish_cmd_vel_msg(0.0, self.recovery_rotation_speed)

        elif elapsed < self.recovery_rotation_duration:
            self.publish_cmd_vel_msg(0.0, -self.recovery_rotation_speed)

        else:
            self.publish_cmd_vel_msg(0.0, 0.0)
            self.recovery_rotation_active = False
            self.recovery_rotation_start_time = 0.0
            
            self.get_logger().info("Recovery rotation completed. Moving to SAVING_START_POSE.")
            self.state = NavigationState.SAVING_START_POSE
    
    def publish_cmd_vel_msg(self, linear_x: float, angular_z: float) -> None:
        """Publishes a Twist message to the cmd_vel topic.

        Args:
            linear_x (float): The linear velocity in the x direction [m/s].
            angular_z (float): The angular velocity around the z axis [rad/s].
        """
        msg = Twist()
        msg.linear.x = linear_x
        msg.angular.z = angular_z
        self.cmd_vel_pub.publish(msg)
    
    def publish_vision_command(self, command: VisionCommand) -> None:
        """Publishes a vision command to the ticare_vision package.

        Args:
            command (VisionCommand): The vision command to be published (e.g., START_VIS, STOP_VIS).
        """
        msg = String()
        msg.data = command.value
        self.vision_pub.publish(msg)
        self.get_logger().info(f"Published vision command: {command.name}")

    def publish_communication_status(self, status: ComStatus) -> None:
        """Publishes a communication status to the ticare_communication package.

        Args:
            status (ComStatus): The communication status to be published (e.g., HOME, OBJECT_POINT).
        """
        msg = String()
        msg.data = status.value
        self.communication_pub.publish(msg)
        self.get_logger().info(f"Published communication status: {status.name}")

    def send_save_pose_request(self, label: SavePoseLabel) -> None:
        """Sends a service request to save the current pose with the specified label.

        Args:
            label (SavePoseLabel): The label for the pose to be saved (e.g., START_POSE, 
            OBJECT_POSE).
        """

        # TODO: Implement service request to save the current pose with the specified label

    # TODO: Implement additional helper methods for sending navigation goals, etc.

    def vision_callback(self, msg: String) -> None:
        """
        Handles object detection status from the vision package.

        Args:
            msg (String): The message data from the vision node.
        """
        status = msg.data
        match status:
            case "object_detected":
                if self.state is NavigationState.SEARCHING:
                    self.object_detected = True
                    self.search_start_time = 0.0
                    self.get_logger().info("Object found: Moving to SAVING_OBJECT_POSE.")
                    self.state = NavigationState.SAVING_OBJECT_POSE

            case _:
                self.get_logger().warn(f"Unknown vision status: {status}")

    def communication_callback(self, msg: String) -> None:
        """
        Handles mission commands from the communication package.

        Args:
            msg (String): The message data containing the command.
        """
        command = msg.data
        match command:
            case "start_nav":
                if self.state is NavigationState.IDLE:
                    self.get_logger().info("Mission started: Moving to LOCALIZING")
                    self.state = NavigationState.LOCALIZING

            case "return":
                if self.state is NavigationState.AWAITING_RETURN:
                    self.get_logger().info("User request: Moving to NAV_TO_OBJECT")
                    self.state = NavigationState.NAV_TO_OBJECT

            case _:
                self.get_logger().warning(f"Unknown communication command: {command}")

    # TODO: Implement service and action client callbacks 
    def save_pose_response_callback(self, future) -> None:
        # TODO: If response is successful, publish "start_vis", "object_point" or "stop_vis" 
        # depending on the service request label or current state
        pass

    def nav_to_pose_response_callback(self, future) -> None:
        pass

    def nav_to_pose_result_callback(self, future) -> None:
        pass

    def follow_waypoints_response_callback(self, future) -> None:
        pass

    def follow_waypoints_result_callback(self, future) -> None:
        pass
    

def main(args=None) -> None:
    """Main function to initialize the NavManager node and start spinning."""
    rclpy.init(args=args)
    nav_manager = NavManager()

    try:
        rclpy.spin(nav_manager)

    except KeyboardInterrupt:
        pass

    finally:
        nav_manager.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
