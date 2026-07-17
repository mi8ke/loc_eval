#!/usr/bin/env bash
# Record a rosbag of the key evaluation topics for one run (reproducibility backup).
# The primary metric input (TUM files) comes from traj_logger; this bag lets a run
# be replayed / re-analyzed later.
#
# Usage: record_run.sh <out_dir> <run_name> [duration_sec]
#   duration_sec: if given, recording stops automatically after N seconds.
set -euo pipefail

OUT="${1:?out_dir required}"
RUN="${2:?run_name required}"
DUR="${3:-}"

mkdir -p "$OUT"
BAG="$OUT/${RUN}_bag"

TOPICS=(/tf /tf_static /ground_truth/odom /scan /odom /cmd_vel /clock \
        /amcl_pose /particle_cloud /pose)

echo "Recording to $BAG ..."
if [[ -n "$DUR" ]]; then
  timeout "$DUR" ros2 bag record -o "$BAG" "${TOPICS[@]}" || true
else
  echo "(Ctrl-C to stop)"
  ros2 bag record -o "$BAG" "${TOPICS[@]}"
fi
echo "Saved $BAG"
