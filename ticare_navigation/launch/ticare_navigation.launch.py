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
    map_path = "home/pal/mapa_car2.yaml"

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
            "ros2",
            "service",
            "call",
            "/map_server/load_map",
            "nav2_msgs/srv/LoadMap",
            '"{map_url: "home/pal/mapa_car2.yaml"}"',
        ],
        shell=True,
    )

    set_max_vel_x_cmd = ExecuteProcess(
        cmd=[
            "ros2",
            "param",
            "set",
            "/controller_server",
            "FollowPath.vx_max",
            "0.25",
        ],
        shell=True,
    )

    set_acc_lim_x_cmd = ExecuteProcess(
        cmd=[
            "ros2",
            "param",
            "set",
            "/mobile_base_controller",
            "linear.x.max_acceleration",
            "0.5",
        ],
        shell=True,
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        output="screen",
        arguments=["-d", rviz_config_path],
        parameters=[{"use_sim_time": LaunchConfiguration("use_sim_time")}],
    )

    return LaunchDescription(
        [
            use_sim_time,
            ticare_nodes_launch,
            load_map_service_call,
            set_max_vel_x_cmd,
            set_acc_lim_x_cmd,
            rviz,
        ]
    )
