import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    """
    Launches the AMCL node along with the map server and lifecycle manager for localization.
    """

    pkg_dir = get_package_share_directory('ticare_navigation')
    
    map_file = os.path.join(pkg_dir, 'maps', 'final_map.yaml')
    amcl_yaml = os.path.join(pkg_dir, 'data', 'my_amcl_params.yaml')
    
    remappings = [('/tf', 'tf'),
                  ('/tf_static', 'tf_static')]

    return LaunchDescription([
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output='screen',
            remappings=remappings,
            parameters=[{'use_sim_time': True}, 
                        {'yaml_filename':map_file}]
        ),
            
        Node(
            package='nav2_amcl',
            executable='amcl',
            name='amcl',
            output='screen',
            remappings=remappings,
            parameters=[amcl_yaml, {'use_sim_time': True}]
        ),

        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_localization',
            output='screen',
            parameters=[{'use_sim_time': True},
                        {'autostart': True},
                        {'node_names': ['map_server', 'amcl']}]
        )
    ])
