from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.actions import ExecuteProcess
from launch.actions import IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    ticare_navigation_dir = PathJoinSubstitution([FindPackageShare("ticare_navigation"), "launch"])
    rviz_config_path = PathJoinSubstitution(
        [FindPackageShare("ticare_navigation"), "rviz", "rviz_ticare_config.rviz"]
    )
    map_path = PathJoinSubstitution("home/pal/mapa_car2.yaml")

    use_sim_time = DeclareLaunchArgument(
        "use_sim_time",
        default_value="False",
        description="Whether or not to use simulation time for the navigation nodes.",
    )

    ticare_nodes_launch = IncludeLaunchDescription(
        PathJoinSubstitution([ticare_navigation_dir, "ticare_nodes.launch.py"]),
        launch_arguments={"use_sim_time": LaunchConfiguration("use_sim_time")}.items(),
    )

    load_map_service_call = ExecuteProcess(
    cmd=[
        'ros2', 'service', 'call', 
        '/map_server/load_map', 
        'nav2_msgs/srv/LoadMap', 
        f'{{map_url: "{map_path}"}}'
    ],
    shell=True
)

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        output="screen",
        arguments=["-d", rviz_config_path],
        parameters=[{"use_sim_time": LaunchConfiguration("use_sim_time")}],
    )

    return LaunchDescription([use_sim_time, ticare_nodes_launch, load_map_service_call, rviz])
  