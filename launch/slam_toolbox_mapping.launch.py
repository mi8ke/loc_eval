#!/usr/bin/env python3
"""slam_toolbox online-async MAPPING run (one-off) to build a serialized pose graph.

Drive the robot around the world while this runs, then serialize the map:
  ros2 service call /slam_toolbox/serialize_map slam_toolbox/srv/SerializePoseGraph \
    "{filename: <ws>/src/loc_eval/maps/turtlebot3_world_stb}"   # then rebuild loc_eval
That produces turtlebot3_world_stb.posegraph (+ .data), used by slam_toolbox.launch.py.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg = get_package_share_directory('loc_eval')
    params = LaunchConfiguration(
        'params_file',
        default=os.path.join(pkg, 'config', 'slam_toolbox_mapping.yaml'))

    slam = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[params, {'use_sim_time': True}])

    return LaunchDescription([
        DeclareLaunchArgument('params_file', default_value=os.path.join(
            pkg, 'config', 'slam_toolbox_mapping.yaml')),
        slam,
    ])
