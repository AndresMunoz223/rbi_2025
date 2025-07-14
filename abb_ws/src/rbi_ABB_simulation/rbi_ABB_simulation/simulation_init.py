try:
#   print('Revisando instalación....')
  import mujoco
  mujoco.MjModel.from_xml_string('<mujoco/>')
except Exception as e:
  raise e from RuntimeError(
      'Algo salio mal en la instalación (pip install mujoco)')


import time
import threading
import numpy as np
from math import cos, sin


import os
from glob import glob
from ament_index_python.packages import get_package_share_directory
from icecream import ic
# import keyboard

# Graphics and plotting.
import rclpy
from rclpy.node import Node

from std_msgs.msg import Float32MultiArray
from nav_msgs.msg import Odometry

from terminaltexteffects.effects.effect_beams import Beams


# ! Generating odometry
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped

import matplotlib.pyplot as plt
import cv2 
# mejores prints
np.set_printoptions(precision=3, suppress=True, linewidth=100)

#! ------------------------Descripción--------------------------

package_name = 'rbi_ABB_simulation'

MJCF = os.path.join(
                get_package_share_directory(package_name),'descriptions','basic_scenario.xml')

#!---------------------------------------------------------------------------------


def euler_to_quaternion(roll, pitch, yaw):
    """
    Converts Euler angles (roll, pitch, yaw) to a quaternion (x, y, z, w).

    Args:
        roll (float): Rotation around the x-axis (in radians).
        pitch (float): Rotation around the y-axis (in radians).
        yaw (float): Rotation around the z-axis (in radians).

    Returns:
        tuple: A tuple representing the quaternion (x, y, z, w).
    """

    cy = cos(yaw * 0.5)
    sy = sin(yaw * 0.5)
    cp = cos(pitch * 0.5)
    sp = sin(pitch * 0.5)
    cr = cos(roll * 0.5)
    sr = sin(roll * 0.5)

    w = cr * cp * cy + sr * sp * sy
    x = sr * cp * cy - cr * sp * sy
    y = cr * sp * cy + sr * cp * sy
    z = cr * cp * sy - sr * sp * cy

    return (x, y, z, w)


class MujocoSimulator(Node):
    def __init__(self, Description):
        super().__init__('simulator_abb')

        #! Subscribers and publishers
        self.subs_motor_goal_angle = self.create_subscription(Float32MultiArray, "/motor_goal_angle", self.motor_goal_angle_callback,10)
        self.odometry_pub = self.create_publisher(Odometry, "/end_efector_odom", 10)

        #! Odometry timer
        self.create_timer(0.1, self.odometry_publisher)


        #* Simulator parameters
        self.simulation_object = mujoco.MjModel.from_xml_path(Description)
        self.simulation_data = mujoco.MjData(self.simulation_object)
        self.render_height = 480
        self.render_width = 480
        self.video_fps = 60
        self.sim_time = 30
        self.simulation_object.opt.timestep = 0.005
        self.motor_goal_angle_arr = []

        #! Robot parameters
        self.pose_array = []

        self.world_frame = 'world_frame'
        self.tool_frame = 'tool_frame'

        self.tool_odom = [0., 0., 0., 0., 0., 0., 0.]
        

    def motor_goal_angle_callback(self, msg):
        self.motor_goal_angle_arr = msg.data

    def odometry_publisher(self):

        odom_msg = Odometry()

        odom_msg.header.stamp = self.get_clock().now().to_msg()
        odom_msg.header.frame_id = self.world_frame
        odom_msg.child_frame_id = self.tool_frame

        odom_msg.pose.pose.position.x = self.tool_odom[0]
        odom_msg.pose.pose.position.y = self.tool_odom[1]
        odom_msg.pose.pose.position.z = self.tool_odom[2]

        odom_msg.pose.pose.orientation.x = float(self.tool_odom[3])
        odom_msg.pose.pose.orientation.y = float(self.tool_odom[4])
        odom_msg.pose.pose.orientation.z = float(self.tool_odom[5])
        odom_msg.pose.pose.orientation.w = float(self.tool_odom[6])

        self.odometry_pub.publish(odom_msg)


    def start_sim(self):

        n_frames = self.sim_time*self.video_fps
        frames = []
        times = []
        sensordata = []

        #* Señal para nuestro motor
        mujoco.mj_resetData(self.simulation_object, self.simulation_data)

        with mujoco.Renderer(self.simulation_object, self.render_height, self.render_width) as renderer:
            renderer._scene_option.flags[mujoco.mjtVisFlag.mjVIS_RANGEFINDER] = False
            renderer._scene_option.flags[mujoco.mjtVisFlag.mjVIS_TRANSPARENT] = True
            renderer._scene_option.frame = mujoco.mjtFrame.mjFRAME_BODY

            for i in range(n_frames):
                
                while self.simulation_data.time < i/self.video_fps:
                    #* Propagate simulation
                    mujoco.mj_step(self.simulation_object, self.simulation_data)


                self.simulation_data.ctrl[0] = np.sin(self.simulation_data.time)*2.
                self.simulation_data.ctrl[1] = np.sin(self.simulation_data.time)*0.5
                self.simulation_data.ctrl[2] = np.sin(self.simulation_data.time)*0.5
                self.simulation_data.ctrl[3] = np.sin(self.simulation_data.time)*1.
                self.simulation_data.ctrl[4] = np.sin(self.simulation_data.time)*1.
                self.simulation_data.ctrl[5] = np.sin(self.simulation_data.time)*1.
                

                self.pose_array = self.simulation_data.qpos

                # ic(self.pose_array)

                ic(self.simulation_data.geom_xpos[self.simulation_data.geom("sixth_joint_geom").id].copy())

                renderer.update_scene(self.simulation_data, "fixed")

                img_frame = renderer.render()
                img_frame = cv2.cvtColor(img_frame,cv2.COLOR_BGR2RGB)

                cv2.imshow("Global",img_frame)
                cv2.waitKey(25) & 0xFF == ord('q') # Exit if 'q' is pressed
                
                # frames.append(frame)

            cv2.destroyAllWindows()



def main():
    rclpy.init(args=None)
    simulator = MujocoSimulator(MJCF)
    t = threading.Thread(target=simulator.start_sim, args=())
    t.start()
    rclpy.spin(simulator)
    simulator.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()