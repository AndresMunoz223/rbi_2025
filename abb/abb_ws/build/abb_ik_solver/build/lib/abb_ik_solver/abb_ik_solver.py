import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
from geometry_msgs.msg import PoseStamped
import numpy as np
from icecream import ic
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster
from builtin_interfaces.msg import Time

ic.disable()

np.set_printoptions(precision=4, suppress=True) 

dh_params = np.array([[   0,        0, 0.342,     0],
                      [  90,  0.06988,     0,    90],
                      [   0,    0.362,     0,    0],
                      [  90,       0,    0.380,   0],
                      [ -90,        0,     0,    0],
                      [  90,         0, 0.25,   90]], dtype=float)

DEG_TO_RAD = np.pi/180

class IkSolverScara():
    def __init__(self, l1, l2, thetha_1_bounds=[359, -359], thetha_2_bounds=[359, -359]):
        self.l1 = l1
        self.l2 = l2
        self.theta_1_bounds = thetha_1_bounds
        self.theta_2_bounds = thetha_2_bounds
        self.prev_theta_2 = 1.
        ic(f"Robot configured with : {self.l1, self.l2, self.theta_1_bounds, self.theta_2_bounds}")
        
        #!Note for yo, pues, yo hago esta chimbada. Implemente los bound check de z, no se le olvide :)

    def solve_for_pose(self, pose : np.array):
        x = pose[0][0]
        y = pose[1][0]
        
        r = np.sqrt(x**2 + y**2)
        d = (r**2 - self.l1**2 - self.l2**2)/(2*self.l1*self.l2)
        
        theta_2 = -np.arctan2(np.sqrt(1 - d**2),d)
        theta_1 = np.arctan2(y,x) - np.arctan2(np.sin(theta_2)*self.l2,(self.l1 + np.cos(theta_2)*self.l2)) 
        
        if theta_1 > self.theta_1_bounds[0] or theta_1 < self.theta_1_bounds[1]:
            ic("Limits reached [Theta_1]")
            return None
        if theta_2 > self.theta_2_bounds[0] or theta_2 < self.theta_2_bounds[1]:
            ic("Limits reached [Theta_2]")
            return None

        return theta_1, theta_2

class ABBKinematics():
    def __init__(self, dh_matrix : np.array):
        self.dh_matrix = dh_matrix
        self.current_joint_pos = None
        self.d = 0.25
        
        self.inner_2r_solver = IkSolverScara(l1=0.362,l2=0.380)


#! Basic transformations

    def x_translation(self, x : float) -> np.array:
        return np.array([[1, 0, 0, x],
                         [0, 1, 0, 0],
                         [0, 0, 1, 0],
                         [0, 0, 0, 1]], dtype=float)

    def x_rotation(self, alpha : float) -> np.array:
        return np.array([[1,             0,              0, 0],
                         [0, np.cos(alpha*DEG_TO_RAD), -np.sin(alpha*DEG_TO_RAD), 0],
                         [0, np.sin(alpha*DEG_TO_RAD),  np.cos(alpha*DEG_TO_RAD), 0],
                         [0,             0,              0, 1]], dtype=float)
    
    def z_translation(self, z : float) -> np.array:
        return np.array([[1, 0, 0, 0],
                         [0, 1, 0, 0],
                         [0, 0, 1, z],
                         [0, 0, 0, 1]], dtype=float)
    

    def z_rotation(self, theta: float) -> np.array:
        return np.array([[np.cos(theta*DEG_TO_RAD),-np.sin(theta*DEG_TO_RAD), 0, 0],
                         [np.sin(theta*DEG_TO_RAD), np.cos(theta*DEG_TO_RAD), 0, 0],
                         [            0,             0, 1, 0],
                         [            0,             0, 0, 1]], dtype=float)

    def euler_to_rotation_matrix(self, roll, pitch, yaw):
        
        cx, cy, cz = np.cos(roll*DEG_TO_RAD), np.cos(pitch*DEG_TO_RAD), np.cos(yaw*DEG_TO_RAD)
        sx, sy, sz = np.sin(roll*DEG_TO_RAD), np.sin(pitch*DEG_TO_RAD), np.sin(yaw*DEG_TO_RAD)

        R = np.array([
            [cz*cy, cz*sy*sx - sz*cx, cz*sy*cx + sz*sx],
            [sz*cy, sz*sy*sx + cz*cx, sz*sy*cx - cz*sx],
            [-sy,   cy*sx,             cy*cx]
        ])
        return R


