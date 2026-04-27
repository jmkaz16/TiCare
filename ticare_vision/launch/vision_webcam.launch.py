from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    package_dir = get_package_share_directory('tiare_vision')
    params_file = os.path.join(package_dir, 'config', 'vision_params_webcam.yaml')

    return LaunchDescription([
        Node(
            package='tiare_vision',
            executable='object_detector',
            name='object_detector_node',
            output='screen',
            parameters=[params_file]
        )
    ])