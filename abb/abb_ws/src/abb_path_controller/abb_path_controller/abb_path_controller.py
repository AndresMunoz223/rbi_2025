from rclpy.node import Node
import rclpy

from nav_msgs.msg import Path
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64MultiArray

from tf2_ros import Buffer, TransformListener
from tf2_ros import LookupException, ConnectivityException, ExtrapolationException
from icecream import ic

class PathController(Node):
    def __init__(self):
        super().__init__("position_controller_node")

        self.path_subs = self.create_subscription(Path, "/abb/cmd_path", self.path_sub_callback, 10)
        self.cmd_vel_pub = self.create_publisher(Float64MultiArray, "/arm_joints_controller/commands", 10)
        self.odom_timer = self.create_timer(0.1, self.get_robot_pose)

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        

        self.path = []
        self.epsilon_lin = 0.03
        self.epsilon_ang = 0.03

    def path_sub_callback(self, msg : Path):
        self.path = msg.poses

    def get_robot_pose(self):
        try:
            now = rclpy.time.Time()
            transformation = self.tf_buffer.lookup_transform(
                "odom",
                "base_link",
                now,
                timeout=rclpy.duration.Duration(seconds=0.5)
            )
            self.base_link_end_effector_translation_tf = transformation.transform
        except (LookupException, ConnectivityException, ExtrapolationException):
            self.get_logger().warn("TF tree failed")
            pass

    def position_controller_post(self):
        pass
    #! Si está a un epsilon de la posición deseada, seguir con el siguiente punto.

def main():

    rclpy.init(args=None)
    path_contr_node = PathController()
    rclpy.spin(path_contr_node)
    path_contr_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()