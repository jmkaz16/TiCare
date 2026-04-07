from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    bittle_action_node = Node(package="bittle_actions", executable="command", output="screen")

    bittle_communication_node = Node(
        package="bittle_communication", executable="communication_publisher", output="screen"
    )

    return LaunchDescription([bittle_action_node, bittle_communication_node])
