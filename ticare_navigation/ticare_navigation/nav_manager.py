import os
from ament_index_python.packages import get_package_share_directory

import rclpy
from rclpy.node import Node
from rclpy.time import Time
from rclpy.action import ActionClient
from rclpy.action.client import ClientGoalHandle
from rclpy.task import Future

# from tf2_ros import Buffer, TransformListener

from enum import Enum
from rcl_interfaces.msg import ParameterDescriptor
from std_msgs.msg import String
from geometry_msgs.msg import Twist
from geometry_msgs.msg import PoseStamped
from ticare_interfaces.srv import SavePose
from nav2_msgs.action import NavigateToPose
from nav2_msgs.action import FollowWaypoints

import yaml
import time
from rosidl_runtime_py.set_message import set_message_fields


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

        timer (Timer): Main control loop timer that checks the current state and executes the
        corresponding behavior.

        data_dir (str): The directory path where the YAML files of the initial and object poses are
        saved.
        config_dir (str): The directory path where the YAML file of the coverage points is saved.
    """

    def __init__(self) -> None:
        """Initializes the NavManager node, sets up publishers, subscribers, services, action
        clients and timers."""
        super().__init__("nav_manager")

        self.state: NavigationState = NavigationState.IDLE
        self.control_loop_period: float = 0.1  # [s] Period for the main control loop timer

        self.declare_parameter(
            "recovery_rotation_duration",
            30.0,
            ParameterDescriptor(description="Duration for the recovery rotation in seconds"),
        )
        self.declare_parameter(
            "recovery_rotation_speed",
            0.5,
            ParameterDescriptor(description="Angular speed for the recovery rotation in rad/s"),
        )
        self.declare_parameter(
            "search_duration",
            300.0,
            ParameterDescriptor(description="Maximum duration for the search phase in seconds"),
        )

        self.recovery_rotation_active: bool = False  # Flag to indicate if recovery rotation needed
        self.recovery_rotation_duration: float = self.get_parameter(
            "recovery_rotation_duration"
        ).value  # [s] Duration for the recovery rotation
        self.recovery_rotation_start_time: Time = Time(
            nanoseconds=0, clock_type=self.get_clock().clock_type
        )  # [s] Timestamp when the recovery starts
        self.recovery_rotation_speed: float = self.get_parameter(
            "recovery_rotation_speed"
        ).value  # [rad/s] Angular speed during recovery rotation

        self.object_detected: bool = False  # Flag to track if the object has been detected
        self.cancel_goal_active: bool = False  # Flag to indicate if a cancel goal request is active

        self.search_duration: float = self.get_parameter(
            "search_duration"
        ).value  # [s] Max duration for the search phase
        self.search_start_time: Time = Time(
            nanoseconds=0, clock_type=self.get_clock().clock_type
        )  # [s] Timestamp when the search phase starts

        self.vision_pub = self.create_publisher(String, "nav2vis", 10)
        self.communication_pub = self.create_publisher(String, "nav2com", 10)
        self.cmd_vel_pub = self.create_publisher(Twist, "cmd_vel", 10)

        self.vision_sub = self.create_subscription(String, "vis2nav", self.vision_callback, 10)
        self.communication_sub = self.create_subscription(
            String, "com2nav", self.communication_callback, 10
        )

        # self.tf_buffer = Buffer()
        # self.tf_listener = TransformListener(self.tf_buffer, self)

        self.save_pose_client = self.create_client(SavePose, "save_pose")

        self.nav_to_pose_client = ActionClient(self, NavigateToPose, "navigate_to_pose")
        self.follow_waypoints_client = ActionClient(self, FollowWaypoints, "follow_waypoints")

        self.timer = self.create_timer(self.control_loop_period, self.control_loop_callback)

        self.get_logger().info(f"Navigation Manager initialized. Current state: {self.state.name}")

        package_share_path = get_package_share_directory("ticare_navigation")

        self.data_dir = os.path.join(package_share_path, "data")
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        self.config_dir = os.path.join(package_share_path, "config")
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

    def control_loop_callback(self) -> None:
        """Main control loop that orchestrates FSM transitions based on the current state."""
        match self.state:
            case NavigationState.IDLE:
                pass

            case NavigationState.LOCALIZING:
                if self.recovery_rotation_active:
                    self.perform_recovery_rotation()

                else:
                    self.get_logger().info("Moving to SAVING_START_POSE.")
                    self.state = NavigationState.SAVING_START_POSE
                    self.send_save_pose_request(SavePoseLabel.START_POSE)

            case NavigationState.SAVING_START_POSE:
                pass

            case NavigationState.SEARCHING:
                now = self.get_clock().now()
                elapsed_time = (now - self.search_start_time).nanoseconds / 1e9

                if elapsed_time > self.search_duration:

                    self.search_start_time = Time(
                        nanoseconds=0, clock_type=self.get_clock().clock_type
                    )
                    self.publish_vision_command(VisionCommand.STOP_VIS)

                    self.cancel_goal_active = True
                    cancel_future = self.follow_waypoints_goal_handle.cancel_goal_async()
                    cancel_future.add_done_callback(self.cancel_follow_waypoints_response_callback)

                    # self.get_logger().info("Search duration exceeded: Moving to RETURNING_HOME.")
                    # self.state = NavigationState.RETURNING_HOME
                    # self.send_nav_to_pose_goal(label=SavePoseLabel.START_POSE)

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

        if self.recovery_rotation_start_time.nanoseconds == 0:
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
            self.recovery_rotation_start_time = Time(
                nanoseconds=0, clock_type=self.get_clock().clock_type
            )

            self.get_logger().info("Recovery rotation completed. Moving to SAVING_START_POSE.")
            self.state = NavigationState.SAVING_START_POSE
            self.send_save_pose_request(SavePoseLabel.START_POSE)

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
        while not self.save_pose_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().warning("SavePose service is not available.")

        match label:
            case SavePoseLabel.START_POSE:
                self.get_logger().info("Requesting to save START_POSE.")

            case SavePoseLabel.OBJECT_POSE:
                self.get_logger().info("Requesting to save OBJECT_POSE.")

            case _:
                self.get_logger().warning(f"Unknown SavePose label: {label}")
                return

        future = self.save_pose_client.call_async(SavePose.Request(label=label.value))
        future.add_done_callback(self.save_pose_response_callback)

    def send_nav_to_pose_goal(self, label: SavePoseLabel) -> None:
        """Sends a goal to the NavigateToPose action server to navigate to the specified pose.

        Args:
            label (SavePoseLabel): The label of the pose to navigate to (e.g., START_POSE,
            OBJECT_POSE).
        """
        match label:
            case SavePoseLabel.START_POSE:
                self.get_logger().info("Sending NavigateToPose goal to return home.")
                file_name = os.path.join(self.data_dir, f"{label.value}.yaml")

            case SavePoseLabel.OBJECT_POSE:
                self.get_logger().info("Sending NavigateToPose goal to navigate to object.")
                file_name = os.path.join(self.data_dir, f"{label.value}.yaml")

            case _:
                self.get_logger().warn("Goal not recognized.")
                return

        with open(file_name, "r") as file:
            yaml_data = yaml.safe_load(file)

        goal_pose = PoseStamped()
        set_message_fields(goal_pose, yaml_data)

        # if label == SavePoseLabel.START_POSE:
        #     try:
        #         now = rclpy.time.Time()
        #         transform = self.tf_buffer.lookup_transform(
        #             "map", "base_footprint", now, timeout=rclpy.duration.Duration(seconds=1.0)
        #         )
        #         goal_pose.pose.orientation = transform.transform.rotation
        #         self.get_logger().info("Got current orientation")
        #     except Exception as e:
        #         self.get_logger().warn("Could not obtain orientation")

        goal_pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = goal_pose

        # self.get_logger().info(f"Goal send: '{goal_msg}'")

        self.nav_to_pose_client.wait_for_server()
        self.future = self.nav_to_pose_client.send_goal_async(
            goal_msg, feedback_callback=self.nav_to_pose_feedback_callback
        )
        self.future.add_done_callback(self.nav_to_pose_response_callback)

    def send_follow_waypoints_goal(self, room: str = "all") -> None:
        """Sends a goal to the FollowWaypoints action server to execute a coverage path.

        Args:
            room (str): The room for which to execute the coverage path. Default is "all",
            which executes the full path, other options (Lab_Paloma, Sala_D, etc.).
        """
        file_name = os.path.join(self.config_dir, "coverage_waypoints.yaml")
        with open(file_name, "r") as file:
            yaml_data = yaml.safe_load(file)

        raw_points = []
        if room == "all":
            for room_list in yaml_data.values():
                raw_points.extend(room_list)

        else:
            if room in yaml_data:
                raw_points = yaml_data[room]

            else:
                self.get_logger().warning(
                    f"Room '{room}' not found in coverage_points.yaml. No waypoints sent."
                )
                return

        waypoints = []
        current_time = self.get_clock().now().to_msg()
        for point in raw_points:
            msg = PoseStamped()
            set_message_fields(msg, point)
            msg.header.stamp = current_time
            waypoints.append(msg)

        goal_msg = FollowWaypoints.Goal()
        goal_msg.poses = waypoints
        self.follow_waypoints_client.wait_for_server()
        future = self.follow_waypoints_client.send_goal_async(
            goal_msg, feedback_callback=self.follow_waypoints_feedback_callback
        )
        future.add_done_callback(self.follow_waypoints_response_callback)

    def vision_callback(self, msg: String) -> None:
        """
        Handles object detection status from the vision package.

        Args:
            msg (String): The message data from the vision node.
        """
        status = msg.data
        match status:
            case "object_detected":
                if self.state == NavigationState.SEARCHING:
                    self.object_detected = True
                    self.search_start_time = Time(
                        nanoseconds=0, clock_type=self.get_clock().clock_type
                    )
                    cancel_future = self.follow_waypoints_goal_handle.cancel_goal_async()
                    cancel_future.add_done_callback(self.cancel_follow_waypoints_response_callback)

                    # self.nav_to_pose_goal_handle.cancel_goal_async()
                    # self.get_logger().info(
                    #     "Cancelling FollowWaypoints goal due to object detection."
                    # )
                    # cancel_follow_waypoints = self.follow_waypoints_client._cancel_goal_async(
                    #     self.follow_waypoints_goal_handle
                    # )
                    # cancel_follow_waypoints.add_done_callback(self.cancel_follow_waypoints_callback)
                    # self.cancel_goal_active = True
                    # self.get_logger().info("Object found: Moving to SAVING_OBJECT_POSE.")
                    # self.state = NavigationState.SAVING_OBJECT_POSE
                    # self.send_save_pose_request(SavePoseLabel.OBJECT_POSE)

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
                if self.state == NavigationState.IDLE:
                    self.get_logger().info("Mission started: Moving to LOCALIZING")
                    self.state = NavigationState.LOCALIZING

            case "return":
                if self.state == NavigationState.AWAITING_RETURN:
                    self.get_logger().info("User request: Moving to NAV_TO_OBJECT")
                    self.state = NavigationState.NAV_TO_OBJECT
                    self.send_nav_to_pose_goal(label=SavePoseLabel.OBJECT_POSE)

            case _:
                self.get_logger().warning(f"Unknown communication command: {command}")

    def save_pose_response_callback(self, future: Future) -> None:
        """
        Handles the response from the SavePose service.

        Args:
            future (Future): The future object representing the service call.
        """
        try:
            response = future.result()
            self.get_logger().info(f"SavePose service response: {response.success}")

            if response.success:
                self.get_logger().info("Pose saved successfully.")

                if self.state == NavigationState.SAVING_START_POSE:
                    self.publish_vision_command(VisionCommand.START_VIS)
                    self.get_logger().info("Starting search: Moving to SEARCHING.")
                    self.state = NavigationState.SEARCHING
                    self.search_start_time = self.get_clock().now()
                    self.send_follow_waypoints_goal()

                elif self.state == NavigationState.SAVING_OBJECT_POSE:
                    self.get_logger().info("Object pose saved: Moving to RETURNING_HOME.")
                    self.state = NavigationState.RETURNING_HOME
                    self.send_nav_to_pose_goal(label=SavePoseLabel.START_POSE)

            else:
                self.get_logger().error(f"Failed to save pose: {response.message}")
                self.get_logger().info("No pose saved: Moving to LOCALIZING.")
                self.state = NavigationState.LOCALIZING
                self.recovery_rotation_active = True

        except Exception as e:
            self.get_logger().error(f"Service call failed: {e}")

    def nav_to_pose_response_callback(self, future: Future) -> None:
        """
        Handles the response from the NavigateToPose action server.

        Args:
            future (Future): The future object representing the action goal response.
        """
        nav_to_pose_goal_handle: ClientGoalHandle = future.result()
        if not nav_to_pose_goal_handle.accepted:
            self.get_logger().error("NavigateToPose goal was rejected.")
            return

        self.get_logger().info("NavigateToPose goal accepted.")
        self.nav_to_pose_goal_handle = nav_to_pose_goal_handle

        self.nav_to_pose_result_future = self.nav_to_pose_goal_handle.get_result_async()
        self.nav_to_pose_result_future.add_done_callback(self.nav_to_pose_result_callback)

    def nav_to_pose_result_callback(self, future: Future) -> None:
        """
        Handles the result from the NavigateToPose action server.

        Args:
            future (Future): The future object representing the action result.
        """
        result = future.result().result
        self.get_logger().info(f"NavigateToPose result received: {result}")

        if self.state == NavigationState.RETURNING_HOME:
            self.publish_communication_status(ComStatus.HOME)
            if self.object_detected:
                self.get_logger().info("Returned home: Moving to AWAITING_RETURN.")
                self.state = NavigationState.AWAITING_RETURN
            else:
                self.get_logger().info("Returned home and no object detected: Moving to IDLE.")
                self.state = NavigationState.IDLE
                self.cancel_goal_active = False

        elif self.state == NavigationState.NAV_TO_OBJECT:
            self.publish_communication_status(ComStatus.OBJECT_POINT)
            self.get_logger().info("Arrived at object location. Mission complete: Moving to IDLE.")
            self.state = NavigationState.IDLE
            self.object_detected = False

    def nav_to_pose_feedback_callback(self, feedback_msg: NavigateToPose.Feedback) -> None:
        """
        Handles feedback from the NavigateToPose action server.

        Args:
            feedback_msg (NavigateToPose.Feedback): The feedback message from the action server.
        """
        feedback = feedback_msg.feedback.distance_remaining
        self.get_logger().debug(f"NavigateToPose feedback received: {feedback}")

        if feedback < 0.30 and self.state == NavigationState.RETURNING_HOME:
            self.get_logger().info(f"Near goal {feedback:.2f}, stopping rotation.")
            if hasattr(self, "nav_to_pose_goal_handle"):  # cancel goal
                self.nav_to_pose_goal_handle.cancel_goal_async()

    def follow_waypoints_response_callback(self, future: Future) -> None:
        """
        Handles the response from the FollowWaypoints action server.

        Args:
            future (Future): The future object representing the action goal response.
        """
        follow_waypoints_goal_handle: ClientGoalHandle = future.result()
        if not follow_waypoints_goal_handle.accepted:
            self.get_logger().error("FollowWaypoints goal was rejected.")
            return

        self.get_logger().info("FollowWaypoints goal accepted.")
        self.follow_waypoints_goal_handle = follow_waypoints_goal_handle

        self.follow_waypoints_result_future = self.follow_waypoints_goal_handle.get_result_async()
        self.follow_waypoints_result_future.add_done_callback(self.follow_waypoints_result_callback)

    def follow_waypoints_result_callback(self, future: Future) -> None:
        """
        Handles the result from the FollowWaypoints action server.

        Args:
            future (Future): The future object representing the action result.
        """
        result = future.result().result
        self.get_logger().info(f"FollowWaypoints result received: {result}")

        # TODO: When finished and not canceled
        time.sleep(0.5)
        if self.state == NavigationState.SEARCHING:
            if self.object_detected:
                self.get_logger().info("Object found: Moving to SAVING_OBJECT_POSE.")
                self.state = NavigationState.SAVING_OBJECT_POSE
                self.send_save_pose_request(SavePoseLabel.OBJECT_POSE)

            elif self.cancel_goal_active:
                self.get_logger().info("Search duration exceeded: Moving to RETURNING_HOME.")
                self.state = NavigationState.RETURNING_HOME
                self.send_nav_to_pose_goal(label=SavePoseLabel.START_POSE)

    def follow_waypoints_feedback_callback(self, feedback_msg: FollowWaypoints.Feedback) -> None:
        """
        Handles feedback from the FollowWaypoints action server.

        Args:
            feedback_msg (FollowWaypoints.Feedback): The feedback message from the action server.
        """
        feedback = feedback_msg.feedback.current_waypoint
        self.get_logger().debug(f"FollowWaypoints feedback received: {feedback}")

    def cancel_follow_waypoints_response_callback(self, future: Future) -> None:
        """
        Handles the response from cancelling the FollowWaypoints goal.

        Args:
            future (Future): The future object representing the cancel goal response.
        """
        cancel_response = future.result()
        if len(cancel_response.goals_canceling) > 0:
            self.get_logger().info("FollowWaypoints goal cancelled successfully.")
        else:
            self.get_logger().error(f"Failed to cancel FollowWaypoints goal: {cancel_response}")


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
