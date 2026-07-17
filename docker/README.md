# loc_eval — 2D自己位置推定ベンチマーク（Docker再現手順書）

TurtleBot3 (Gazebo Classic) 上で **5つの2D LiDAR自己位置推定手法**を、同一の地図・
走行・真値に対し **evo** の ATE / RPE で定量比較する環境一式を、Docker で再現するための手順書です。

| 手法 | 方式 | ライセンス | ATE平均±σ (mm)※ |
|---|---|---|---|
| slam_toolbox | スキャンマッチ (localization) | LGPL-2.1 | 7.5 ± 0.7 |
| als_ros2 | Reliable MCL (RBPF) | Apache-2.0 | 8.2 ± 0.2 |
| Cartographer | グラフ最適化 (pure localization) | Apache-2.0 | 10.5 ± 1.0 |
| AMCL (nav2) | Adaptive MCL (KLD) | Apache/LGPL | 16.3 ± 5.0 |
| mrpt_pf_localization | Particle Filter (SE2) | BSD 3-Clause | 181.9 ± 92.1 |

※ `turtlebot3_world`・28秒周回・3試行の参考値（環境により多少変動します）。

---

## 1. 前提条件

- **Docker**（Engine 20.10+ / `docker compose` v2）。ディスク空き **10 GB 程度**。
- ヘッドレス評価だけなら GPU 不要。**GUI（Gazebo/RViz）で観察**する場合は Linux + X11 を推奨。
- 本手順書は `loc_eval` パッケージのルート（この `docker/` の親ディレクトリ）で実行します。

```bash
cd <path>/ros2_ws/src/loc_eval      # package.xml がある場所
```

---

## 2. イメージのビルド

```bash
# compose を使う場合（推奨）
docker compose -f docker/docker-compose.yml build

# もしくは docker 単体
docker build -f docker/Dockerfile -t loc_eval:humble .
```

ビルドでは apt から ROS 2 Humble / Gazebo / TurtleBot3 / nav2 / cartographer /
slam_toolbox / mrpt を導入し、`als_ros2`（GitHub から clone）と `loc_eval` を
`colcon build` します。事前生成済みの地図（占有格子 `.pgm`、slam_toolbox の
`.posegraph`、Cartographer の `.pbstream`）はパッケージに同梱しているため、
**すぐに localization を実行できます**（再マッピング不要）。

---

## 3. コンテナ起動

```bash
docker compose -f docker/docker-compose.yml up -d
```

`docker-compose.yml` は次を設定します。
- `network_mode: host` … ROS 2 DDS のディスカバリと X11 を簡単に
- `ROS_DOMAIN_ID=42` … ホスト上の他 ROS ノードと混線しない
- `./results` → コンテナの `/ros2_ws/results` にマウント（結果がホストに残る）

GUI を使う場合は起動前にホストで一度だけ許可します。
```bash
xhost +local:docker
```

---

## 4. 評価の実行（ヘッドレス一括：最短ルート）

コンテナに **2つのシェル**で入り、A で Gazebo、B で評価を回します。

**シェル A — Gazebo（真値付き, ヘッドレス）:**
```bash
docker compose -f docker/docker-compose.yml exec loc_eval bash
ros2 launch loc_eval gazebo_gt.launch.py gui:=false
```

**シェル B — 5手法 × 3試行を一括評価:**
```bash
docker compose -f docker/docker-compose.yml exec loc_eval bash
ros2 run loc_eval run_all.sh /ros2_ws/results/phaseC 3
```

`run_all.sh` は各 run で自動的に
**`/reset_world`（初期姿勢統一）→ 手法起動 → 標準軌跡走行 → evo → プロセス一括停止**
を行い、`/ros2_ws/results/phaseC/summary.csv`（=ホストの `./results/phaseC/summary.csv`）に
ATE/RPE を追記します。所要 **約12〜15分**。

**結果の確認:**
```bash
cat /ros2_ws/results/phaseC/summary.csv
```
```
method,trial,ate_rmse_m,rpe_rmse_m
slam_toolbox,1,0.008113,0.005630
...
```

---

## 5. 個別手法を単発で実行する

`gazebo_gt.launch.py` を起動した状態（シェルA）で、別シェルから任意の手法を起動できます。
各手法起動の**前に** `ros2 service call /reset_world std_srvs/srv/Empty` を実行してください
（初期姿勢を揃えるための必須手順）。

| 手法 | 起動コマンド |
|---|---|
| AMCL | `ros2 launch loc_eval amcl.launch.py out_dir:=/ros2_ws/results run_name:=amcl` |
| als_ros2 | `ros2 launch loc_eval als_ros2.launch.py out_dir:=/ros2_ws/results run_name:=als` |
| slam_toolbox | `ros2 launch loc_eval slam_toolbox.launch.py out_dir:=/ros2_ws/results run_name:=stb` |
| Cartographer | `ros2 launch loc_eval cartographer.launch.py out_dir:=/ros2_ws/results run_name:=carto` |
| mrpt | `ros2 launch loc_eval mrpt.launch.py out_dir:=/ros2_ws/results run_name:=mrpt` |

