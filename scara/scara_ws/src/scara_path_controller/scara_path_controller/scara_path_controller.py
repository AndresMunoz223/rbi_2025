from rclpy.node import Node
import rclpy

from nav_msgs.msg import Path
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64MultiArray

from tf2_ros import Buffer, TransformListener
from tf2_ros import LookupException, ConnectivityException, ExtrapolationException
from icecream import ic

import time

from geometry_msgs.msg import PoseStamped

class PathController(Node):
    def __init__(self):
        super().__init__("position_controller_node")

        self.path_subs = self.create_subscription(Path, "/scara/cmd_path", self.path_sub_callback, 10)
        self.pose_pub = self.create_publisher(PoseStamped, "/scara/path/goal_pose", 10)
        self.odom_timer = self.create_timer(0.1, self.get_robot_pose)

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        

        self.path = []
        self.epsilon_lin = 0.03
        self.epsilon_ang = 0.03

    def path_sub_callback(self, msg : Path):
        self.path = msg.poses

        for poses in self.path:
            
            msg = PoseStamped()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = "world_0"

            msg.pose.position.x = float(poses.pose.position.x)
            msg.pose.position.y = float(poses.pose.position.y)
            msg.pose.position.z = float(poses.pose.position.z)

            msg.pose.orientation.x = 0.
            msg.pose.orientation.y = 0.
            msg.pose.orientation.z = 0.
            msg.pose.orientation.w = 1.

            self.pose_pub.publish(msg)
            # self.get_logger().info(f'Publishing pose: {msg}')
            
            time.sleep(1.8)        

    def get_robot_pose(self):
        try:
            now = rclpy.time.Time()
            transformation = self.tf_buffer.lookup_transform(
                "world_0",
                "tool",
                now,
                timeout=rclpy.duration.Duration(seconds=0.5)
            )
            self.base_link_end_effector_translation_tf = transformation.transform
        except (LookupException, ConnectivityException, ExtrapolationException):
            self.get_logger().warn("TF tree failed")
            pass

        

def main():

    rclpy.init(args=None)
    path_contr_node = PathController()
    rclpy.spin(path_contr_node)
    path_contr_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()