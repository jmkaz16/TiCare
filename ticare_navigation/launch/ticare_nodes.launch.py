from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():

    use_sim_time = DeclareLaunchArgument(
        "use_sim_time",
        default_value="True",
        description="Whether or not to use simulation time for the navigation nodes.",
    )

    navigation_manager_node = Node(
        package="ticare_navigation",
        executable="nav_manager",
        output="screen",
        parameters=[
            {
                "use_sim_time": LaunchConfiguration("use_sim_time"),
                "recovery_rotation_duration": 30.0,
                "recovery_rotation_speed": 0.5,
                "search_duration": 300.0,
            }
        ],
    )

    pose_recorder_node = Node(
        package="ticare_navigation",
        executable="pose_recorder",
        output="screen",
        parameters=[
            {
                "use_sim_time": LaunchConfiguration("use_sim_time"),
                "position_error_threshold": 0.5,
                "orientation_error_threshold": 0.25,
            }
        ],
    )

    return LaunchDescription([use_sim_time, navigation_manager_node, pose_recorder_node])