走行させて（例）：
```bash
timeout 28 ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.15}, angular: {z: 0.35}}"
```
評価：
```bash
ros2 run loc_eval eval_evo.sh \
  /ros2_ws/results/<run>_gt.tum /ros2_ws/results/<run>_est.tum /ros2_ws/results <run>
```

---

## 6. GUI で観察する（任意）

```bash
# ホストで一度: xhost +local:docker
# シェルA:
ros2 launch loc_eval gazebo_gt.launch.py gui:=true
# 別シェル: RViz で map / scan / TF を確認
rviz2
```
`gui:=true` で Gazebo クライアントが立ち上がります（要 X11）。

---

## 7. 地図を作り直す（任意）

同梱地図で足りる場合は不要です。別ワールドや再作成が必要なときのみ。

**slam_toolbox（posegraph）:**
```bash
ros2 launch loc_eval slam_toolbox_mapping.launch.py      # 別シェルで robot を走らせて地図化
ros2 service call /slam_toolbox/serialize_map slam_toolbox/srv/SerializePoseGraph \
  "{filename: /ros2_ws/src/loc_eval/maps/turtlebot3_world_stb}"
```
**Cartographer（pbstream）:**
```bash
ros2 launch loc_eval cartographer_mapping.launch.py
ros2 service call /finish_trajectory cartographer_ros_msgs/srv/FinishTrajectory "{trajectory_id: 0}"
ros2 service call /write_state cartographer_ros_msgs/srv/WriteState \
  "{filename: '/ros2_ws/src/loc_eval/maps/turtlebot3_world.pbstream', include_unfinished_submaps: false}"
```
作り直したら `colcon build --packages-select loc_eval` を再実行します。

---

## 8. 構成と仕組み

```
loc_eval/
  launch/    gazebo_gt.launch.py              # TB3 + P3D真値 + ワールド
             {amcl,als_ros2,slam_toolbox,cartographer,mrpt}.launch.py
             {slam_toolbox,cartographer}_mapping.launch.py
  config/    各手法パラメータ, cartographer lua
  maps/      turtlebot3_world.{yaml,pgm}, *_stb.posegraph/.data, *.pbstream
  scripts/   traj_logger.py  eval_evo.sh  run_method.sh  run_all.sh
  models/    turtlebot3_burger_gt/           # 真値P3Dプラグイン付きモデル
  docker/    Dockerfile  entrypoint.sh  docker-compose.yml  README.md(本書)
```

**評価アーキテクチャ**：全手法に同一入力・同一真値・同一指標を与えます。

| トピック | 役割 |
|---|---|
| `/ground_truth/odom` | 真値（Gazebo P3D、frame=map） |
| `/scan`, `/odom` | 全手法共通の入力 |
| `map → base_footprint` (TF) | 各手法の推定（Cartographerのみ `/tracked_pose`） |

`traj_logger.py` が真値と推定を同一タイムスタンプで TUM 出力し、`eval_evo.sh` が
`evo_ape`/`evo_rpe`（SE(3) Umeyama整列）で ATE/RPE を算出します。

---

## 9. トラブルシューティング

- **GUI が出ない / `cannot connect to display`**：ホストで `xhost +local:docker` を実行。
  X11 が無い環境（サーバ等）では `gui:=false` のヘッドレスで評価してください。
- **描画が重い / ソフトウェアレンダリング**：ヘッドレス評価（`gui:=false`）では GPU 不要。
  GUI で GPU を使う場合は `--gpus all` 等の追加設定を検討。
- **他の ROS ノードと混線する**：`ROS_DOMAIN_ID`（compose では 42）を使い分ける。
- **mrpt が `UNINITIALIZED` のまま**：`mrpt_map_server` が `/mrpt_map/metric_map` を
  配信できているか確認。`mrpt.launch.py` は占有格子 yaml を自動で MRPT メトリックマップに変換します。
- **Cartographer の精度が極端に悪い**：TB3 の LiDAR が 5 Hz と低速で `map→odom` TF が
  ジャンプするため、本環境では滑らかな `/tracked_pose` を記録して評価しています
  （`cartographer.launch.py` が設定済み）。
- **`map_server` の GraphicsMagick エラー**：Docker では通常発生しません
  （ライブラリが正規の位置にあるため）。ローカル環境固有の対処が launch に入っていますが無害です。
- **結果がホストに出ない**：out_dir を `/ros2_ws/results/...` にする（compose のマウント先）。

---

## 10. ライセンス

各手法は個別ライセンスに従います（表の通り）。`als_ros2` は Apache-2.0、
`mrpt_pf_localization` は BSD-3、`slam_toolbox` は LGPL-2.1、`Cartographer`/`nav2_amcl` は
Apache-2.0系。外部ノードとして利用する構成のため実務上の制約は小さいですが、配布時は各
リポジトリのライセンスをご確認ください。
