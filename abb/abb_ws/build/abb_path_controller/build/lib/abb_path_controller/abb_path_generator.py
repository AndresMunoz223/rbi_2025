from rclpy.node import Node
import rclpy

from nav_msgs.msg import Path
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64MultiArray
from geometry_msgs.msg import PoseStamped
from geometry_msgs.msg import Pose

from tf2_ros import Buffer, TransformListener
from tf2_ros import LookupException, ConnectivityException, ExtrapolationException
from icecream import ic

import numpy as np

class PathGenerator(Node):
    def __init__(self):
        super().__init__("path_generator_node")

        self.path_pub = self.create_publisher(Path, "/abb/path", 10)
        self.goal_pose_subs = self.create_subscription(PoseStamped, "/goal_pose", self.goal_pose_callback,10)
        self.odom_timer = self.create_timer(0.1, self.get_robot_pose)

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.base_link_3_translation_tf = None
        self.base_link_4_translation_tf = None
        self.base_link_end_effector_translation_tf = None

        #? Path config
        self.path_resolution = 0.01
        self.goal_pose = None
        self.world_path = []
        self.c_path = []

    def goal_pose_callback(self, msg : PoseStamped):
        self.goal_pose = msg.pose


    def astar(self, pose_1 : Pose, pose_2 : Pose ):
        pose_upper_limmit_x = np.max(np.array([pose_1.position.x, pose_2.position.x ]))
        pose_lower_limmit_x = np.min(np.array([pose_1.position.x, pose_2.position.x ]))

        pose_upper_limmit_y = np.max(np.array([pose_1.position.y, pose_2.position.y ]))
        pose_lower_limmit_y = np.min(np.array([pose_1.position.y, pose_2.position.y ]))

        pose_upper_limmit_z = np.max(np.array([pose_1.position.z, pose_2.position.z ]))
        pose_lower_limmit_z = np.min(np.array([pose_1.position.z, pose_2.position.z ]))        

        x_axis = np.arange(pose_lower_limmit_x,pose_upper_limmit_x, self.path_resolution)
        y_axis = np.arange(pose_lower_limmit_y,pose_upper_limmit_y, self.path_resolution)
        z_axis = np.arange(pose_lower_limmit_z,pose_upper_limmit_z, self.path_resolution)

        

        pass

    def get_robot_pose(self):
        try:
            now = rclpy.time.Time()
            transformation = self.tf_buffer.lookup_transform(
                "base_link",
                "link_3",
                now,
                timeout=rclpy.duration.Duration(seconds=0.5)
            )
            self.base_link_3_translation_tf = transformation.transform
            ic(f"Bl-l3 : {self.base_link_3_translation_tf}")

            transformation = self.tf_buffer.lookup_transform(
                "base_link",
                "link_4",
                now,
                timeout=rclpy.duration.Duration(seconds=0.5)
            )
            self.base_link_4_translation_tf = transformation.transform
            ic(f"fBl-l4 : {self.base_link_4_translation_tf}")


            transformation = self.tf_buffer.lookup_transform(
                "base_link",
                "end_effector",
                now,
                timeout=rclpy.duration.Duration(seconds=0.5)
            )

            self.base_link_end_effector_translation_tf = transformation.transform
            ic(f"Bl-eef : {self.base_link_end_effector_translation_tf}")


        except (LookupException, ConnectivityException, ExtrapolationException):
            self.get_logger().warn("TF tree failed")
            pass



def main():

    rclpy.init(args=None)
    path_contr_node = PathGenerator()
    rclpy.spin(path_contr_node)
    path_contr_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()