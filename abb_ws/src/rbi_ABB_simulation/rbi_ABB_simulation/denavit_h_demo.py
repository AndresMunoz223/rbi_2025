try:
#   print('Revisando instalación....')
  import mujoco
  from dm_control import mjcf
  import dm_control
  mujoco.MjModel.from_xml_string('<mujoco/>')
except Exception as e:
  raise e from RuntimeError(
      'Algo salio mal en la instalación (pip install mujoco)')


import time
import threading
import numpy as np
from math import cos, sin
from icecream import ic


import os
from glob import glob
from ament_index_python.packages import get_package_share_directory


import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from sensor_msgs.msg import Imu

from terminaltexteffects.effects.effect_beams import Beams


# ! Generating odometry
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped
from dm_control.mujoco.wrapper.mjbindings import enums

import matplotlib.pyplot as plt
import cv2 
# mejores prints
np.set_printoptions(precision=3, suppress=True, linewidth=100)

#! ------------------------Descripción--------------------------

package_name = 'rbi_ABB_simulation'

MJCF = os.path.join(get_package_share_directory(package_name),'descriptions','basic_scenario.xml')


arena = mjcf.RootElement()

chequered = arena.asset.add('texture', type='2d', builtin='checker', width=300,
                            height=300, rgb1=[.2, .3, .4], rgb2=[.3, .4, .5])

grid = arena.asset.add('material', name='grid', texture=chequered,
                       texrepeat=[5, 5], reflectance=.2)

arena.worldbody.add('geom', type='plane', size=[10, 10, .1], material=grid)

arena.worldbody.add('camera',name="global_fixed_camera",
                 pos=[0, -8.0, 12],  # Position: e.g., 3 units back, 1.5 units up
                 euler=[45, 0, 0])    # Y-axis: [0 1 0] (points up)

#* ---------------------- Robot -----------------------------------------------------
spawn_pos = (0., 0., 0.)
spawn_site = arena.worldbody.add('site', pos=spawn_pos, group=3)

class Robot(object):
    def __init__(self, dh_matrix : np.array):
        length = 0.3

        self.model = mjcf.RootElement()
        self.model.default.joint.damping = 2
        self.model.default.joint.type = 'hinge'
        self.model.default.geom.type = 'capsule'
        self.model.default.geom.rgba = [1, 0., 0., 1]

        self.link_number = dh_matrix.shape[0]
        self.link_array = []
        self.position_array = []
        self.orientation_Arrat = []

        print(self.link_number)


        length = 1


        #!------------- Legacy ------------------

        # frame 0:
        # root_frame = self.model.worldbody.add('body')
        # # root_joint = root_frame.add('joint', axis = [0,0,1], type = 'hinge')

        self.models_arr = []
        num = 3
        for ii in range(num):
            
            new_model = mjcf.RootElement()
            new_model.default.joint.damping = 2
            new_model.default.joint.type = 'hinge'
            new_model.default.geom.type = 'capsule'
            new_model.default.geom.rgba = [1, 0.9*ii, 0., 1]

            new_frame = new_model.worldbody.add('body')
            new_frame.add('geom', fromto=[0, 0, 0, 0, 0, length], size=[length/4])
            new_joint = new_frame.add('joint', axis = [0,1,0])

            #Si es el ultimo en ser procesado se lo pegamos al mundo
            if ii == num - 1:
                site = self.model.worldbody.add('site', pos=[0, 0, 0], euler=[0, 0, 0])
                site.attach(new_model)
                self.models_arr.append(new_model)
                self.model.actuator.add('position', joint=new_joint, kp=10)
                print("Did last")
            elif ii == 0:
                print("Did first")
                self.models_arr.append(new_model)
            else:
                print("did mid")
                site = self.models_arr[ii - 1].worldbody.add('site', pos=[0, 0, length*(ii+1)], euler=[0, 0, 0])
                site.attach(new_model)
                self.models_arr[ii - 1].actuator.add('position', joint=new_joint, kp=10)
                self.models_arr.append(new_model)



        # # Thigh:
        # self.thigh = self.model.worldbody.add('body')
        # self.hip = self.thigh.add('joint', axis=[0, 0, 1])
        # self.thigh.add('geom', fromto=[0, 0, 0, length, 0, 0], size=[length/4])

        # # Hip:
        # self.shin = self.thigh.add('body', pos=[length, 0, 0])
        # self.knee = self.shin.add('joint', axis=[0, 1, 0])
        # self.shin.add('geom', fromto=[0, 0, 0, length, 0, length], size=[length/5])
        # # Position actuators:
        # self.model.actuator.add('position', joint=self.hip, kp=10)
        # self.model.actuator.add('position', joint=self.knee, kp=10)


a_01 = 0.1
a_12 = 0.1
s_1 = 0.1
s_4 = 0.1
s_6 = 0.1


                        #!  a, alpha, s, theta
dh_matrix = np.array([[0, a_01, s_1, 0],
                      [np.pi/2, a_12, 0, 0],
                      [0, 0, 0, np.pi/2],
                      [np.pi/2, 0, s_4, 0],
                      [-np.pi/2, 0, 0, np.pi],
                      [-np.pi/2, 0, s_6, np.pi]
                    ])

R1 = Robot(dh_matrix=dh_matrix)

spawn_site.attach(R1.model)

for x in [-2, 2]:
    arena.worldbody.add('light', pos=[x, -1, 3], dir=[-x, 1, -2])




#!---------------------------------------------------------------------------------



def euler_to_quaternion(roll, pitch, yaw):

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
        super().__init__('car_simulator')

        self.physics_object = mjcf.Physics.from_mjcf_model(arena)
        self.simulation_object = self.physics_object.model
        self.simulation_data = self.physics_object.data
        self.render_height = 480
        self.render_width = 480
        self.video_fps = 60
        self.sim_time = 30
        self.simulation_object.opt.timestep = 0.005





    def start_sim(self):
        #* Helper functs

        n_frames = self.sim_time*self.video_fps
        frames = []
        times = []
        sensordata = []
        try:
            for i in range(n_frames):
                
                while self.simulation_data.time < i/self.video_fps:
                    self.physics_object.step()
                
                scene_option = dm_control.mujoco.wrapper.core.MjvOption()
                scene_option.frame = enums.mjtFrame.mjFRAME_GEOM
                scene_option.flags[enums.mjtVisFlag.mjVIS_TRANSPARENT] = True
                scene_option.flags[enums.mjtVisFlag.mjVIS_JOINT] = True
                # scene_option.geomgroup[mujoco.mjtGeom.mjGEOM_ARROW] = 1

                img_frame = self.physics_object.render(width=self.render_width, height=self.render_height, camera_id="global_fixed_camera", scene_option=scene_option)

                img_frame = cv2.cvtColor(img_frame,cv2.COLOR_BGR2RGB)
                cv2.imshow("Global",img_frame)
                cv2.moveWindow("Global", 0, 0)

                cv2.waitKey(25) & 0xFF == ord('q') # Exit if 'q' is pressed
                # frames.append(frame)
        
            cv2.destroyAllWindows()
        except Exception as e:
            print(e)



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