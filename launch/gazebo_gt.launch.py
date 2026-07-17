#!/usr/bin/env python3
"""Bring up Gazebo with a TurtleBot3 Burger that also publishes ground-truth pose.

Spawns the loc_eval `turtlebot3_burger_gt` model (stock burger + P3D plugin ->
/ground_truth/odom) into a selectable TurtleBot3 world, plus robot_state_publisher
for the static sensor TFs. This is the shared simulation base every localization
method is evaluated against.

Args:
  world     : turtlebot3_world (default) | turtlebot3_house | <abs path to .world>
  x_pose,y_pose : spawn pose (defaults match turtlebot3_world.launch.py)
  use_sim_time  : true (default)
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (AppendEnvironmentVariable, DeclareLaunchArgument,
                            IncludeLaunchDescription, SetEnvironmentVariable)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def generate_launch_description():
    pkg_tb3_gazebo = get_package_share_directory('turtlebot3_gazebo')
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')
    pkg_loc_eval = get_package_share_directory('loc_eval')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    x_pose = LaunchConfiguration('x_pose', default='-2.0')
    y_pose = LaunchConfiguration('y_pose', default='-0.5')
    world_name = LaunchConfiguration('world', default='turtlebot3_world')
    gui = LaunchConfiguration('gui', default='true')

    # Resolve a bare world name to turtlebot3_gazebo/worlds/<name>.world; an absolute
    # path (starts with '/') is used verbatim.
    world_path = PythonExpression([
        "'", world_name, "' if '", world_name, "'.startswith('/') else '",
        os.path.join(pkg_tb3_gazebo, 'worlds'), "' + '/' + '", world_name, "' + '.world'"
    ])

    gt_model = os.path.join(
        pkg_loc_eval, 'models', 'turtlebot3_burger_gt', 'model.sdf')

    # turtlebot3_common meshes (model:// URIs) and our GT model must be on the path.
    set_tb3_model = SetEnvironmentVariable('TURTLEBOT3_MODEL', 'burger')
    add_model_path = AppendEnvironmentVariable(
        'GAZEBO_MODEL_PATH',
        os.path.join(pkg_tb3_gazebo, 'models') + ':' +
        os.path.join(pkg_loc_eval, 'models'))

    gzserver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gzserver.launch.py')),
        launch_arguments={'world': world_path}.items())

    gzclient = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gzclient.launch.py')),
        condition=IfCondition(gui))

    robot_state_publisher = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_tb3_gazebo, 'launch', 'robot_state_publisher.launch.py')),
        launch_arguments={'use_sim_time': use_sim_time}.items())

    spawn = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-entity', 'turtlebot3_burger', '-file', gt_model,
                   '-x', x_pose, '-y', y_pose, '-z', '0.01'],
        output='screen')

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('world', default_value='turtlebot3_world'),
        DeclareLaunchArgument('x_pose', default_value='-2.0'),
        DeclareLaunchArgument('y_pose', default_value='-0.5'),
        DeclareLaunchArgument('gui', default_value='true'),
        set_tb3_model,
        add_model_path,
        gzserver,
        gzclient,
        robot_state_publisher,
        spawn,
    ])
