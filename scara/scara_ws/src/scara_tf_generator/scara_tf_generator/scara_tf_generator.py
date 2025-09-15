#!/usr/bin/env python3
import rclpy
from rclpy.node import Node

from std_msgs.msg import Float32MultiArray
from geometry_msgs.msg import TransformStamped
import tf2_ros
import numpy as np
from icecream import ic

np.set_printoptions(precision=4, suppress=True) 


dh_params = np.array([[   0,        0, 0.254,     0],
                      [   0,    0.210,     0,     0],
                      [   0,    0.250,     0,     0],
                      [   0,        0,     0,     0],], dtype=float)

DEG_TO_RAD = np.pi/180

#! Usé chatg para esta función, la verdad la pude haber importado de Otro paquete, pero la vddad no era tan relevante en el momento. :|
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
        self.prev_theta_2 = 1.
        ic(f"Robot configured with : {self.l1, self.l2, self.theta_1_bounds, self.theta_2_bounds}")

        self.dh_matrix = dh_matrix

    def solve_for_pose(self, pose : np.array):
        x = pose[0][0]
        y = pose[1][0]
        z = pose[2][0]
        phi = pose[3][0]
        
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
        
        if np.sign(self.prev_theta_2) != np.sign(theta_2):
            self.prev_theta_2 = theta_2
            return np.array([[0], [0], [z + 0.05], [phi]])

        return np.array([[theta_1], [theta_2], [z + 0.05], [phi]])

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



class JointToTFNode(Node):
    def __init__(self):
        super().__init__("joint_to_tf_node")

        self.dh_params = dh_params

        self.declare_parameter("link_1_lenght", 0.210)
        self.declare_parameter("link_2_lenght", 0.250)
        
        l1_lenght = self.get_parameter("link_1_lenght").get_parameter_value().double_value
        l2_lenght = self.get_parameter("link_2_lenght").get_parameter_value().double_value
        self.ik_solver = IkSolverScara(l1=l1_lenght, l2=l2_lenght, dh_matrix=self.dh_params)
                
        # Subscriber to joint positions
        self.subscription = self.create_subscription(
            Float32MultiArray,
            "/ScaraController/current_joint_pos",
            self.joint_callback,
            10,
        )

        # TF broadcaster
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)
        self.get_logger().info("JointToTFNode started. Listening for joint positions...")

    def joint_callback(self, msg: Float32MultiArray):
        if len(msg.data) < 6:
            self.get_logger().warn("Received joint array with less than 6 elements.")
            return

        current_pose = np.array([[msg.data[0]/DEG_TO_RAD],
                                 [msg.data[1]/DEG_TO_RAD],
                                 [msg.data[2]/DEG_TO_RAD],
                                 [msg.data[3]/DEG_TO_RAD]])

        transform = self.solver.get_fk(3, current_pose)

        q = rotation_matrix_to_quaternion(transform[0:3,0:3])
        
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = "world_0"        
        t.child_frame_id = "tool"          

        t.transform.translation.x = float(transform[0][3])
        t.transform.translation.y = float(transform[1][3])
        t.transform.translation.z = float(transform[2][3])
        t.transform.rotation.x = float(q[0])
        t.transform.rotation.y = float(q[1])
        t.transform.rotation.z = float(q[2])
        t.transform.rotation.w = float(q[3])

        # Broadcast TF
        self.tf_broadcaster.sendTransform(t)


def main(args=None):
    rclpy.init(args=args)
    node = JointToTFNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
