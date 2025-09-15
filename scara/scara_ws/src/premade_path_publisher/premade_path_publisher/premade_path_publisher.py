from rclpy.node import Node
import rclpy

from nav_msgs.msg import Path
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64MultiArray

from tf2_ros import Buffer, TransformListener
from tf2_ros import LookupException, ConnectivityException, ExtrapolationException
from icecream import ic
from ament_index_python.packages import get_package_share_directory
import os
from glob import glob
import time
from geometry_msgs.msg import PoseStamped


package_name = 'premade_path_publisher'


class PathController(Node):
    def __init__(self):
        super().__init__("premade_path_publisher")

        self.pose_pub = self.create_publisher(Path, "/scara/cmd_path", 10)
        self.odom_timer = self.create_timer(0.1, self.get_robot_pose)

        self.path_file = os.path.join(get_package_share_directory(package_name),'config','path_square.txt')

        with open(self.path_file, "r") as f:
            lines = f.readlines()
            self.points_interest = [[float(num) for num in line.strip().split('|')] for line in lines]
        

        self.publish_flag = 1

        time.sleep(8)
 
        self.publish_flag = 0


    def get_robot_pose(self):

        if not self.publish_flag:
            path_msg = Path()
            path_msg.header.frame_id = "world_0"
            path_msg.header.stamp = self.get_clock().now().to_msg()
            
            for poses_of_interests in self.points_interest:
                pose = PoseStamped()
                pose.header.frame_id = "world_0"
                pose.header.stamp = self.get_clock().now().to_msg()
                pose.pose.position.x = float(poses_of_interests[0])
                pose.pose.position.y = float(poses_of_interests[1])
                pose.pose.position.z = float(poses_of_interests[2])
                pose.pose.orientation.w = 1.0  # identity quaternion    
                path_msg.poses.append(pose)
        
            self.pose_pub.publish(path_msg)
            self.get_logger().info(f"Published path with {len(path_msg.poses)} poses")
            self.publish_flag = 1
            
        time.sleep(5)


        

def main():

    rclpy.init(args=None)
    path_contr_node = PathController()
    rclpy.spin(path_contr_node)
    path_contr_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()