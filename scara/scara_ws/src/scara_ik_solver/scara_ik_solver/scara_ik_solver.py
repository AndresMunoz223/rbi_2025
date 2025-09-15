import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
from geometry_msgs.msg import PoseStamped
import numpy as np
from icecream import ic

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

np.set_printoptions(precision=4, suppress=True) 


dh_params = np.array([[   0,        0, 0.254,     0],
                      [   0,    0.210,     0,     0],
                      [   0,    0.250,     0,     0],
                      [   0,        0,     0,     0],], dtype=float)

DEG_TO_RAD = np.pi/180

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


class IkSolverScara():
    def __init__(self, l1, l2, dh_matrix, thetha_1_bounds=[62, -62], thetha_2_bounds=[100, -100], z_bounds=[0.3, 0]):
        self.l1 = l1
        self.l2 = l2
        self.theta_1_bounds = thetha_1_bounds
        self.theta_2_bounds = thetha_2_bounds
        self.prev_theta_2 = 0.
        self.prev_theta_1 = 0.
        ic(f"Robot configured with : {self.l1, self.l2, self.theta_1_bounds, self.theta_2_bounds}")

        self.dh_matrix = dh_matrix

    def solve_for_pose(self, pose : np.array):
        x = pose[0][0]
        y = pose[1][0]
        z = pose[2][0] - 0.254
        phi = pose[3][0]
        
        r = np.sqrt(np.power(x,2) + np.power(y,2))
        d = (np.power(r,2) - np.power(self.l1,2) - np.power(self.l2,2))/(2*self.l1*self.l2)
        
        theta_2 = -np.arctan2(np.sqrt(1 - np.power(d,2)),d)
        theta_1 = np.arctan2(y,x) - np.arctan2(np.sin(theta_2)*self.l2,(self.l1 + np.cos(theta_2)*self.l2)) 
        
        if theta_1 > self.theta_1_bounds[0] or theta_1 < self.theta_1_bounds[1]:
            ic("Limits reached [Theta_1]")
            return None
        if theta_2 > self.theta_2_bounds[0] or theta_2 < self.theta_2_bounds[1]:
            ic("Limits reached [Theta_2]")
            return None
        
        pose = self.get_fk(3, np.array([[theta_1/DEG_TO_RAD], [theta_2/DEG_TO_RAD], [z], [phi/DEG_TO_RAD]]))
        
        # ic(pose)
        
        _, _, yaw = self.rotation_matrix_to_euler(pose[0:3,0:3])

        # theta_1_delta = self.prev_theta_1 - theta_1
        # theta_2_delta = self.prev_theta_2 - theta_2
        # if np.abs(theta_1_delta) >= 10*DEG_TO_RAD or np.abs(theta_2_delta) >= 10*DEG_TO_RAD :
        #     ic(theta_1_delta/DEG_TO_RAD)
        #     ic(theta_2_delta/DEG_TO_RAD)

        
        # self.prev_theta_1 = theta_1
        # self.prev_theta_2 = theta_2


        return np.array([[theta_1], [theta_2], [phi - yaw], [z]])

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

    def rotation_matrix_to_euler(self, R: np.array):
        
        if np.isclose(R[2,0], -1.0):
            pitch = np.pi / 2
            roll = np.arctan2(R[0,1], R[0,2])
            yaw = 0.0
        elif np.isclose(R[2,0], 1.0):
            pitch = -np.pi / 2
            roll = np.arctan2(-R[0,1], -R[0,2])
            yaw = 0.0
        else:
            pitch = -np.arcsin(R[2,0])
            roll = np.arctan2(R[2,1]/np.cos(pitch), R[2,2]/np.cos(pitch))
            yaw = np.arctan2(R[1,0]/np.cos(pitch), R[0,0]/np.cos(pitch))

        return roll, pitch, yaw


#! ------------------------

    def get_fk(self, link_index : int, current_pose : np.array):
        
        current_pose_array = np.array([[   0,        0,                     0,    current_pose[0][0]],
                                        [  0,       0.,                      0,   current_pose[1][0]],
                                        [  0,       0.,     current_pose[2][0],                    0],
                                        [  0,       0.,                      0,   current_pose[3][0]]], dtype=float)
        
        current_origin = np.array([[1, 0, 0, 0],
                                   [0, 1, 0, 0],
                                   [0, 0, 1, 0],
                                   [0, 0, 0, 1]], dtype=float)
        
        current_dh = self.dh_matrix + current_pose_array
        
        for i in range(link_index):
            current_origin = current_origin @ self.x_rotation(current_dh[i][0]) @ self.x_translation(current_dh[i][1])  @ self.z_translation(current_dh[i][2]) @ self.z_rotation(current_dh[i][3])            
            
        return current_origin

class IkSolverNode(Node):
    def __init__(self):
        super().__init__("ik_solver_node")
        self.declare_parameter("link_1_lenght", 0.210)
        self.declare_parameter("link_2_lenght", 0.250)
        
        l1_lenght = self.get_parameter("link_1_lenght").get_parameter_value().double_value
        l2_lenght = self.get_parameter("link_2_lenght").get_parameter_value().double_value
        self.ik_solver = IkSolverScara(l1=l1_lenght, l2=l2_lenght, dh_matrix=dh_params)
        
        self.pose_subs = self.create_subscription(PoseStamped, "/scara/path/goal_pose", self.goal_pose_callback, 10)
        self.joint_pub = self.create_publisher(Float64MultiArray, "/arm_joints_controller/commands", 10)
        
    
    def goal_pose_callback(self, msg : PoseStamped):
        
        roll, pitch, yaw = quat_to_euler([msg.pose.orientation.x, msg.pose.orientation.y, msg.pose.orientation.z, msg.pose.orientation.w])
        
        desired_pose = np.array([[msg.pose.position.x], [msg.pose.position.y], [msg.pose.position.z], [yaw]])
        
        joint_coords = self.ik_solver.solve_for_pose(desired_pose)
        
        if joint_coords is not None:
            msg = Float64MultiArray()
            msg.data = [joint_coords[0][0], joint_coords[1][0], joint_coords[2][0], joint_coords[3][0]]
            # ic(msg.data)
            self.joint_pub.publish(msg)
        else:
            ic("Invalid point, solver failed")
        
        
        
        
        
        
        



def main():
    rclpy.init(args=None)
    node = IkSolverNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()