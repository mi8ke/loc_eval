#!/usr/bin/env bash
# Source ROS 2 + the loc_eval overlay + Gazebo for every command in the container.
set -e
source /opt/ros/humble/setup.bash
source /ros2_ws/install/setup.bash
# Gazebo Classic env: puts /usr/share/gazebo-11/models on GAZEBO_MODEL_PATH so the
# base models (sun, ground_plane) resolve locally. Without this, Gazebo falls back to
# the online model database and gzserver hangs/dies (exit 255) in an offline container.
[ -f /usr/share/gazebo/setup.sh ] && source /usr/share/gazebo/setup.sh
# Never fetch models over the network — everything the benchmark needs is local.
export GAZEBO_MODEL_DATABASE_URI=""
export TURTLEBOT3_MODEL="${TURTLEBOT3_MODEL:-burger}"
export PATH="$HOME/.local/bin:$PATH"
exec "$@"
