from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    ticare_navigation_dir = PathJoinSubstitution([FindPackageShare("ticare_navigation"), "launch"])

    ticare_sim_launch = IncludeLaunchDescription(
        PathJoinSubstitution([ticare_navigation_dir, "ticare_sim.launch.py"]),
    )

    ticare_nodes_launch = IncludeLaunchDescription(
        PathJoinSubstitution([ticare_navigation_dir, "ticare_nodes.launch.py"]),
    )

    return LaunchDescription([ticare_sim_launch, ticare_nodes_launch])
