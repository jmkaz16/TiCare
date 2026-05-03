from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="ticare_communication",
                executable="state_manager",
                name="state_manager",
                output="screen",
                emulate_tty=True,
            )
        ]
    )
