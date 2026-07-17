-- Cartographer 2D PURE LOCALIZATION against a frozen .pbstream (see mapping config
-- loc_eval_2d.lua). Loaded with -load_state_filename <map.pbstream> and
-- -load_frozen_state true by the localization launch.

include "loc_eval_2d.lua"

-- Publish the smoothed pose of tracking_frame in map on /tracked_pose. The TF
-- (map->odom) is jumpy with TB3's 5 Hz LiDAR, so evaluation logs this pose topic
-- instead (see cartographer.launch.py est_topic).
options.publish_tracked_pose = true

TRAJECTORY_BUILDER.pure_localization_trimmer = {
  max_submaps_to_keep = 3,
}

POSE_GRAPH.optimize_every_n_nodes = 20

return options
