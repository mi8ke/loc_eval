#!/usr/bin/env python3
"""slam_toolbox LOCALIZATION mode + ground-truth trajectory logger.

Localizes against a pre-built serialized pose graph (see slam_toolbox_mapping.launch.py)
and logs GT + map->base_footprint TF via traj_logger, producing <run>_gt.tum /
<run>_est.tum for evo. Run alongside loc_eval gazebo_gt.launch.py.

Args: map_file (serialized posegraph basename, no extension), run_name, out_dir, log.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg = get_package_share_directory('loc_eval')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    params = LaunchConfiguration(
        'params_file',
        default=os.path.join(pkg, 'config', 'slam_toolbox_localization.yaml'))
    map_file = LaunchConfiguration(
        'map_file', default=os.path.join(pkg, 'maps', 'turtlebot3_world_stb'))
    run_name = LaunchConfiguration('run_name', default='slam_toolbox')
    out_dir = LaunchConfiguration('out_dir', default='/tmp/loc_eval')
    log = LaunchConfiguration('log', default='true')

    slam = Node(
        package='slam_toolbox',
        executable='localization_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[params, {'use_sim_time': use_sim_time,
                             'map_file_name': map_file}])

    traj_logger = Node(
        package='loc_eval', executable='traj_logger.py', name='traj_logger',
        output='screen', condition=IfCondition(log),
        parameters=[{'use_sim_time': use_sim_time, 'gt_topic': '/ground_truth/odom',
                     'map_frame': 'map', 'base_frame': 'base_footprint',
                     'out_dir': out_dir, 'run_name': run_name}])

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('params_file', default_value=os.path.join(
            pkg, 'config', 'slam_toolbox_localization.yaml')),
        DeclareLaunchArgument('map_file', default_value=os.path.join(
            pkg, 'maps', 'turtlebot3_world_stb')),
        DeclareLaunchArgument('run_name', default_value='slam_toolbox'),
        DeclareLaunchArgument('out_dir', default_value='/tmp/loc_eval'),
        DeclareLaunchArgument('log', default_value='true'),
        slam,
        traj_logger,
    ])
