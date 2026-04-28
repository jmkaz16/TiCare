import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description() -> LaunchDescription:
    """
    Generates the launch description for the ticare_vision package.
    
    Returns:
        LaunchDescription: The ROS 2 launch description object.
    """
    config_path = os.path.join(
        get_package_share_directory("ticare_vision"),
        "config",
        "vision_params.yaml"
    )

    vision_node = Node(
        package="ticare_vision",
        executable="vision_node",
        name="vision_node",
        parameters=[config_path],
        output="screen"
    )

    return LaunchDescription([vision_node])