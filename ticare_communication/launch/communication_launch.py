from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument


def generate_launch_description():

    use_sim_time = DeclareLaunchArgument(
        "use_sim_time",
        default_value="True",
        description="Whether or not to use simulation time for the communication nodes.",
    )

    capture_audio_node = Node(
        package="audio_capture",
        executable="audio_capture_node",
        output="screen",
        parameters=[{"format": "wave", "use_sim_time": LaunchConfiguration("use_sim_time")}],
    )

    communication_node = Node(
        package="ticare_communication",
        executable="state_manager",
        output="screen",
        parameters=[{"use_sim_time": LaunchConfiguration("use_sim_time")}],
    )

    return LaunchDescription([use_sim_time, capture_audio_node, communication_node])
