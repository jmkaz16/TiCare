import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description() -> LaunchDescription:
    """
    Generates the launch description for the ticare_vision package.
    """

    use_sim_time = DeclareLaunchArgument(
        "use_sim_time",
        default_value="False",
        description="Whether or not to use simulation time for the navigation nodes.",
    )

    camera_id_arg = DeclareLaunchArgument(
        'camera_id',
        default_value='0',
        description='ID de la webcam a usar (sobrescribe el yaml)'
    )

    config_path = os.path.join(
        get_package_share_directory("ticare_vision"),
        "config",
        "vision_params.yaml"
    )


    vision_node = Node(
        package="ticare_vision",
        executable="vision_node",
        name="vision_node",
        parameters=[
            config_path, 
            {"use_sim_time": LaunchConfiguration("use_sim_time"),
            'camera_id': LaunchConfiguration('camera_id')}
        ],
        output="screen"
    )

    return LaunchDescription([use_sim_time,
        camera_id_arg,
        vision_node
    ])