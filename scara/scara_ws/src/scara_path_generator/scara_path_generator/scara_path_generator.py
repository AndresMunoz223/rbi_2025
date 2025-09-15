from rclpy.node import Node
import rclpy
import numpy as np

from tf2_ros import Buffer, TransformListener
from tf2_ros import LookupException, ConnectivityException, ExtrapolationException
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Path

#! Vamos a plotear
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from icecream import ic

ic.disable()

class Astar3DNode(Node):
# class Astar3DNode():
    def __init__(self):
        super().__init__("path_generator_node")
        
        #! Dummy stuff prior to actually getting the map
        
        self.map_x_resolution = 0.005 #[m]
        self.map_y_resolution = 0.005 #[m]
        self.map_z_resolution = 0.005 #[m]
        
        self.current_position = np.array([[0./self.map_x_resolution], [0./self.map_y_resolution], [0./self.map_z_resolution]], dtype=int)    

        self.flag = 0.;
        self.generated_map = None
        self.map_region = None
        
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.pose_timer = self.create_timer(0.1, self.get_pose)
        self.goal_pose_subs = self.create_subscription(PoseStamped, "/goal_pose", self.goal_pose_callback, 10)
        self.path_pub = self.create_publisher(Path, '/scara/cmd_path', 10)
        
        self.goal_pose = None
        
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111, projection='3d')

        self.movements = {
            1: np.array([[-1], [ 0], [ 0]], dtype=int),  
            2: np.array([[ 1], [ 0], [ 0]], dtype=int),  
            3: np.array([[ 0], [-1], [ 0]], dtype=int),  
            4: np.array([[ 0], [ 1], [ 0]], dtype=int),  
            5: np.array([[ 0], [ 0], [-1]], dtype=int),  
            6: np.array([[ 0], [ 0], [ 1]], dtype=int), 
        }

        self.path = np.array([], dtype=float)
        self.map_exp = 1.
        self.safe_zone_astar = np.array([[int(0.5*self.map_exp/self.map_x_resolution)],[int(0.5*self.map_exp/self.map_y_resolution)],[int(0.5*self.map_exp/self.map_z_resolution)]])
        
    def a_star(self, final_pose : np.array):
        current_pose = self.safe_zone_astar
        final_pose = self.safe_zone_astar + final_pose

        ic(current_pose, final_pose)

        #! Excluimos un movimiento al no evaluar la casilla actual

        points = 0
        best_move = 0
        current_cost = 1000000.
        err_pose = final_pose - current_pose
        zero = np.array([[0],[0],[0]])
        
        ic("Entered A*")
        while np.linalg.norm(err_pose) != 0.:
            # ic(err_pose)
            try: 
                for ii in range(len(self.movements)):
                    curr_move = self.movements[ii + 1]
                    value = self.generated_map[curr_move[0][0] + current_pose[0][0]][curr_move[1][0] + current_pose[1][0]][curr_move[2][0] + current_pose[2][0]]
                    next_pose = current_pose + curr_move
                    err_pose  = final_pose - next_pose
                    euclidean_cost = np.linalg.norm(err_pose)
                    cost = euclidean_cost + value
                    if current_cost > cost : 
                        current_cost = cost 
                        best_move = curr_move
                        # ic(best_move)
                    points += 1
            except:
                self.generated_map[current_pose[0][0]][current_pose[1][0]][current_pose[2][0]] = 1
                ic(err_pose)
                break
                # ic(euclidean_cost, best_move, curr_move)
            current_pose = current_pose + best_move
            self.generated_map[current_pose[0][0]][current_pose[1][0]][current_pose[2][0]] = 1
        ic("Exited A*")
        

    def goal_pose_callback(self, msg :PoseStamped):
        
        self.goal_pose = np.array([[msg.pose.position.x], [msg.pose.position.y], [msg.pose.position.z]])
        ic(self.goal_pose, self.current_position)
        
        if self.goal_pose is not None and self.current_position is not None and self.flag is not None:
            
            
            error_pose = self.goal_pose - self.current_position    
            # ic(error_pose)
            
            self.map_region = np.array([[np.abs(error_pose[0][0]) + self.map_exp*2],[np.abs(error_pose[1][0]) + self.map_exp*2],[np.abs(error_pose[2][0]) + self.map_exp*2]])
            self.goal_pose = np.array([[msg.pose.position.x/self.map_x_resolution], [msg.pose.position.y/self.map_y_resolution], [msg.pose.position.z/self.map_z_resolution]])
            current_position_ref = np.array([[self.current_position[0][0]/self.map_x_resolution], [self.current_position[1][0]/self.map_y_resolution], [self.current_position[2][0]/self.map_z_resolution]])
            
            error_pose = self.goal_pose - current_position_ref   
            error_pose_ref = error_pose.copy()
            
            for ii in range(3):
                if error_pose[ii][0] < 0:
                    error_pose_ref[ii][0] = -error_pose_ref[ii][0]
                    
            # ic(error_pose_ref, self.map_region)
            self.generated_map = np.zeros((int(self.map_region[0][0]/self.map_x_resolution),
                                int(self.map_region[1][0]/self.map_y_resolution),
                                int(self.map_region[2][0]/self.map_z_resolution)))
            
            
            error_pose_ref = np.array([[int(error_pose_ref[0])],
                                       [int(error_pose_ref[1])],
                                       [int(error_pose_ref[2])]])
            
            # ic(self.generated_map.shape)
            
            self.a_star(error_pose_ref)

            path = np.argwhere(self.generated_map == 1)
            path = path.T
    

            path = path - self.safe_zone_astar
            
            ic
            for ii in range(3):
                if error_pose[ii][0] < 0:
                    path[ii] = -path[ii]

            path = path + current_position_ref

            x = path[0]*self.map_x_resolution
            y = path[1]*self.map_y_resolution
            z = path[2]*self.map_z_resolution
            
            # ic(x,y,z)
            
            path_msg = Path()
            path_msg.header.frame_id = "world_0"
            path_msg.header.stamp = self.get_clock().now().to_msg()

            
            for xi, yi, zi in zip(x, y, z):
                pose = PoseStamped()
                pose.header.frame_id = "world_0"
                pose.header.stamp = self.get_clock().now().to_msg()
                pose.pose.position.x = float(xi)
                pose.pose.position.y = float(yi)
                pose.pose.position.z = float(zi)
                pose.pose.orientation.w = 1.0  # identity quaternion
                path_msg.poses.append(pose)
            
                        # publish once
            self.path_pub.publish(path_msg)
            self.get_logger().info(f"Published path with {len(path_msg.poses)} poses")
            
            self.flag = None;
                        
            self.ax.scatter(x, y, z, c="r", marker="o")
            # plt.show()
            

        
    def get_pose(self):
        try:
            transform = self.tf_buffer.lookup_transform(
                target_frame="world_0", 
                source_frame="tool", 
                time=rclpy.time.Time()
            )

            t = transform.transform.translation
            self.current_position = np.array([[float(t.x)], [float(t.y)], [float(t.z)]])

            
        except (LookupException, ConnectivityException, ExtrapolationException):
            self.get_logger().warn("TF tree failed")
        

def main():
    rclpy.init(args=None)
    node = Astar3DNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

        

        
        