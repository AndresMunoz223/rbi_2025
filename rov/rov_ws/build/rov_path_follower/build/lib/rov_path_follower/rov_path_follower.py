from rclpy.node import Node
import rclpy
import numpy as np

from tf2_ros import Buffer, TransformListener
from tf2_ros import LookupException, ConnectivityException, ExtrapolationException
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Path

from icecream import ic



#! Path follower node
class PathFollower(Node):
    def __init__(self):
        super().__init__("path_follower_node")
        
        self.path_subs = self.create_subscription(Path, "/path", self.path_callback, 10)
        self.traversed_pub = self.create_publisher(Path, '/traversed_path', 10)
        
        self.goal_pose_pub = self.create_publisher(PoseStamped, "/rov/goal_pose", 10)
        
        self.pose_timer = self.create_timer(0.1, self.point_control_clock)
        self.position_timer = self.create_timer(0.1, self.get_pose)
        self.position_path_timer = self.create_timer(0.35, self.publish_path)
        
        self.path = None
        self.goal_pose = PoseStamped()
        self.prev_positions = []
        self.current_position = None
        
        self.path_msg = Path()
        self.path_msg.header.frame_id = "odom"
        
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)        
        self.point_thresh = 1.3
        self.ring_margin = 0.25
        
        self.current_point = None
        
        self.current_index = None

    
    def path_callback(self, msg : Path):
        #! Create the pose array
        self.msg_lenght = len(msg.poses)
        self.path = np.zeros((3, self.msg_lenght))
        self.current_index = 0
        
        
        if self.current_position is not None:
            ic(self.current_position)
            for ii in range(self.msg_lenght):
                self.path[0][ii] = msg.poses[ii].pose.position.x
                self.path[1][ii] = msg.poses[ii].pose.position.y
                self.path[2][ii] = msg.poses[ii].pose.position.z
            ic(self.path)
                    
    def point_control_clock(self):
    
        if self.current_position is not None and self.path is not None:
    
            selected_point = None
            
            max_dist = 10000

            if self.current_index >= self.msg_lenght - 1:
                # ic(self.current_point)
                # ic(vec)
                # ic("Finished movement")
                pass
            else:       
                for ii in range(self.msg_lenght):
                    vec = np.array([[self.path[:,ii][0]],[self.path[:,ii][1]],[self.path[:,ii][2]]])
                    distance_to = np.linalg.norm(self.current_position - vec)
                    
                    # ic(self.current_position)
                    # ic(distance_to)
                    if self.point_thresh - self.ring_margin < distance_to < self.point_thresh + self.ring_margin and self.current_index < ii:
                        # ic(distance_to)
                        if max_dist > distance_to: 
                            selected_point = self.path[:,ii]
                            best_distance = distance_to
                            self.current_index = ii
                            max_dist = distance_to
                # ic("..................")
                
                        
            if selected_point is not None:
                self.current_point = selected_point
                        

            # else:
                # ic("path not found")
                # ic(self.current_index)
                
            if self.current_point is not None:    
                    
                self.goal_pose.header.frame_id = 'odom'
                self.goal_pose.pose.position.x = self.current_point[0]
                self.goal_pose.pose.position.y = self.current_point[1]
                self.goal_pose.pose.position.z = self.current_point[2]
                
                
                self.goal_pose.pose.orientation.x = 0.0
                self.goal_pose.pose.orientation.y = 0.0
                self.goal_pose.pose.orientation.z = 0.0
                self.goal_pose.pose.orientation.w = 1.0
                
                self.goal_pose_pub.publish(self.goal_pose)
                # ic(self.goal_pose.pose.position)
                


                        
    def publish_path(self):
        
        if self.current_position is not None:
            self.path_msg.header.stamp = self.get_clock().now().to_msg()                

            pose = PoseStamped()
            pose.header.frame_id = "odom"
            pose.header.stamp = self.get_clock().now().to_msg()
            pose.pose.position.x = self.current_position[0][0]
            pose.pose.position.y = self.current_position[1][0]
            pose.pose.position.z = self.current_position[2][0]
            pose.pose.orientation.w = 1.0  # identity quaternion
            
            self.path_msg.poses.append(pose)
            self.traversed_pub.publish(self.path_msg)
            # self.get_logger().info(f"Published path with {len(self.path_msg.poses)} poses")
        
            
    def get_pose(self):
        try:
            transform = self.tf_buffer.lookup_transform(
                target_frame="odom", 
                source_frame="base_link", 
                time=rclpy.time.Time()
            )
            # Translation
            t = transform.transform.translation
            self.current_position = np.array([[float(t.x)], [float(t.y)], [float(t.z)]])
            # ic(self.current_position)
            
        except (LookupException, ConnectivityException, ExtrapolationException):
            self.get_logger().warn("TF tree failed")
        
        
def main():
    rclpy.init(args=None)
    node = PathFollower()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()