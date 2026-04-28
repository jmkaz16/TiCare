import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import RegisterEventHandler, ExecuteProcess
from launch.event_handlers import OnProcessStart, OnProcessExit


def generate_launch_description():
    """
    Generates a ROS 2 launch description to bring up the map_server and AMCL.

    This launch file performs the following steps in sequence:
    1. Starts the nav2_map_server and nav2_amcl nodes with their respective parameter files.
    2. Once map_server starts, it triggers the lifecycle transition for 'map_server'.
    3. Once the map_server transition finishes, it triggers the lifecycle transition for 'amcl'.

    Returns:
        LaunchDescription: The ROS 2 launch description object.
    """

    ticare_nav_dir = get_package_share_directory("ticare_navigation")
    map_config_path = os.path.join(ticare_nav_dir, "maps", "final_map.yaml")
    amcl_config_path = os.path.join(ticare_nav_dir, "data", "my_amcl_params.yaml")

    map_server_node = Node(
        package="nav2_map_server",
        executable="map_server",
        name="map_server",
        output="screen",
        parameters=[{"yaml_filename": map_config_path, "use_sim_time": True}],
    )

    amcl_node = Node(
        package="nav2_amcl",
        executable="amcl",
        name="amcl",
        output="screen",
        parameters=[amcl_config_path, {"use_sim_time": True}],
    )

    bringup_map_server_cmd = ExecuteProcess(
        cmd=["ros2", "run", "nav2_util", "lifecycle_bringup", "map_server"], output="screen"
    )

    bringup_amcl_cmd = ExecuteProcess(
        cmd=["ros2", "run", "nav2_util", "lifecycle_bringup", "amcl"], output="screen"
    )

    start_bringup_map_server_event = RegisterEventHandler(
        event_handler=OnProcessStart(
            target_action=map_server_node, on_start=[bringup_map_server_cmd]
        )
    )

    start_bringup_amcl_event = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=bringup_map_server_cmd, on_exit=[bringup_amcl_cmd]
        )
    )

    return LaunchDescription(
        [map_server_node, amcl_node, start_bringup_map_server_event, start_bringup_amcl_event]
    )
