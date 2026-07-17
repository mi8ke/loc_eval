#!/usr/bin/env python3
"""Cartographer 2D PURE LOCALIZATION + ground-truth trajectory logger.

Localizes against a frozen .pbstream (see cartographer_mapping.launch.py) and logs
GT + map->base_footprint TF via traj_logger -> <run>_gt.tum / <run>_est.tum for evo.
Run alongside loc_eval gazebo_gt.launch.py (after ros2 service call /reset_world).

Args: pbstream (frozen state file), run_name, out_dir, log.
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
    config_dir = os.path.join(pkg, 'config')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    pbstream = LaunchConfiguration(
        'pbstream', default=os.path.join(pkg, 'maps', 'turtlebot3_world.pbstream'))
    run_name = LaunchConfiguration('run_name', default='cartographer')
    out_dir = LaunchConfiguration('out_dir', default='/tmp/loc_eval')
    log = LaunchConfiguration('log', default='true')

    cartographer = Node(
        package='cartographer_ros',
        executable='cartographer_node',
        name='cartographer_node',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
        arguments=['-configuration_directory', config_dir,
                   '-configuration_basename', 'loc_eval_2d_localization.lua',
                   '-load_state_filename', pbstream,
                   '-load_frozen_state', 'true'])

    traj_logger = Node(
        package='loc_eval', executable='traj_logger.py', name='traj_logger',
        output='screen', condition=IfCondition(log),
        parameters=[{'use_sim_time': use_sim_time, 'gt_topic': '/ground_truth/odom',
                     # Cartographer's map->odom TF is jumpy at 5 Hz LiDAR; log the
                     # smooth /tracked_pose (PoseStamped) instead of the TF.
                     'est_topic': '/tracked_pose', 'est_topic_type': 'PoseStamped',
                     'map_frame': 'map', 'base_frame': 'base_footprint',
                     'out_dir': out_dir, 'run_name': run_name}])

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('pbstream', default_value=os.path.join(
            pkg, 'maps', 'turtlebot3_world.pbstream')),
        DeclareLaunchArgument('run_name', default_value='cartographer'),
        DeclareLaunchArgument('out_dir', default_value='/tmp/loc_eval'),
        DeclareLaunchArgument('log', default_value='true'),
        cartographer,
        traj_logger,
    ])
