#!/usr/bin/env bash
# Run every localization method for N trials and collect ATE/RPE into a CSV.
# Requires loc_eval gazebo_gt.launch.py already running.
#
# Usage: run_all.sh <out_dir> [trials]
set -o pipefail

OUT="${1:?out_dir}"
TRIALS="${2:-3}"
mkdir -p "$OUT"

SELF="$(cd "$(dirname "$0")" && pwd)/run_method.sh"
CSV="$OUT/summary.csv"
echo "method,trial,ate_rmse_m,rpe_rmse_m" > "$CSV"

# method:launch_file:init_wait  (cartographer/mrpt need a longer convergence wait)
METHODS=(
  "amcl:amcl.launch.py:14"
  "als_ros2:als_ros2.launch.py:15"
  "slam_toolbox:slam_toolbox.launch.py:14"
  "cartographer:cartographer.launch.py:16"
  "mrpt:mrpt.launch.py:16"
)

for spec in "${METHODS[@]}"; do
  name="${spec%%:*}"; rest="${spec#*:}"; launch="${rest%%:*}"; init="${rest##*:}"
  for t in $(seq 1 "$TRIALS"); do
    run="${name}_t${t}"
    echo ">>> $run"
    line=$(bash "$SELF" "$launch" "$run" "$OUT" "$init" 28)
    ate=$(echo "$line" | cut -d, -f2); rpe=$(echo "$line" | cut -d, -f3)
    echo "${name},${t},${ate},${rpe}" >> "$CSV"
    echo "    -> ATE=${ate}  RPE=${rpe}"
  done
done

echo "=== summary ==="
cat "$CSV"
