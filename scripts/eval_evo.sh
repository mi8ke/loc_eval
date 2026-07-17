#!/usr/bin/env bash
# Compute ATE and RPE between a ground-truth and an estimate trajectory (TUM format)
# using evo, and save numeric results + plots.
#
# Usage: eval_evo.sh <gt.tum> <est.tum> <out_dir> [label]
#
# Produces in <out_dir>:
#   <label>_ape.zip / <label>_rpe.zip   raw evo results
#   <label>_ape.txt / <label>_rpe.txt   human-readable stats (rmse/mean/std/max)
#   <label>_traj.png                    trajectory (xy) plot
#   <label>_ape.png                     APE-over-time plot
set -euo pipefail

GT="${1:?gt.tum required}"
EST="${2:?est.tum required}"
OUT="${3:?out_dir required}"
LABEL="${4:-run}"

mkdir -p "$OUT"

# Sanitize TUM inputs: drop NUL bytes / partial rows and normalize whitespace to a
# single space so evo's csv parser always sees exactly 8 fields per row. This makes
# evaluation robust even if a file was still being written when the run ended.
GTC="$OUT/${LABEL}_gt.clean.tum"
ESTC="$OUT/${LABEL}_est.clean.tum"
for pair in "$GT|$GTC" "$EST|$ESTC"; do
  src="${pair%%|*}"; dst="${pair##*|}"
  tr -d '\000' < "$src" | \
    awk 'NF==8 && $1 ~ /^[0-9]+\.?[0-9]*$/ {print $1,$2,$3,$4,$5,$6,$7,$8}' > "$dst"
done
GT="$GTC"; EST="$ESTC"

# Headless-safe plotting.
export MPLBACKEND=Agg

# t_max_diff generous because GT is 50 Hz and TF estimate is tagged with GT stamps.
TMAX=0.05

# Metrics first (must succeed), plots after (best-effort). Keeping them in separate
# evo invocations means a plotting/display failure never loses the numbers.
echo "== APE (ATE), SE(3) Umeyama alignment =="
evo_ape tum "$GT" "$EST" \
  --align --t_max_diff "$TMAX" \
  --save_results "$OUT/${LABEL}_ape.zip" \
  --no_warnings 2>&1 | tee "$OUT/${LABEL}_ape.txt"

echo "== RPE (relative, 1.0 m delta) =="
evo_rpe tum "$GT" "$EST" \
  --align --t_max_diff "$TMAX" \
  --delta 1.0 --delta_unit m \
  --save_results "$OUT/${LABEL}_rpe.zip" \
  --no_warnings 2>&1 | tee "$OUT/${LABEL}_rpe.txt"

echo "== plots (best-effort) =="
evo_ape tum "$GT" "$EST" --align --t_max_diff "$TMAX" \
  --plot_mode xy --save_plot "$OUT/${LABEL}_ape.png" --no_warnings >/dev/null 2>&1 \
  && echo "  saved ${LABEL}_ape.png" || echo "  (ape plot skipped)"
evo_traj tum "$EST" --ref "$GT" --align --t_max_diff "$TMAX" \
  --plot_mode xy --save_plot "$OUT/${LABEL}_traj.png" --no_warnings >/dev/null 2>&1 \
  && echo "  saved ${LABEL}_traj.png" || echo "  (traj plot skipped)"

echo "Done. Results in $OUT"
