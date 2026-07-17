#!/usr/bin/env python3
"""Online trajectory logger for localization accuracy evaluation.

Writes two TUM-format trajectory files:
  * <run>_gt.tum   -- ground truth, taken from a nav_msgs/Odometry topic
                      (default /ground_truth/odom, published by the Gazebo P3D plugin)
  * <run>_est.tum  -- localization estimate, taken from the map->base TF that
                      every evaluated method publishes (map_frame -> base_frame)

Both files use the ground-truth message timestamp, so the pair is time-aligned and
can be fed directly to evo (evo_ape / evo_rpe) with a small --t_max_diff.

TUM line format:  timestamp tx ty tz qx qy qz qw

This single logger works for all 7 evaluated methods because they all expose the
estimated pose as the map->base_footprint transform (map->odom TF + odom->base
from the diff-drive plugin). Choosing TF as the common estimate source keeps the
comparison apples-to-apples regardless of each method's pose-topic conventions.
"""

import os

import rclpy
from rclpy.node import Node
from rclpy.time import Time
from nav_msgs.msg import Odometry
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped

import tf2_ros


class TrajLogger(Node):
    def __init__(self):
        super().__init__('traj_logger')

        self.gt_topic = self.declare_parameter('gt_topic', '/ground_truth/odom').value
        self.map_frame = self.declare_parameter('map_frame', 'map').value
        self.base_frame = self.declare_parameter('base_frame', 'base_footprint').value
        # If est_topic is set, read the estimate from that pose topic instead of the
        # map->base TF. Use this for methods whose TF is jumpy but which publish a
        # smooth pose (e.g. Cartographer /tracked_pose). est_topic_type is
        # 'PoseStamped' (default) or 'PoseWithCovarianceStamped'.
        self.est_topic = self.declare_parameter('est_topic', '').value
        self.est_topic_type = self.declare_parameter('est_topic_type', 'PoseStamped').value
        out_dir = self.declare_parameter('out_dir', '/tmp/loc_eval').value
        run_name = self.declare_parameter('run_name', 'run').value

        os.makedirs(out_dir, exist_ok=True)
        self.gt_path = os.path.join(out_dir, f'{run_name}_gt.tum')
        self.est_path = os.path.join(out_dir, f'{run_name}_est.tum')
        # Line-buffered so each TUM row is flushed whole -- a reader (evo) never
        # sees a torn line even if it runs while logging is still in progress.
        self.gt_file = open(self.gt_path, 'w', buffering=1)
        self.est_file = open(self.est_path, 'w', buffering=1)

        self.gt_count = 0
        self.est_count = 0
        self.latest_est = None  # (x,y,z,qx,qy,qz,qw) from est_topic, if used

        if self.est_topic:
            msg_type = (PoseWithCovarianceStamped
                        if self.est_topic_type == 'PoseWithCovarianceStamped'
                        else PoseStamped)
            self.create_subscription(msg_type, self.est_topic, self.est_cb, 50)
            est_src = f'topic {self.est_topic} ({self.est_topic_type})'
        else:
            self.tf_buffer = tf2_ros.Buffer()
            self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
            est_src = f'TF {self.map_frame}->{self.base_frame}'

        self.create_subscription(Odometry, self.gt_topic, self.gt_cb, 50)

        self.get_logger().info(
            f'Logging GT from {self.gt_topic} and estimate from {est_src}'
            f'\n  gt : {self.gt_path}\n  est: {self.est_path}')

    def est_cb(self, msg):
        p = msg.pose.pose.position if hasattr(msg.pose, 'pose') else msg.pose.position
        q = msg.pose.pose.orientation if hasattr(msg.pose, 'pose') else msg.pose.orientation
        self.latest_est = (p.x, p.y, p.z, q.x, q.y, q.z, q.w)

    def gt_cb(self, msg: Odometry):
        stamp = msg.header.stamp
        t = stamp.sec + stamp.nanosec * 1e-9

        p = msg.pose.pose.position
        q = msg.pose.pose.orientation
        self.gt_file.write(f'{t:.6f} {p.x:.6f} {p.y:.6f} {p.z:.6f} '
                           f'{q.x:.6f} {q.y:.6f} {q.z:.6f} {q.w:.6f}\n')
        self.gt_count += 1

        # Estimate tagged with the GT stamp, from a pose topic or the map->base TF.
        if self.est_topic:
            if self.latest_est is None:
                return
            x, y, z, qx, qy, qz, qw = self.latest_est
        else:
            try:
                tf = self.tf_buffer.lookup_transform(self.map_frame, self.base_frame, Time())
            except tf2_ros.TransformException:
                return
            tr = tf.transform.translation
            rot = tf.transform.rotation
            x, y, z, qx, qy, qz, qw = tr.x, tr.y, tr.z, rot.x, rot.y, rot.z, rot.w

        self.est_file.write(f'{t:.6f} {x:.6f} {y:.6f} {z:.6f} '
                            f'{qx:.6f} {qy:.6f} {qz:.6f} {qw:.6f}\n')
        self.est_count += 1

    def destroy_node(self):
        try:
            self.gt_file.flush()
            self.gt_file.close()
            self.est_file.flush()
            self.est_file.close()
            self.get_logger().info(
                f'Wrote {self.gt_count} GT poses, {self.est_count} EST poses.')
        except Exception:
            pass
        super().destroy_node()


def main():
    rclpy.init()
    node = TrajLogger()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
