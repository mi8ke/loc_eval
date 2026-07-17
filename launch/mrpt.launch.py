#!/usr/bin/env python3
"""mrpt_pf_localization (MRPT particle filter) + ground-truth trajectory logger.

Wires:
  mrpt_map_server (publishes our ROS occupancy grid as an MRPT metric map on
    /mrpt_map/metric_map) -> mrpt_pf_localization (SE(2) particle filter) -> traj_logger.
mrpt broadcasts map->odom, so the estimate is read from the common map->base_footprint
TF, like the other methods. Run alongside loc_eval gazebo_gt.launch.py
(after ros2 service call /reset_world).

Args: map (ROS occupancy grid yaml), run_name, out_dir, log.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg = get_package_share_directory('loc_eval')
    mrpt_map_share = get_package_share_directory('mrpt_map_server')
    mrpt_pf_share = get_package_share_directory('mrpt_pf_localization')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    map_yaml = LaunchConfiguration(
        'map', default=os.path.join(pkg, 'maps', 'turtlebot3_world.yaml'))
    pf_params = LaunchConfiguration(
        'pf_params_file', default=os.path.join(pkg, 'config', 'mrpt_pf.yaml'))
    run_name = LaunchConfiguration('run_name', default='mrpt')
    out_dir = LaunchConfiguration('out_dir', default='/tmp/loc_eval')
    log = LaunchConfiguration('log', default='true')

    # Publishes our occupancy grid as an MRPT metric map on /mrpt_map/metric_map.
    map_server = Node(
        package='mrpt_map_server', executable='map_server_node', name='map_server_node',
        output='screen',
        parameters=[{'map_yaml_file': map_yaml, 'frame_id': 'map',
                     'pub_mm_topic': 'mrpt_map', 'use_sim_time': use_sim_time}])

    pf = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(mrpt_pf_share, 'launch', 'localization.launch.py')),
        launch_arguments={
            'pf_params_file': pf_params,
            'topic_sensors_2d_scan': '/scan',
            'base_link_frame_id': 'base_footprint',
            'odom_frame_id': 'odom',
            'global_frame_id': 'map',
            'gui_enable': 'False',
        }.items())

    traj_logger = Node(
        package='loc_eval', executable='traj_logger.py', name='traj_logger',
        output='screen', condition=IfCondition(log),
        parameters=[{'use_sim_time': use_sim_time, 'gt_topic': '/ground_truth/odom',
                     'map_frame': 'map', 'base_frame': 'base_footprint',
                     'out_dir': out_dir, 'run_name': run_name}])

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('map', default_value=os.path.join(
            pkg, 'maps', 'turtlebot3_world.yaml')),
        DeclareLaunchArgument('pf_params_file', default_value=os.path.join(
            pkg, 'config', 'mrpt_pf.yaml')),
        DeclareLaunchArgument('run_name', default_value='mrpt'),
        DeclareLaunchArgument('out_dir', default_value='/tmp/loc_eval'),
        DeclareLaunchArgument('log', default_value='true'),
        map_server,
        pf,
        traj_logger,
    ])
