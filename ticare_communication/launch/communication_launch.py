from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    capture_audio_node = Node(
        package="audio_capture",
        executable="audio_capture_node",
        output="screen",
        parameters=[{"format": "wave"}],
    )

    communication_node = Node(
        package="ticare_communication",
        executable="state_manager",
        output="screen",
    )

    return LaunchDescription([capture_audio_node, communication_node])
