import numpy as np
import matplotlib.pyplot as plt
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu
from icecream import ic
import time
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from mavros_msgs.msg import SysStatus


#? Recomendations for the future me:
    #? - Try multithread this

def quaternion_to_euler(x: float, y: float, z: float, w: float) -> np.ndarray:

    # roll (x-axis rotation)
    t0 = 2.0 * (w * x + y * z)
    t1 = 1.0 - 2.0 * (x * x + y * y)
    roll = np.arctan2(t0, t1)

    # pitch (y-axis rotation)
    t2 = 2.0 * (w * y - z * x)
    t2 = np.clip(t2, -1.0, 1.0)
    pitch = np.arcsin(t2)

    # yaw (z-axis rotation)
    t3 = 2.0 * (w * z + x * y)
    t4 = 1.0 - 2.0 * (y * y + z * z)
    yaw = np.arctan2(t3, t4)

    return np.array([[roll], [pitch], [yaw]], dtype=float)

def HTransform(roll: float, pitch: float, yaw: float, pose : np.array) -> np.ndarray:
    cr = np.cos(roll);  sr = np.sin(roll)
    cp = np.cos(pitch); sp = np.sin(pitch)
    cy = np.cos(yaw);   sy = np.sin(yaw)

    T = np.array([
        [cy*cp,            cy*sp*sr - sy*cr,  cy*sp*cr + sy*sr, pose[0][0]],
        [sy*cp,            sy*sp*sr + cy*cr,  sy*sp*cr - cy*sr, pose[1][0]],
        [-sp,                         cp*sr,             cp*cr, pose[2][0]],
        [0,                               0,                 0,          1]], dtype=float)
    return T

class GUINode(Node):
    def __init__(self):
        super().__init__("gui_node")
        self.plt_width = 100
        self.plt_height = 30

        self.declare_parameter('robot_width', 0.3)
        self.declare_parameter('robot_height', 0.2)
        self.declare_parameter('robot_depht', 0.3)
        
        self.declare_parameter('viewer_width', 1.0)
        self.declare_parameter('viewer_height', 1.0)
        self.declare_parameter('viewer_depht', 1.0)
        
        #! Robot plot parameters
        self.robot_width = self.get_parameter('robot_width').value
        self.robot_height = self.get_parameter('robot_height').value
        self.robot_depht = self.get_parameter('robot_depht').value

        self.robot_plot_max_width = self.get_parameter('viewer_width').value
        self.robot_plot_max_height = self.get_parameter('viewer_height').value
        self.robot_plot_max_depht = self.get_parameter('viewer_depht').value

        self.robot_point_description = np.array([[0,self.robot_width,self.robot_width,                0,                 0,                 0,  self.robot_width, self.robot_width],
                                                 [0,               0,self.robot_depht, self.robot_depht,  self.robot_depht,                 0,                 0, self.robot_depht],
                                                 [0,               0,               0,                0, self.robot_height, self.robot_height, self.robot_height, self.robot_height]])

        #! Robot Dynamic parameters
        self.robot_position_odom = None
        self.current_description = None
        
        self.robot_current_orientation = np.array([[0.], [0.], [0.]])
        self.robot_first_orientation = np.array([[0.], [0.], [0.]])
        self.first_pose_flag = None
        self.battery_current = 0.
        self.battery_voltage = 0.

        #! Subscriptors && Timers for visualization
        qos = QoSProfile(depth=10,
                         reliability=ReliabilityPolicy.BEST_EFFORT,
                         history=HistoryPolicy.KEEP_LAST)

        self.pose_subscription = self.create_subscription(
            Imu,
            "/mavros/imu/data",
            self.positon_subs_callback,
            qos_profile=qos
        )
        
        self.current_subscription = self.create_subscription(
            SysStatus,
            "/mavros/sys_status",
            self.system_subs_callback,
            qos_profile=qos
        )
        
        
        self.create_timer(0.1, self.position_plot)
        self.create_timer(0.1, self.odom_update)

        #! Plotting elements
        self.plt_fig = plt.figure()
        self.plt_fig.canvas.manager.set_window_title("ROV visualization")
        self.plt_ax = self.plt_fig.add_subplot(2,2,(2,4),projection="3d")
        self.bat_ax = self.plt_fig.add_subplot(2,2,1)
        self.curr_ax = self.plt_fig.add_subplot(2,2,3)
        
        self.test_counter = 0

        
    
    def odom_update(self):
        T = HTransform(self.robot_current_orientation[0][0],self.robot_current_orientation[1][0],self.robot_current_orientation[2][0],np.array([[0.],[0],[0]]))
        self.current_description = np.zeros((np.size(self.robot_point_description,0) + 1, #! The extra dimension takes the homogeneus side into consideration
                                        np.size(self.robot_point_description,1)))
        for ii in range(8):
            self.current_description[:,ii] =  T @ np.hstack((self.robot_point_description[:,ii]
                                                        ,np.array([1.])))
        self.test_counter += 0.1
    
    def position_plot(self):
        if self.current_description is not None:
            self.plt_ax.cla()
            self.plt_ax.set_xlabel("x [m]")
            self.plt_ax.set_ylabel("Y [m]")
            self.plt_ax.set_zlabel("Z [m]")
            self.plt_ax.set_title("Orientation Visualization")
 
            self.plt_ax.plot3D(self.current_description[0,:],
                                self.current_description[1,:],
                                self.current_description[2,:], linewidth=4, color='blue')
            plt.draw()
            
            self.bat_ax.cla()
            self.bat_ax.bar("ROV battery voltage [mV]", self.battery_voltage, color='yellow', edgecolor='black', width=0.6)
            self.bat_ax.set_title("ROV power state")
            
            self.curr_ax.cla()
            self.curr_ax.bar("ROV current consumption [mA]", self.battery_current*10, color='red', edgecolor='black', width=0.6)
            
            plt.pause(0.2)  # Small pause so GUI can update
        

    def positon_subs_callback(self, msg : Imu):
        if self.first_pose_flag is None:
            self.robot_first_orientation =  quaternion_to_euler(msg.orientation.x,
                                                                    msg.orientation.y,
                                                                    msg.orientation.z,
                                                                    msg.orientation.w)
            self.first_pose_flag = 1.
        else:
            self.robot_current_orientation = quaternion_to_euler(msg.orientation.x,
                                                                    msg.orientation.y,
                                                                    msg.orientation.z,
                                                                    msg.orientation.w) - self.robot_first_orientation
            
            # ic("Updated", self.robot_current_orientation)
            
    def system_subs_callback(self, msg : SysStatus):
        self.battery_current = float(msg.current_battery)
        self.battery_voltage = float(msg.voltage_battery)
        # ic("Updated")

        
def main():
    ic("Executed")
    rclpy.init(args=None)
    plotter_node = GUINode()
    ic("Executing")
    try:
        rclpy.spin(plotter_node)
        ic("Tried to plot")
    except Exception as e:
        ic("Exeption exploted", e)
        time.sleep(0.5)
    finally:
        rclpy.shutdown()
        ic("Finished")
        
    

if __name__ == '__main__':
    main()
        
        
        
