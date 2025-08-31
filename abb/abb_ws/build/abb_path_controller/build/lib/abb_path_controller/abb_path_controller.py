from rclpy.node import Node
import rclpy

from nav_msgs.msg import Path
from geometry_msgs.msg import Twist

from tf2_ros import Buffer, TransformListener
from tf2_ros import LookupException, ConnectivityException, ExtrapolationException
from icecream import ic

class PathController(Node):
    def __init__(self):
        super().__init__("controller_node")

        self.path_subs = self.create_subscription(Path, "/abb/cmd_path", self.path_sub_callback, 10)
        self.cmd_vel_pub = self.create_publisher(Twist, "/abb/cmd_vel", 10)
        self.odom_timer = self.create_timer(0.1, self.get_robot_pose)

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)


        self.path = []

    def path_sub_callback(self, msg : Path):
        self.path = msg.poses

    def get_robot_pose(self):
        try:
            now = rclpy.time.Time()
            transformation = self.tf_buffer.lookup_transform(
                "base_link",
                "end_effector",
                now,
                timeout=rclpy.duration.Duration(seconds=0.5)
            )
            self.base_link_end_effector_translation_tf = transformation.transform
            ic(self.base_link_end_effector_translation_tf)
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