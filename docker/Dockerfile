# 2D LiDAR localization benchmark (loc_eval) — reproducible environment.
# ROS 2 Humble + Gazebo Classic + TurtleBot3 + the 5 evaluated localization methods.
#
# Build (from the loc_eval package root):
#   docker build -f docker/Dockerfile -t loc_eval:humble .
FROM ros:humble-ros-base

ENV DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-lc"]

# --- System + ROS dependencies --------------------------------------------------
# gazebo_ros_pkgs   : Gazebo Classic + P3D ground-truth plugin
# turtlebot3-*      : robot model, worlds, robot_state_publisher launch
# nav2-*            : AMCL, map_server, lifecycle_manager
# cartographer/slam_toolbox/mrpt-* : the other evaluated methods
RUN apt-get update && apt-get install -y --no-install-recommends \
      git \
      python3-pip \
      python3-colcon-common-extensions \
      ros-humble-gazebo-ros-pkgs \
      ros-humble-turtlebot3-gazebo \
      ros-humble-turtlebot3-description \
      ros-humble-nav2-amcl \
      ros-humble-nav2-map-server \
      ros-humble-nav2-lifecycle-manager \
      ros-humble-cartographer-ros \
      ros-humble-slam-toolbox \
      ros-humble-mrpt-pf-localization \
      ros-humble-mrpt-map-server \
      ros-humble-rviz2 \
    && rm -rf /var/lib/apt/lists/*

# --- evo (with a numpy-2-compatible scipy) --------------------------------------
RUN pip3 install --no-cache-dir evo "scipy>=1.13"

# --- Workspace ------------------------------------------------------------------
ENV ROS_WS=/ros2_ws \
    LOC_EVAL_WS=/ros2_ws \
    LOC_EVAL_ALS_SRC=/ros2_ws/src/als_ros2/als_ros2 \
    TURTLEBOT3_MODEL=burger

WORKDIR ${ROS_WS}/src

# als_ros2 (source; ament). Pin a commit here for byte-reproducibility if desired.
RUN git clone --depth 1 https://github.com/iASL-Gifu/als_ros2.git

# loc_eval package (this repo). .dockerignore keeps results/ and .git out.
COPY . ${ROS_WS}/src/loc_eval

# Build only the two source packages; everything else is from apt.
WORKDIR ${ROS_WS}
RUN source /opt/ros/humble/setup.bash \
    && colcon build --packages-select als_ros2 loc_eval

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
