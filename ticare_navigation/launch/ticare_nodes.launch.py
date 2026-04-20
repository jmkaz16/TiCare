from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    navigation_manager_node = Node(package="ticare_navigation", executable="navigation_manager", output="screen")

    pose_recorder_node = Node(package="ticare_navigation", executable="pose_recorder", output="screen")

    return LaunchDescription([navigation_manager_node, pose_recorder_node])
