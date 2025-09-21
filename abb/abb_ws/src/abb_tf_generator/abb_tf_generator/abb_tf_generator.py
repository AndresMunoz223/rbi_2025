#!/usr/bin/env python3
import rclpy
from rclpy.node import Node

from std_msgs.msg import Float32MultiArray
from geometry_msgs.msg import TransformStamped
import tf2_ros
import numpy as np
from icecream import ic

np.set_printoptions(precision=4, suppress=True) 

dh_params = np.array([[   0,        0, 0.342,     0],
                      [  90,  0.06988,     0,    90],
                      [   0,    0.362,     0,    0],
                      [  90,       0,    0.380,   0],
                      [ -90,        0,     0,    0],
                      [  90,         0, 0.25,   90]], dtype=float)

DEG_TO_RAD = np.pi/180

import numpy as np

def rotation_matrix_to_quaternion(R: np.ndarray):
    """
    Convert a 3x3 rotation matrix to quaternion [x, y, z, w].
    """
    assert R.shape == (3, 3), "R must be a 3x3 matrix"

    q = np.zeros(4)
    trace = np.trace(R)

    if trace > 0:
        s = 0.5 / np.sqrt(trace + 1.0)
        q[3] = 0.25 / s
        q[0] = (R[2, 1] - R[1, 2]) * s
        q[1] = (R[0, 2] - R[2, 0]) * s
        q[2] = (R[1, 0] - R[0, 1]) * s
    else:
        if (R[0, 0] > R[1, 1]) and (R[0, 0] > R[2, 2]):
            s = 2.0 * np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2])
            q[3] = (R[2, 1] - R[1, 2]) / s
            q[0] = 0.25 * s
            q[1] = (R[0, 1] + R[1, 0]) / s
            q[2] = (R[0, 2] + R[2, 0]) / s
        elif R[1, 1] > R[2, 2]:
            s = 2.0 * np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2])
            q[3] = (R[0, 2] - R[2, 0]) / s
            q[0] = (R[0, 1] + R[1, 0]) / s
            q[1] = 0.25 * s
            q[2] = (R[1, 2] + R[2, 1]) / s
        else:
            s = 2.0 * np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1])
            q[3] = (R[1, 0] - R[0, 1]) / s
            q[0] = (R[0, 2] + R[2, 0]) / s
            q[1] = (R[1, 2] + R[2, 1]) / s
            q[2] = 0.25 * s

    # Normalize to unit quaternion
    q = q / np.linalg.norm(q)
    return q  # [x, y, z, w]

class IkSolverScara():
    def __init__(self, l1, l2, thetha_1_bounds=[359, -359], thetha_2_bounds=[359, -359]):
        self.l1 = l1
        self.l2 = l2
        self.theta_1_bounds = thetha_1_bounds
        self.theta_2_bounds = thetha_2_bounds
        self.prev_theta_2 = 1.
        ic(f"Robot configured with : {self.l1, self.l2, self.theta_1_bounds, self.theta_2_bounds}")
        
        #!Implemente los bound check de z, no se le olvide :)

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
        self.d = 0.165
        
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


class JointToTFNode(Node):
    def __init__(self):
        super().__init__("joint_to_tf_node")

        self.dh_params = dh_params
        self.solver = ABBKinematics(dh_matrix=self.dh_params)

        # Subscriber to joint positions
        self.subscription = self.create_subscription(
            Float32MultiArray,
            "/ABBController/current_joint_pos",
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
                                 [msg.data[3]/DEG_TO_RAD],
                                 [msg.data[4]/DEG_TO_RAD],
                                 [msg.data[5]/DEG_TO_RAD]])

        transform = self.solver.get_fk(6, current_pose)

        
        q = rotation_matrix_to_quaternion(transform[0:3,0:3])

        
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = "world_0"        
        t.child_frame_id = "tool"          

        t.transform.translation.x = float(transform[0][3])
        t.transform.translation.y = float(transform[1][3])
        t.transform.translation.z = float(transform[2][3]) #! Compensate the initial elevation
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
