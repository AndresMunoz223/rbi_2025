import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
from geometry_msgs.msg import PoseStamped
import numpy as np
from icecream import ic


class ABBKinematics():
    def __init__(self, dh_matrix : np.array):
        self.dh_matrix = dh_matrix

#! Basic transformations

    def x_translation(self, x : float) -> np.array:
        return np.array([[1, 0, 0, x],
                         [0, 1, 0, 0],
                         [0, 0, 1, 0],
                         [0, 0, 0, 1]])

    def x_rotation(self, alpha : float) -> np.array:
        return np.array([[1,             0,              0, 0],
                         [0, np.cos(alpha), -np.sin(alpha), 0],
                         [0, np.sin(alpha),  np.cos(alpha), 0],
                         [0,             0,              0, 1]])
    
    def z_translation(self, z : float) -> np.array:
        return np.array([[1, 0, 0, 0],
                         [0, 1, 0, 0],
                         [0, 0, 1, z],
                         [0, 0, 0, 1]])
    
    def z_rotation(self, theta: float) -> np.array:
        return np.array([[np.cos(alpha),-np.sin(alpha), 0, 0],
                         [np.sin(alpha), np.cos(alpha), 0, 0],
                         [            0,             0, 0, 0],
                         [            0,             0, 0, 1]])

#! ------------------------

    def get_fk(self, link_index : int):
        current_origin = np.array([[0.], [0.], [0.], [0.]])
        for i in range(link_index):
            current_origin = x_translation(self.dh_matrix[link_index][0])*x_rotation(self.dh_matrix[link_index][1])*z_translation(self.dh_matrix[link_index][2])*z_rotation(self.dh_matrix[link_index][3])
        return current_origin
    
    def get_ik(self):
        pass




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

class IkSolverABB():
    def __init__(self, dh_parameters : np.array):
        self.dh_parameters = dh_parameters
        
        
    def solve_for_pose(self, pose : np.array):
        pass

class IkSolverNode(Node):
    def __init__(self):
        super().__init__("ik_solver_node")
        self.dh_params = np.array([[  0,       0, 1.202,   0],
                                   [ 90, 0.06988,     0,  90],
                                   [  0,   0.362,     0,  90],
                                   [  0,   0.380,     0, 180],
                                   [-90,       0,     0, 180],
                                   [-90,       0, 0.065, 180]])
        
        
        self.pose_subs = self.create_subscription(PoseStamped, "/goal_pose", self.goal_pose_callback, 10)
        self.joint_pub = self.create_publisher(Float64MultiArray, "/arm_joints_controller/commands", 10)
        
    
    def goal_pose_callback(self, msg : PoseStamped):
        
        roll, pitch, yaw = quat_to_euler([msg.pose.orientation.x, msg.pose.orientation.y, msg.pose.orientation.z, msg.pose.orientation.w])
        
        desired_pose = np.array([[msg.pose.position.x], [msg.pose.position.y], [msg.pose.position.z], [yaw]])
        
        joint_coords = self.ik_solver.solve_for_pose(desired_pose)
        
        if joint_coords is not None:
            msg = Float64MultiArray()
            msg.data = [joint_coords[0][0], joint_coords[1][0], joint_coords[2][0], joint_coords[3][0]]
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