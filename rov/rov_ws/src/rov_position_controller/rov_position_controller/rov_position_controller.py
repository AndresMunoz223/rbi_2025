import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist

from tf2_ros import Buffer, TransformListener
from geometry_msgs.msg import TransformStamped
from sensor_msgs.msg import Imu
from geometry_msgs.msg import PoseStamped

from tf2_ros import LookupException, ConnectivityException, ExtrapolationException
from icecream import ic

import numpy as np
from numpy import isnan, isinf

ic.disable()

#! Aux stuff to get there :)
def quaternion_to_euler(qx, qy, qz, qw):
    """
    Convert quaternion (x, y, z, w) into Euler angles (roll, pitch, yaw).
    Roll  -> rotation around x-axis
    Pitch -> rotation around y-axis
    Yaw   -> rotation around z-axis
    Returns angles in radians.
    """
    # Roll (x-axis rotation)
    sinr_cosp = 2.0 * (qw * qx + qy * qz)
    cosr_cosp = 1.0 - 2.0 * (qx * qx + qy * qy)
    roll = np.arctan2(sinr_cosp, cosr_cosp)

    # Pitch (y-axis rotation)
    sinp = 2.0 * (qw * qy - qz * qx)
    if abs(sinp) >= 1:
        pitch = np.pi/2 * np.sign(sinp)  # use 90° if out of range
    else:
        pitch = np.arcsin(sinp)

    # Yaw (z-axis rotation)
    siny_cosp = 2.0 * (qw * qz + qx * qy)
    cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz)
    yaw = np.arctan2(siny_cosp, cosy_cosp)

    return roll, pitch, yaw
    
class ControllerPID():
    def __init__(self, kp, ki, kd, Ts=None, u_min=-np.inf , u_max=-np.inf ): # use Ts in case of discrete controller
        # cont. gains
        self.update_gains(kp, ki, kd, Ts)
        self.error = [0.0, 0.0, 0.0] #* ek, ek-1, ek-2
        self.uk = [0.0, 0.0] #* uk, uk-1
        self.sp = 0.
        self.u_max = u_max
        self.u_min = u_min

    # define setpoint
    def setpoint(self, sp):
        self.sp = sp

    ## discrete control law
    def get_discr_u(self, error): # y is the measured variable
        # compute error and control signal
        self.error[0] = error
        self.uk[0] = self.q0*self.error[0] + self.q1*self.error[1] + self.q2*self.error[2] + self.uk[1]
        
        if isnan(self.uk[0]):
            self.uk[0] = 0.0

        # update register variables
        self.uk[1] = self.uk[0]
        self.error[1] = self.error[0]
        self.error[2] = self.error[1]

        # send control signal
        self.uk[0] = self.satur(self.uk[0])
        return self.uk[0] 
    

    def update_discr_gains(self):
        ti = self.kp/self.ki
        td = self.kd/self.kp
        # compute discr. gains
        self.q0 = self.kp*(1 + self.Ts/(2*ti) + td/self.Ts)
        self.q1 = self.kp*(self.Ts/(2*ti) - 2*td/self.Ts - 1)
        self.q2 = self.kp*(td/self.Ts)
        print(f'updated discr gains: {self.q0} {self.q1} {self.q2}')

    def update_gains(self, kp, ki, kd, Ts=None):
        self.kp = kp
        self.ki = ki
        self.kd = kd

        self.Ts = Ts

        if isinstance(Ts, (int, float)):
            self.update_discr_gains()
        else:
            self.q0 = 0.0
            self.q1 = 0.0
            self.q2 = 0.0           

    ## saturate control law
    def satur(self, u):
        if u < self.u_min : return self.u_min 
        elif u > self.u_max : return self.u_max 
        else: return u

#! ------------------------------

class PositionController(Node):
    def __init__(self):
        super().__init__("attitude_controller")

        self.cmd_vel_pub = self.create_publisher(Twist, "/cmd_vel", 10)
        self.controller_timer = self.create_timer(0.1, self.controller_timer)
        
        self.goal_pose_subs = self.create_subscription(PoseStamped, "/rov/goal_pose", self.goal_pose_callback, 10)

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.u_action_ = None
        self.yaw_action_ = None
        
        self.goal_pose = None

        self.base_link_end_effector_translation_tf = None
        
        self.imu_accel = None
        self.imu_ang_vel = None

        self.position = None
        self.orientation = None

        self.forward_controller = ControllerPID(0.5, 0.05, 0., 0.1, u_min=0., u_max= 1.)
        self.turn_controller = ControllerPID(1.5, 0.05, 0., 0.1, u_min=-2., u_max= 2.)

        self.k1 = 2.

    def goal_pose_callback(self, msg : PoseStamped):
        self.goal_pose = msg.pose.position
        ic(self.goal_pose)
        

    def controller_timer(self):
        try:
            transform = self.tf_buffer.lookup_transform(
                target_frame="odom", 
                source_frame="base_link", 
                time=rclpy.time.Time()
            )

            # Translation
            t = transform.transform.translation

            # Orientation (quaternion → euler)
            q = transform.transform.rotation
            yaw, pitch, roll = quaternion_to_euler(q.x, q.y, q.z, q.w)
                        
            self.position = np.array([float(t.x), float(t.y), float(t.z)])
            self.orientation = np.array([[np.cos(yaw)], [np.sin(yaw)]])
            
            if self.goal_pose is not None:
                
                y_error = self.goal_pose.y - self.position[1]
                x_error = self.goal_pose.x - self.position[0]

                error_planar_vector = np.array([[x_error , y_error]])
                error_planar_vector = error_planar_vector/np.linalg.norm(error_planar_vector)

                angle = np.arccos(np.dot(error_planar_vector,self.orientation))
                x_local = np.cos(-yaw)*error_planar_vector[0][0] - np.sin(-yaw)*error_planar_vector[0][1]
                y_local = np.sin(-yaw)*error_planar_vector[0][0] + np.cos(-yaw)*error_planar_vector[0][1]

                angle_sign = np.sign(-y_local)

                angle_to_element = angle*angle_sign
                
                ic(x_local, y_local)
                ic(angle_sign)                

                u_action_ = self.forward_controller.get_discr_u(np.sqrt(y_error**2 + x_error**2))
                yaw_action_ = self.turn_controller.get_discr_u(angle_to_element)
                
                msg = Twist()
                
                if np.abs(np.sqrt(x_error**2 + y_error**2)) > 0.1:    
                    msg.linear.x = float(u_action_/(1 + np.abs(yaw_action_)*self.k1))
                    msg.angular.z = -float(yaw_action_)
                    msg.linear.z = self.goal_pose.z
                    self.cmd_vel_pub.publish(msg)
                
                else:
                    msg.linear.z = self.goal_pose.z
                    self.cmd_vel_pub.publish(msg)
                
        except (LookupException, ConnectivityException, ExtrapolationException):
            self.get_logger().warn("TF tree failed")
            pass
        
        

def main():
    rclpy.init(args=None)
    node = PositionController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()