from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    tiago_dir = PathJoinSubstitution([FindPackageShare("tiago_gazebo"), "launch"])

    world_path = PathJoinSubstitution(
        [FindPackageShare("ticare_navigation"), "worlds", "car_shifted_final"]
    )

    tiago_gazebo_launch = IncludeLaunchDescription(
        PathJoinSubstitution([tiago_dir, "tiago_gazebo.launch.py"]),
        launch_arguments={
            "world_name": world_path,
            "slam": "True",
            "arm_type": "no-arm",
            "navigation": "True",
            "is_public_sim": "True",
        }.items(),
    )

    return LaunchDescription([tiago_gazebo_launch])


# Possible arguments to pass to the launch file:
#
# 'base_type':
#     Base type. Valid choices are: ['pmb2', 'omni_base']
#     (default: 'pmb2')

# 'has_screen':
#     Has screen at torso. Valid choices are: ['False', 'True']
#     (default: 'False')

# 'arm_type':
#     Arm type. Valid choices are: ['tiago-arm', 'no-arm']
#     (default: 'tiago-arm')

# 'arm_motor_model':
#     Arm motor model. Valid choices are: ['parker', 'ilm']
#     (default: 'parker')

# 'end_effector':
#     End effector model. Valid choices are: ['pal-gripper', 'pal-hey5', 'custom', 'no-end-effector', 'robotiq-2f-85', 'robotiq-2f-140']
#     (default: 'pal-gripper')

# 'ft_sensor':
#     FT sensor model. Valid choices are: ['schunk-ft', 'no-ft-sensor']
#     (default: 'schunk-ft')

# 'wrist_model':
#     Wrist model. Valid choices are: ['wrist-2010', 'wrist-2017']
#     (default: 'wrist-2017')

# 'camera_model':
#     Head camera model. Valid choices are: ['orbbec-astra', 'orbbec-astra-pro', 'asus-xtion', 'no-camera']
#     (default: 'orbbec-astra')

# 'laser_model':
#     Base laser model. Valid choices are: ['no-laser', 'sick-571', 'sick-561', 'sick-551', 'hokuyo']
#     (default: 'sick-571')

# 'navigation':
#     Specify if launching Navigation2. Valid choices are: ['True', 'False']
#     (default: 'False')

# 'advanced_navigation':
#     Specify if launching Advanced Navigation. Valid choices are: ['True', 'False']
#     (default: 'False')

# 'slam':
#     Whether or not you are using SLAM
#     (default: 'False')

# 'docking':
#     Specify if launching Docking. Valid choices are: ['True', 'False']
#     (default: 'False')

# 'moveit':
#     Specify if launching MoveIt 2. Valid choices are: ['True', 'False']
#     (default: 'True')

# 'world_name':
#     Specify world name, will be converted to full path.
#     (default: 'pal_office')

# 'namespace':
#     Define namespace of the robot.
#     (default: '')

# 'tuck_arm':
#     Launches tuck arm node. Valid choices are: ['True', 'False']
#     (default: 'True')

# 'is_public_sim':
#     Enable public simulation. Valid choices are: ['True', 'False']
#     (default: 'False')

# 'rviz':
#     Launch RViz client. Valid choices are: ['True', 'False']
#     (default: 'True')

# 'gzclient':
#     Whether to launch gzclient (the Gazebo GUI). Valid choices are: ['True', 'False']
#     (default: 'True')

# 'gazebo_version':
#     Version of Gazebo to be used, 'classic' or 'gazebo'. Valid choices are: ['gazebo', 'classic']
#     (default: 'classic')
