cmake_minimum_required(VERSION 3.8)
project(loc_eval)

find_package(ament_cmake REQUIRED)

# Install shared resources.
install(DIRECTORY
  launch
  config
  models
  maps
  DESTINATION share/${PROJECT_NAME}
)

# Install Python nodes and helper scripts as executables.
install(PROGRAMS
  scripts/traj_logger.py
  scripts/eval_evo.sh
  scripts/record_run.sh
  scripts/run_method.sh
  scripts/run_all.sh
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
