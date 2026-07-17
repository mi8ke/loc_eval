#!/usr/bin/env bash
# Source ROS 2 + the loc_eval overlay for every shell / command in the container.
set -e
source /opt/ros/humble/setup.bash
source /ros2_ws/install/setup.bash
export TURTLEBOT3_MODEL="${TURTLEBOT3_MODEL:-burger}"
export PATH="$HOME/.local/bin:$PATH"
exec "$@"
