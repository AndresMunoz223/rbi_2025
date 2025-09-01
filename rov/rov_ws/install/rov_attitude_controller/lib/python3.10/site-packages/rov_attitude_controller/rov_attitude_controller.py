import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist

from tf2_ros import Buffer, TransformListener
from geometry_msgs.msg import TransformStamped
from sensor_msgs.msg import Imu

from tf2_ros import LookupException, ConnectivityException, ExtrapolationException
from icecream import ic
import time


import numpy as np
from numpy import isnan, isinf

ic.disable()

if not hasattr(np, "float"):
    np.float = float

def quaternion_to_euler(qx, qy, qz, qw):
    """
    Convert quaternion (x, y, z, w) into Euler angles (roll, pitch, yaw).

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
        
        self.init_time = 0.
        self.continuous_time = 0.
        
        self.integral = None



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
        self.error = self.sp - y
        self.integral += (time.time() - self.init_time)*self.error
        
        self.u = self.kp*self.error + self.ki*self.integral
        self.init_time = time.time()
        return self.u
    

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
        
        #! Creating suscriptions
        self.cmd_subs = self.create_subscription(Twist, "/cmd_vel", self.cmd_vel_callback, 10)
        self.imu_subs = self.create_subscription(Imu, "/imu/data", self.imu_callback, 10)
        
        
        #! Publishers
        self.cmd_vel_pub = self.create_publisher(Twist, "/rov/cmd_vel", 10)
        
        #! Timers
        self.odom_timer = self.create_timer(0.1, self.get_robot_pose)


        #! tf tree buffers & Listerner
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)


        #! Control-realted setpoints and stuff
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

        #! Select natural depht 
        self.depht_controller.setpoint(self.z_set_point_)


    def cmd_vel_callback(self, msg : Twist):
        """
        
        Get the feed-forward terms and depht set-point from /rov/cmd_vel msgs
        
        Parameters
        ----------
        None
        
        Returns
        ----------
        None
        
        """
        
        self.u_action_ = msg.linear.x
        self.yaw_action_ = msg.angular.z
        self.z_set_point_ = msg.linear.z
        
        self.depht_controller.setpoint(self.z_set_point_)
        
        
    def imu_callback(self, msg : Imu):
        """
        
        Get the Acceleration and angular rates from the IMU
        
        Parameters
        ------------
        Imu msg
        
        
        Returns 
        ------------
        None
        
        """
        
        self.imu_accel = msg.linear_acceleration
        self.imu_ang_vel = msg.angular_velocity
            

    def get_robot_pose(self):
        """
            Get robot pose from tf tree.
            
            Gets the robot's relative position against the world map.
            
            Parameters
            ----------
            None
            
            
            Returns
            ----------
            None
        
        """
        try:
            transform = self.tf_buffer.lookup_transform(
                target_frame="odom", 
                source_frame="base_link", 
                time=rclpy.time.Time()
            )

            #! Get the transformation from the map's frame (Translation)
            t = transform.transform.translation
            self.position = np.array([float(t.x), float(t.y), float(t.z)])

         
            #! Get the transformation from the map's frame (Orientation)
            q = transform.transform.rotation
            yaw, pitch, roll = quaternion_to_euler(q.x, q.y, q.z, q.w)

            self.orientation = [roll, pitch, yaw]

            #! Generate the attitude controler response            
            if self.u_action_ is not None and self.yaw_action_ is not None:

                msg = Twist()
                
                #! Transform the reference to the local frame,avoiding singularities
                roll, pitch = self.transorm_angle_set_point() 

                roll_action = self.roll_controller.get_discr_u(roll)
                pitch_action = self.pitch_controller.get_discr_u(pitch)
                z_action_ = self.depht_controller.get_discr_u(self.position[2])

                #! Under the proposed conditions, the system seems to be naturally stable.
                msg.angular.x = roll_action
                msg.angular.y = pitch_action
                msg.linear.z = z_action_


                #! Forward terms (The controller will correct for these)
                msg.linear.x = self.u_action_
                msg.angular.z = self.yaw_action_
                
                #! Publish the actions
                self.cmd_vel_pub.publish(msg)

        #? Raise exceptions, in case of no available tf tree
        except (LookupException, ConnectivityException, ExtrapolationException):
            self.get_logger().warn("TF tree failed")
            pass

    def transorm_angle_set_point(self):
        """
            Get the Current state in the local reference frame.
            
            This function get's the current orientation from imu data, generating a local frame representation of orientation.
        
            Parameters
            ----------
            None
            
            Returns
            ----------
            None
        
        """
        
        if self.imu_accel is not None and self.imu_ang_vel is not None:
            corrected_roll_angle = np.arctan2(self.imu_accel.y, np.sqrt(self.imu_accel.x**2 + self.imu_accel.z**2))
            corrected_pitch_angle = np.arctan2(-self.imu_accel.x, np.sqrt(self.imu_accel.y**2 + self.imu_accel.z**2))
            return corrected_roll_angle,  corrected_pitch_angle
            
            
        
    
    

#! Main for spinning the node
def main():
    rclpy.init(args=None)
    node = AttitudeController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()