#!/usr/bin/env python3
"""AMCL (nav2_amcl) localization + ground-truth trajectory logger.

Brings up nav2_map_server + nav2_amcl (lifecycle-managed) against the shared map,
and starts loc_eval's traj_logger so a run directly produces <run>_gt.tum /
<run>_est.tum for evo. Run this alongside loc_eval gazebo_gt.launch.py.

Args:
  map        : map yaml (default: loc_eval turtlebot3_world.yaml)
  params_file: amcl params (default: loc_eval config/amcl.yaml)
  run_name   : output basename (default: amcl)
  out_dir    : TUM output dir (default: /tmp/loc_eval)
  log        : start traj_logger (default: true)
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
    map_yaml = LaunchConfiguration(
        'map', default=os.path.join(pkg, 'maps', 'turtlebot3_world.yaml'))
    params_file = LaunchConfiguration(
        'params_file', default=os.path.join(pkg, 'config', 'amcl.yaml'))
    run_name = LaunchConfiguration('run_name', default='amcl')
    out_dir = LaunchConfiguration('out_dir', default='/tmp/loc_eval')
    log = LaunchConfiguration('log', default='true')

    # This machine has GraphicsMagick libs moved out of /usr/lib into
    # /usr/lib/bak_magick, so nav2_map_server can't find libGraphicsMagick++-Q16.so.12.
    # Restore it on LD_LIBRARY_PATH for the map_server process only (no system change).
    map_server_env = {'LD_LIBRARY_PATH':
                      '/usr/lib/bak_magick:' + os.environ.get('LD_LIBRARY_PATH', '')}

    map_server = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        additional_env=map_server_env,
        parameters=[{'use_sim_time': use_sim_time,
                     'yaml_filename': map_yaml,
                     'topic_name': 'map',
                     'frame_id': 'map'}])

    amcl = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        output='screen',
        parameters=[params_file])

    lifecycle = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_localization',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time,
                     'autostart': True,
                     'node_names': ['map_server', 'amcl']}])

    traj_logger = Node(
        package='loc_eval',
        executable='traj_logger.py',
        name='traj_logger',
        output='screen',
        condition=IfCondition(log),
        parameters=[{'use_sim_time': use_sim_time,
                     'gt_topic': '/ground_truth/odom',
                     'map_frame': 'map',
                     'base_frame': 'base_footprint',
                     'out_dir': out_dir,
                     'run_name': run_name}])

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('map', default_value=os.path.join(
            pkg, 'maps', 'turtlebot3_world.yaml')),
        DeclareLaunchArgument('params_file', default_value=os.path.join(
            pkg, 'config', 'amcl.yaml')),
        DeclareLaunchArgument('run_name', default_value='amcl'),
        DeclareLaunchArgument('out_dir', default_value='/tmp/loc_eval'),
        DeclareLaunchArgument('log', default_value='true'),
        map_server,
        amcl,
        lifecycle,
        traj_logger,
    ])
