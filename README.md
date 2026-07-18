# loc_eval — 2D LiDAR Localization Benchmark (Gazebo / TurtleBot3)

同一の地図・走行・真値のもとで、**5つの2D自己位置推定手法**を Gazebo Classic 上で
定量比較する ROS 2 パッケージ。真値は物理エンジンの実ポーズ（P3D プラグイン）、指標は
**evo** の ATE / RPE（SE(3) Umeyama 整列）。**Docker で環境一式を再現できます。**

## 結果（`turtlebot3_world`・28秒周回・3試行、ATE/RPE RMSE）

| # | 手法 | 方式 | License | ATE (mm) | RPE (mm) |
|---|---|---|---|---:|---:|
| 1 | **slam_toolbox** | スキャンマッチ (localization) | LGPL-2.1 | 7.5 ± 0.7 | 5.6 ± 0.2 |
| 2 | **als_ros2** | Reliable MCL (RBPF) | Apache-2.0 | 8.2 ± 0.2 | 4.7 ± 0.4 |
| 3 | **Cartographer** | グラフ最適化 (pure loc) | Apache-2.0 | 10.5 ± 1.0 | 2.9 ± 1.0 |
| 4 | **AMCL** (nav2) | Adaptive MCL (KLD) | Apache/LGPL | 16.3 ± 5.0 | 25.3 ± 2.1 |
| 5 | **mrpt_pf_localization** | Particle Filter (SE2) | BSD 3-Clause | 181.9 ± 92.1 | 465.6 ± 302.9 |

生データ: [`results/phaseC/summary.csv`](results/phaseC/summary.csv)

## クイックスタート（Docker）

```bash
docker compose -f docker/docker-compose.yml build
docker compose -f docker/docker-compose.yml up -d

# シェルA: Gazebo（真値付き・ヘッドレス）
docker compose -f docker/docker-compose.yml exec loc_eval bash
ros2 launch loc_eval gazebo_gt.launch.py gui:=false

# シェルB: 5手法 × 3試行を一括評価 → results/phaseC/summary.csv
docker compose -f docker/docker-compose.yml exec loc_eval bash
ros2 run loc_eval run_all.sh /ros2_ws/results/phaseC 3
```

詳細な手順（GUI 観察・個別手法・地図再生成・トラブルシュート）は
**[docker/README.md](docker/README.md)（手順書）** を参照。

## 仕組み

全手法に**同一入力・同一真値・同一指標**を与えるのが要。

| トピック | 役割 |
|---|---|
| `/ground_truth/odom` | 真値（Gazebo P3D、frame=map） |
| `/scan`, `/odom` | 全手法共通の入力 |
| `map → base_footprint` (TF) | 各手法の推定（Cartographer のみ `/tracked_pose`） |

`traj_logger.py` が真値と推定を同一タイムスタンプで TUM 出力し、`eval_evo.sh` が
`evo_ape`/`evo_rpe` で ATE/RPE を算出。`run_method.sh` は各 run で
`/reset_world`（初期姿勢統一）→ 手法起動 → 標準軌跡 → evo → プロセス一括停止を自動化。

## 構成

```
loc_eval/
  launch/    gazebo_gt.launch.py, {amcl,als_ros2,slam_toolbox,cartographer,mrpt}.launch.py
             {slam_toolbox,cartographer}_mapping.launch.py
  config/    各手法パラメータ, cartographer lua
  maps/      turtlebot3_world.{yaml,pgm}, *_stb.posegraph/.data, *.pbstream（同梱）
  scripts/   traj_logger.py, eval_evo.sh, run_method.sh, run_all.sh
  models/    turtlebot3_burger_gt/   （真値 P3D プラグイン付きモデル）
  docker/    Dockerfile, entrypoint.sh, docker-compose.yml, README.md（手順書）
```

## 依存

ROS 2 Humble / Gazebo Classic / TurtleBot3。評価手法は apt から導入、`als_ros2` は
ソース（[iASL-Gifu/als_ros2](https://github.com/iASL-Gifu/als_ros2)）。詳細は Dockerfile を参照。

## 評価候補と除外した手法

当初は 7 手法を評価候補として検討したが、次の 2 手法は **ROS 2 Humble で動作しない**ため
評価対象から外し、上記 5 手法に絞った。

- **gmcl** — 公式実装は ROS 1 のみで、ROS 2 Humble 向けの移植版が存在しない。
- **iris_lama** — ROS 2 対応ブランチが dashing / eloquent 止まりで、Humble ではビルドできない。

（同系統の ROS 2 代替として `beluga` や `emcl2_ros2` が候補になり得る。）

## ライセンス

本パッケージは Apache-2.0。各評価手法は個々のライセンス（表の通り）に従う。
