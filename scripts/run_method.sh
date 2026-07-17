#!/usr/bin/env bash
# Reproducible single evaluation run for one localization method.
#
# Assumes loc_eval gazebo_gt.launch.py is ALREADY running (gzserver + GT).
# Sequence: reset_world (robot -> spawn) -> launch method+logger in its own process
# group -> wait for init/convergence -> play the STANDARD trajectory -> stop ->
# eval_evo -> kill the whole method process group (setsid group kill).
#
# Usage: run_method.sh <launch_file> <run_name> <out_dir> [init_wait_s] [drive_s]
# Prints one CSV line: <run_name>,<ate_rmse>,<rpe_rmse>
# NOTE: no `set -u` -- ROS setup.bash references unbound vars (AMENT_TRACE_SETUP_FILES).
set -o pipefail

LAUNCH="${1:?launch file, e.g. amcl.launch.py}"
RUN="${2:?run_name}"
OUT="${3:?out_dir}"
INIT="${4:-15}"
DRIVE="${5:-28}"

# Workspace overlay: override with LOC_EVAL_WS for other layouts (e.g. Docker /ros2_ws).
LOC_EVAL_WS="${LOC_EVAL_WS:-/home/miyake/ros2_ws}"
source /opt/ros/humble/setup.bash
source "${LOC_EVAL_WS}/install/setup.bash"
export PATH="$HOME/.local/bin:$PATH"
mkdir -p "$OUT"

# 1) reset robot to the known spawn pose (fixed initial pose of every localizer)
ros2 service call /reset_world std_srvs/srv/Empty >/dev/null 2>&1
sleep 2

# 2) launch the method in a fresh session (setsid) so the whole tree shares one PGID
setsid ros2 launch loc_eval "$LAUNCH" out_dir:="$OUT" run_name:="$RUN" \
    > "$OUT/${RUN}_launch.log" 2>&1 &
LPID=$!             # session/group leader PID == PGID
sleep "$INIT"

# 3) standard trajectory (identical for every run) then stop
timeout "$DRIVE" ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist \
    "{linear: {x: 0.15}, angular: {z: 0.35}}" >/dev/null 2>&1
ros2 topic pub -t 5 /cmd_vel geometry_msgs/msg/Twist "{}" >/dev/null 2>&1
sleep 1

# 4) stop the method group gracefully then forcibly (flushes logger, frees frames)
kill -INT -"$LPID" 2>/dev/null
sleep 3
kill -KILL -"$LPID" 2>/dev/null
sleep 2

# 5) evaluate (eval_evo.sh is installed as a loc_eval executable -> location-independent)
ros2 run loc_eval eval_evo.sh \
    "$OUT/${RUN}_gt.tum" "$OUT/${RUN}_est.tum" "$OUT" "$RUN" >/dev/null 2>&1

ate=$(awk '/rmse/{print $2; exit}' "$OUT/${RUN}_ape.txt" 2>/dev/null)
rpe=$(awk '/rmse/{print $2; exit}' "$OUT/${RUN}_rpe.txt" 2>/dev/null)
echo "${RUN},${ate:-NA},${rpe:-NA}"
