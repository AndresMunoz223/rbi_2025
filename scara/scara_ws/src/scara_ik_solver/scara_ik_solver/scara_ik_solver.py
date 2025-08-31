import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
from geometry_msgs.msg import PoseStamped
import numpy as np
from icecream import ic

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
    def __init__(self, l1, l2, thetha_1_bounds=[62, -62], thetha_2_bounds=[100, -100], z_bounds=[0.3, 0]):
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


class IkSolverNode(Node):
    def __init__(self):
        super().__init__("ik_solver_node")
        self.declare_parameter("link_1_lenght", 0.210)
        self.declare_parameter("link_2_lenght", 0.250)
        
        l1_lenght = self.get_parameter("link_1_lenght").get_parameter_value().double_value
        l2_lenght = self.get_parameter("link_2_lenght").get_parameter_value().double_value
        self.ik_solver = IkSolverScara(l1=l1_lenght, l2=l2_lenght)
        
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