#! ------------------------

    def get_fk(self, link_index : int, current_pose : np.array):
        
        current_pose_array = np.array([[   0,         0,    0.,  current_pose[0][0]],
                                        [  0,       0.,     0,   current_pose[1][0]],
                                        [  0,       0.,     0,   current_pose[2][0]],
                                        [  0,       0.,     0,   current_pose[3][0]],
                                        [  0,        0,     0,   current_pose[4][0]],
                                        [  0,        0,    0.,   current_pose[5][0]]], dtype=float)
        
        current_origin = np.array([[1, 0, 0, 0],
                                   [0, 1, 0, 0],
                                   [0, 0, 1, 0],
                                   [0, 0, 0, 1]], dtype=float)
        
        current_dh = self.dh_matrix + current_pose_array
        
        for i in range(link_index):
            current_origin = current_origin @ self.x_rotation(current_dh[i][0]) @ self.x_translation(current_dh[i][1])  @ self.z_translation(current_dh[i][2]) @ self.z_rotation(current_dh[i][3])            
            
        return current_origin
    
    def get_ik(self, goal_pose : np.array):
        
        R_0_6 = self.euler_to_rotation_matrix(goal_pose[3][0], goal_pose[4][0], goal_pose[5][0])
        
        p_m = np.array([[goal_pose[0][0] - self.d*R_0_6[0][2]],
                        [goal_pose[1][0] - self.d*R_0_6[1][2]],
                        [goal_pose[2][0] - self.d*R_0_6[2][2]]])

        ic(p_m, R_0_6)
        
        #! Just the orientation, quite easy
        theta_1 = np.arctan2(p_m[1][0], p_m[0][0])
        # Second option 
        #theta_1 = np.arctan2(goal_pose[1][0], goal_pose[0][0]) + np.pi
        
        
        #! Now here it comes the "Scara", just treat it like a 2R. Had to adjust for deviation
        x_p = np.sqrt((self.dh_matrix[1][1] - p_m[0][0])**2 + p_m[1][0]**2)
        y_p = p_m[2][0] - self.dh_matrix[0][2]
        
        pose_p = np.array([[x_p],
                           [y_p]])
        
        ic(pose_p)
        
        R = np.array([[np.cos(np.pi/2), -np.sin(np.pi/2)],
                      [np.sin(np.pi/2), np.cos(np.pi/2)]])
        
        pose_p = R.T @ pose_p
        
        ic(pose_p)
        
        theta_2, theta_3 =  self.inner_2r_solver.solve_for_pose(pose_p)
        
        #! Correct for reference
        theta_3 += np.pi/2
        
        current_pos = np.array([[theta_1/DEG_TO_RAD], [theta_2/DEG_TO_RAD], [theta_3/DEG_TO_RAD], [0.], [0.], [0.]])
        
        ic(current_pos)
        
        transform_link_3 = self.get_fk(4, current_pos)
        
        ic(transform_link_3)
        
        R_0_3 = transform_link_3[0:3,0:3]
        
        R_3_6 = R_0_3.T @ R_0_6
        
        theta_4 = np.arctan2(R_3_6[1][2], R_3_6[0][2])
        theta_5 = np.arctan2(np.sqrt(1 - R_3_6[2][2]**2), R_3_6[2][2])
        theta_6 = np.arctan2(R_3_6[2][1], -R_3_6[2][0])
        
        ic(np.array([[theta_1], [theta_2], [theta_3], [theta_4], [theta_5], [theta_6]]))
        
        return np.array([[theta_1], [theta_2], [theta_3], [theta_4], [theta_5], [theta_6]])

def quat_to_euler(q):
    """
    Convert a quaternion [x, y, z, w] into Euler angles (roll, pitch, yaw).
    Returns roll, pitch, yaw in radians.
    """
    x, y, z, w = q

    # Normalize
    norm = np.linalg.norm([x, y, z, w])
    if norm == 0:
        raise ValueError("Zero-norm quaternion is invalid.")
    x, y, z, w = x / norm, y / norm, z / norm, w / norm

    # Roll (x-axis rotation)
    sinr_cosp = 2 * (w * x + y * z)
    cosr_cosp = 1 - 2 * (x * x + y * y)
    roll = np.arctan2(sinr_cosp, cosr_cosp)

    # Pitch (y-axis rotation)
    sinp = 2 * (w * y - z * x)
    pitch = np.arcsin(np.clip(sinp, -1, 1))

    # Yaw (z-axis rotation)
    siny_cosp = 2 * (w * z + x * y)
    cosy_cosp = 1 - 2 * (y * y + z * z)
    yaw = np.arctan2(siny_cosp, cosy_cosp)

    return roll, pitch, yaw

class IkSolverNode(Node):
    def __init__(self):
        super().__init__("ik_solver_node")
        self.dh_params = dh_params

        self.solver = ABBKinematics(dh_matrix=self.dh_params)
        self.goal_pose = None

        # self.pose_subs = self.create_subscription(Float64MultiArray, "/ABBController/current_joint_pos", self.data_subs_callback, 10)        
        self.pose_subs = self.create_subscription(PoseStamped, "/abb/path/goal_pose", self.goal_pose_callback, 10)
        self.joint_pub = self.create_publisher(Float32MultiArray, "/ABBController/desired_joint_pos", 10)
        
        self.current_pose = None
    
    def goal_pose_callback(self, msg : PoseStamped):
        
        roll, pitch, yaw = quat_to_euler([msg.pose.orientation.x, msg.pose.orientation.y, msg.pose.orientation.z, msg.pose.orientation.w])

        #! We'll later worry about the orientation
        desired_pose = np.array([[msg.pose.position.x],
                                 [msg.pose.position.y],
                                 [msg.pose.position.z],
                                 
                                 [0/DEG_TO_RAD],
                                 [np.pi/2/DEG_TO_RAD],
                                 [0*yaw/DEG_TO_RAD]])
        
    

        self.goal_positions = self.solver.get_ik(desired_pose)
        
        msg = Float32MultiArray()
        
        # #! Mujoco
        # msg.data = [self.goal_positions[0][0],
        #                   self.goal_positions[1][0],
        #                   self.goal_positions[2][0],
        #                   self.goal_positions[3][0],
        #                   self.goal_positions[4][0],
        #                   self.goal_positions[5][0]]


        # ! GZ
        msg.data = [self.goal_positions[0][0],
                          -self.goal_positions[1][0],
                          -self.goal_positions[2][0],
                          self.goal_positions[3][0],
                          -self.goal_positions[4][0],
                          self.goal_positions[5][0]]

        ic(msg.data)

        self.joint_pub.publish(msg)

def main():
    rclpy.init(args=None)
    node = IkSolverNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()