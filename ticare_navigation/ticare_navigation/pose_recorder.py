import os
from ament_index_python.packages import get_package_share_directory

import rclpy
from rclpy.node import Node

from ticare_interfaces.srv import SavePose
from geometry_msgs.msg import PoseWithCovarianceStamped
from geometry_msgs.msg import PoseStamped

from rosidl_runtime_py.convert import message_to_yaml


class PoseRecorder(Node):
    """Node responsible for receiving poses and storing them in YAML format.

    Attributes:
        current_pose (PoseWithCovarianceStamped): The latest pose received from the /amcl_pose
        topic.
        srv (Service): Receives a label and saves the current pose.
        subscription (Subscription): Catches the current pose for immediate saving.
        data_dir (str): The directory path where the YAML files will be saved.
        covariance (float): The average covariance calculated from the pose's covariance matrix.
        data_to_save (PoseStamped): The pose data formatted for saving to a YAML file.
    """

    def __init__(self) -> None:
        """
        Initializes the PoseRecorder node, sets up the subscription to the /amcl_pose topic,
        and creates the save_pose service.
        """
        super().__init__("pose_recorder")

        self.current_pose = (
            None  # Initialize current_pose to None to handle possible crashes at startup
        )

        self.srv = self.create_service(SavePose, "save_pose", self.save_pose_callback)

        self.subscription = self.create_subscription(
            PoseWithCovarianceStamped, "amcl_pose", self.pose_callback, 10
        )
        self.subscription  # prevent unused variable warning

        package_share_path = get_package_share_directory("ticare_navigation")

        self.data_dir = os.path.join(package_share_path, "data")

        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def pose_callback(self, msg: PoseWithCovarianceStamped) -> None:
        """
        Callback function that updates the current pose and covariance based on incoming messages
        from the /amcl_pose topic.

        Args:
            msg (PoseWithCovarianceStamped): The message received from the /amcl_pose topic,
                containing the robot's current pose and covariance information.
        """
        self.current_pose = msg

        self.covariance = (
            self.current_pose.pose.covariance[0]
            * self.current_pose.pose.covariance[7]
            * self.current_pose.pose.covariance[35]
            + self.current_pose.pose.covariance[1]
            * self.current_pose.pose.covariance[11]
            * self.current_pose.pose.covariance[30]
            + self.current_pose.pose.covariance[5]
            * self.current_pose.pose.covariance[6]
            * self.current_pose.pose.covariance[31]
            - self.current_pose.pose.covariance[1]
            * self.current_pose.pose.covariance[7]
            * self.current_pose.pose.covariance[30]
            - self.current_pose.pose.covariance[1]
            * self.current_pose.pose.covariance[5]
            * self.current_pose.pose.covariance[35]
            - self.current_pose.pose.covariance[0]
            * self.current_pose.pose.covariance[11]
            * self.current_pose.pose.covariance[31]
        )

        self.data_to_save = PoseStamped()
        self.data_to_save.header = self.current_pose.header
        self.data_to_save.pose = self.current_pose.pose.pose

    def save_pose_callback(
        self, request: SavePose.Request, response: SavePose.Response
    ) -> SavePose.Response:
        """
        Callback function that handles incoming service requests to save the current pose
        to a YAML file.

        Args:
            request (SavePose.Request): The service request containing the label for the pose
                to be saved.
            response (SavePose.Response): The service response indicating the success or failure
                of the save operation.

        Returns:
            SavePose.Response: The response object containing the result of the save operation.
        """
        if self.current_pose is None:
            response.success = False
            response.message = "No pose data available to save."
            self.get_logger().warn("Attempted to save pose, but no pose data is available.")

            return response

        if self.covariance > 0.35:
            response.success = False
            response.message = "Covariance is too high to save pose."
            self.get_logger().warn(response.message)

            return response

        else:
            file_name = f"{request.label}.yaml"
            file_path = os.path.join(self.data_dir, file_name)

            try:
                with open(file_path, "w") as file:
                    file.write(message_to_yaml(self.data_to_save))

                response.success = True
                response.message = f"Pose saved successfully: {request.label}"
                self.get_logger().info(f"Incoming request: {request.label}")

                return response

            except Exception as e:
                response.success = False
                response.message = f"Error occurred while saving pose: {str(e)}"
                self.get_logger().error(response.message)

                return response


# ros2 service call /save_pose ticare_interfaces/srv/SavePose "{label: 'juan'}"


def main(args=None) -> None:
    """
    Main function that initializes the ROS node and starts spinning to process incoming messages
    and service requests.
    """
    rclpy.init(args=args)
    pose_recorder = PoseRecorder()

    try:
        rclpy.spin(pose_recorder)

    except KeyboardInterrupt:
        pass

    finally:
        pose_recorder.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
