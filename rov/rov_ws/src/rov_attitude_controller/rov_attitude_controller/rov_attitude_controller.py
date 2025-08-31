import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist

from tf2_ros import Buffer, TransformListener
from geometry_msgs.msg import TransformStamped
from sensor_msgs.msg import Imu

from tf2_ros import LookupException, ConnectivityException, ExtrapolationException
from icecream import ic

import numpy as np
from numpy import isnan, isinf

ic.disable()

if not hasattr(np, "float"):
    np.float = float

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
    def __init__(self, kp, ki, kd, Ts=None): # use Ts in case of discrete controller
        # cont. gains
        self.update_gains(kp, ki, kd, Ts)
        self.error = [0.0, 0.0, 0.0] #* ek, ek-1, ek-2
        self.uk = [0.0, 0.0] #* uk, uk-1
        self.sp = 0.

    # define setpoint
    def setpoint(self, sp):
        self.sp = sp

    ## discrete control law
    def get_discr_u(self, y): # y is the measured variable
        # compute error and control signal
        self.error[0] = self.sp - y
        self.uk[0] = self.q0*self.error[0] + self.q1*self.error[1] + self.q2*self.error[2] + self.uk[1]
        
        if isnan(self.uk[0]):
            self.uk[0] = 0.0

        # update register variables
        self.uk[1] = self.uk[0]
        self.error[1] = self.error[0]
        self.error[2] = self.error[1]

        # send control signal
        return self.uk[0] 
    

    # continuous control law
    def get_cont_u(self, y):
        # TODO: develop this method in case the user wants a continuous controller
        # self.error = self.sp - y
        # self.u = self.kp*self.error + self.ki*self.integral + self.kd*self.dedt
        # return self.u
        pass

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
    def satur(self, minu, maxu, u):
        if u < minu: return minu
        elif u > maxu: return maxu
        else: return u


class AttitudeController(Node):
    def __init__(self):
        super().__init__("attitude_controller")
        self.cmd_subs = self.create_subscription(Twist, "/cmd_vel", self.cmd_vel_callback, 10)
        self.imu_subs = self.create_subscription(Imu, "/imu/data", self.imu_callback, 10)

        self.cmd_vel_pub = self.create_publisher(Twist, "/rov/cmd_vel", 10)
        
        self.odom_timer = self.create_timer(0.1, self.get_robot_pose)

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.z_set_point_ = 2.

        self.u_action_ = 0.
        self.yaw_action_ = 0.
        self.roll_action_ = None
        self.pitch_action_ = None
        self.base_link_end_effector_translation_tf = None
        
        self.imu_accel = None
        self.imu_ang_vel = None

        self.position = None
        self.orientation = None

        self.roll_controller = ControllerPID(2, 0.1, 0., 0.1)
        self.pitch_controller = ControllerPID(2, 0.4, 0., 0.1)
        self.depht_controller = ControllerPID(3, 0.15, 0., 0.1)

        self.depht_controller.setpoint(self.z_set_point_)


    def cmd_vel_callback(self, msg : Twist):
        self.u_action_ = msg.linear.x
        self.yaw_action_ = msg.angular.z
        self.z_set_point_ = msg.linear.z
        ic(self.z_set_point_)
        
        self.depht_controller.setpoint(self.z_set_point_)
        
        
    def imu_callback(self, msg : Imu):
        self.imu_accel = msg.linear_acceleration
        self.imu_ang_vel = msg.angular_velocity
            

    def get_robot_pose(self):
        try:
            transform = self.tf_buffer.lookup_transform(
                target_frame="odom", 
                source_frame="base_link", 
                time=rclpy.time.Time()
            )

            # Translation
            t = transform.transform.translation
            self.position = np.array([float(t.x), float(t.y), float(t.z)])

            # Orientation (quaternion → euler)
            q = transform.transform.rotation
            yaw, pitch, roll = quaternion_to_euler(q.x, q.y, q.z, q.w)

            # ic(self.position,self.orientation)

            self.orientation = [roll, pitch, yaw]
            
            if self.u_action_ is not None and self.yaw_action_ is not None:

                msg = Twist()
                
                roll, pitch = self.transorm_angle_set_point()

                roll_action = self.roll_controller.get_discr_u(roll)
                pitch_action = self.pitch_controller.get_discr_u(pitch)
                z_action_ = self.depht_controller.get_discr_u(self.position[2])

                # ic(roll_action,pitch_action,z_action_)
                # ic(roll, pitch, self.position[2])

                #! Under the proposed conditions, the system seems to be naturally stable

                msg.angular.x = roll_action
                msg.angular.y = pitch_action
                
                msg.linear.z = z_action_

                msg.linear.x = self.u_action_
                msg.angular.z = self.yaw_action_
                
                
                self.cmd_vel_pub.publish(msg)


        except (LookupException, ConnectivityException, ExtrapolationException):
            self.get_logger().warn("TF tree failed")
            pass

    def transorm_angle_set_point(self):
        #* The main idea with this function is to change the angle reference, for us, fo define the control
        #* in such a way to avoid singularities.
        
        if self.imu_accel is not None and self.imu_ang_vel is not None:
            corrected_roll_angle = np.arctan2(self.imu_accel.y, np.sqrt(self.imu_accel.x**2 + self.imu_accel.z**2))
            corrected_pitch_angle = np.arctan2(-self.imu_accel.x, np.sqrt(self.imu_accel.y**2 + self.imu_accel.z**2))
            return corrected_roll_angle,  corrected_pitch_angle
            
            
        
    
    


def main():
    rclpy.init(args=None)
    node = AttitudeController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()