import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

from enum import Enum
from std_msgs.msg import String
from ticare_interfaces.srv import SavePose
from nav2_msgs.action import NavigateToPose
from nav2_msgs.action import FollowWaypoints


class NavigationState(Enum):
    """
    Defines the states for the TiCare Navigation FSM.

    Attributes:
        IDLE: System is initialized and waiting for a mission.
        LOCALIZING: Ensures the robot is properly situated in the environment.
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
        """Initializes the NavManager node, sets up publishers, subscribers, services and action
        clients."""
        super().__init__("nav_manager")

        self.state = NavigationState.IDLE

        self.vision_pub = self.create_publisher(String, "nav2vis", 10)
        self.communication_pub = self.create_publisher(String, "nav2com", 10)

        self.vision_sub = self.create_subscription(String, "vis2nav", self.vision_callback, 10)
        self.communication_sub = self.create_subscription(
            String, "com2nav", self.communication_callback, 10
        )

        self.save_pose_client = self.create_client(SavePose, "save_pose")
        # self.load_map_client = self.create_client(LoadMap, "/map_server/load_map")

        self.nav_to_pose_client = ActionClient(self, NavigateToPose, "navigate_to_pose")
        self.follow_waypoints_client = ActionClient(self, FollowWaypoints, "follow_waypoints")

        self.get_logger().info(f"Navigation Manager initialized. Current state: {self.state.name}")

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
