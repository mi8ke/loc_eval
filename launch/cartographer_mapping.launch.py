#!/usr/bin/env python3
"""Cartographer 2D MAPPING run (one-off) to produce a frozen .pbstream.

Drive the robot around the world while this runs, then save the state:
  ros2 service call /finish_trajectory cartographer_ros_msgs/srv/FinishTrajectory \
    "{trajectory_id: 0}"
  ros2 service call /write_state cartographer_ros_msgs/srv/WriteState \
    "{filename: '$(ros2 pkg prefix loc_eval)/share/loc_eval/maps/turtlebot3_world.pbstream', include_unfinished_submaps: false}"
  (or save into the source tree: <ws>/src/loc_eval/maps/turtlebot3_world.pbstream, then rebuild)
The .pbstream is then used by cartographer.launch.py (pure localization).
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    pkg = get_package_share_directory('loc_eval')
    config_dir = os.path.join(pkg, 'config')

    cartographer = Node(
        package='cartographer_ros',
        executable='cartographer_node',
        name='cartographer_node',
        output='screen',
        parameters=[{'use_sim_time': True}],
        arguments=['-configuration_directory', config_dir,
                   '-configuration_basename', 'loc_eval_2d.lua'])

    return LaunchDescription([cartographer])
