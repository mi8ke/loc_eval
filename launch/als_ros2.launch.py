#!/usr/bin/env python3
"""als_ros2 (Naoki Akai / iASL-Gifu reliable MCL) localization + ground-truth logger.

Runs the als_ros2 `mcl` node against the shared loc_eval map and TurtleBot3 frames
(base_footprint / base_scan), plus nav2_map_server and traj_logger, so a run produces
the same <run>_gt.tum / <run>_est.tum as the AMCL setup. mcl broadcasts map->odom
(broadcast_tf=true), so the estimate is read from the common map->base_footprint TF.

Run alongside loc_eval gazebo_gt.launch.py.

Args: map, run_name, out_dir, log, use_mrf_failure_detector (default false),
      initial x/y/yaw (default match turtlebot3_world spawn -2.0,-0.5,0).
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg = get_package_share_directory('loc_eval')
    als_share = get_package_share_directory('als_ros2')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    map_yaml = LaunchConfiguration(
        'map', default=os.path.join(pkg, 'maps', 'turtlebot3_world.yaml'))
    run_name = LaunchConfiguration('run_name', default='als_ros2')
    out_dir = LaunchConfiguration('out_dir', default='/tmp/loc_eval')
    log = LaunchConfiguration('log', default='true')

    mcl_yaml = os.path.join(als_share, 'config', 'mcl.yaml')

    # mcl.yaml hardcodes the original author's absolute path for the reliability
    # classifier; point it at the classifier shipped in the als_ros2 source tree.
    # (This only feeds reliability estimation; pose tracking / ATE is unaffected.)
    # Override LOC_EVAL_ALS_SRC for other layouts (e.g. Docker /ros2_ws/src/als_ros2/als_ros2).
    als_src = os.environ.get(
        'LOC_EVAL_ALS_SRC', '/home/miyake/ros2_ws/src/als_ros2/als_ros2')
    mae_classifier_dir = os.path.join(als_src, 'classifiers', 'MAE', 'gifu_univ_7th') + '/'

    # GraphicsMagick libs live in /usr/lib/bak_magick on this machine; restore on
    # LD_LIBRARY_PATH for map_server only (see graphicsmagick note).
    map_server_env = {'LD_LIBRARY_PATH':
                      '/usr/lib/bak_magick:' + os.environ.get('LD_LIBRARY_PATH', '')}

    map_server = Node(
        package='nav2_map_server', executable='map_server', name='map_server',
        output='screen', additional_env=map_server_env,
        parameters=[{'use_sim_time': use_sim_time, 'yaml_filename': map_yaml,
                     'topic_name': 'map', 'frame_id': 'map'}])

    lifecycle = Node(
        package='nav2_lifecycle_manager', executable='lifecycle_manager',
        name='lifecycle_manager_localization', output='screen',
        parameters=[{'use_sim_time': use_sim_time, 'autostart': True,
                     'node_names': ['map_server']}])

    # mcl subscribes to /map with VOLATILE QoS, while nav2 map_server latches
    # (transient_local) and publishes once on activation. Start mcl FIRST so it is
    # subscribed before map_server activates and thus receives the single map message.
    mcl = Node(
        package='als_ros2', executable='mcl', name='mcl', output='screen',
        parameters=[mcl_yaml, {
            'use_sim_time': use_sim_time,
            'map_name': '/map',
            'scan_name': '/scan',
            'odom_name': '/odom',
            'map_frame': 'map',
            'odom_frame': 'odom',
            'base_link_frame': 'base_footprint',
            'laser_frame': 'base_scan',
            'broadcast_tf': True,
            'use_odom_tf': False,
            # Keep the map->odom TF valid between MCL updates so the ground-truth
            # logger samples the estimate at full rate (mcl.yaml ships 0.0, which
            # makes the transform expire immediately and yields a sparse estimate).
            'transform_tolerance': 1.0,
            'mae_classifier_dir': mae_classifier_dir,
            'initial_pose_x': LaunchConfiguration('initial_pose_x', default='-2.0'),
            'initial_pose_y': LaunchConfiguration('initial_pose_y', default='-0.5'),
            'initial_pose_yaw': LaunchConfiguration('initial_pose_yaw', default='0.0'),
        }])

    # Delay map bringup a moment so mcl's /map subscription exists first.
    delayed_map = TimerAction(period=3.0, actions=[map_server, lifecycle])

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
        DeclareLaunchArgument('run_name', default_value='als_ros2'),
        DeclareLaunchArgument('out_dir', default_value='/tmp/loc_eval'),
        DeclareLaunchArgument('log', default_value='true'),
        DeclareLaunchArgument('initial_pose_x', default_value='-2.0'),
        DeclareLaunchArgument('initial_pose_y', default_value='-0.5'),
        DeclareLaunchArgument('initial_pose_yaw', default_value='0.0'),
        mcl,
        delayed_map,
        traj_logger,
    ])
