
#* Revisión de la instalación de MuJoCo
try:
  import mujoco
  mujoco.MjModel.from_xml_string('<mujoco/>')
except Exception as e:
  raise e from RuntimeError(
      'Algo salio mal en la instalación (pip install mujoco, e intentalo denuevo)')

#!-------------------------------------------------------------------- 

#* Importe de librerías necesarias para la simulación
import time
import threading
import numpy as np
from math import cos, sin


#* Librerías de calidad de vida
import os
from glob import glob
from ament_index_python.packages import get_package_share_directory
from icecream import ic


#* rclpy y relacionados a ros2    
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped

#* Plot y datos
import matplotlib.pyplot as plt
import cv2 

#* Little funky funny library
from terminaltexteffects.effects.effect_beams import Beams


#! ------------------------Descripción del robót--------------------------

package_name = 'scara_mujoco' #* Nombre del paquete.

#* Importamos la descripción del paquete.
MJCF = os.path.join(get_package_share_directory(package_name),'descriptions','basic_scenario.xml') 

#!---------------------------------------------------------------------------------

#* Función de apoyo, de angulos de euler a quaternión.
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



#* Clase del simulador, heredamos de Node.
class MujocoSimulator(Node):
    def __init__(self, Description):
        super().__init__('simulator_abb') #! Definimos el nombre del simulador

        #! Suscriptores y publicadores
        self.subs_motor_goal_angle = self.create_subscription(Float32MultiArray, "/motor_goal_angle", self.motor_goal_angle_callback,10)
        self.odometry_pub = self.create_publisher(Odometry, "/end_efector_odom", 10)

        #! Temporizador para la odometría
        self.create_timer(0.1, self.odometry_publisher)


        #* Simulator Parámetros de simulación
        self.simulation_object = mujoco.MjModel.from_xml_path(Description)
        self.simulation_data = mujoco.MjData(self.simulation_object)
        self.render_height = 480
        self.render_width = 480
        self.video_fps = 60
        self.sim_time = 30
        self.simulation_object.opt.timestep = 0.005
        self.motor_goal_angle_arr = []

        #! Parámetros del robót
        self.pose_array = []
        self.world_frame = 'world_frame'
        self.tool_frame = 'tool_frame'
        self.tool_odom = [0., 0., 0., 0., 0., 0., 0.]
        


    #! Callback, setpoint de los motores
    def motor_goal_angle_callback(self, msg):
        self.motor_goal_angle_arr = msg.data

    #! Publicador de la odometría
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


    #! Inicio de la simulación, thread distinto.
    def start_sim(self):

        n_frames = self.sim_time*self.video_fps

        #* reseteamos la simulación
        mujoco.mj_resetData(self.simulation_object, self.simulation_data)

        #* pasamos los parámetros al objeto render
        with mujoco.Renderer(self.simulation_object, self.render_height, self.render_width) as renderer:
            renderer._scene_option.flags[mujoco.mjtVisFlag.mjVIS_RANGEFINDER] = False
            renderer._scene_option.flags[mujoco.mjtVisFlag.mjVIS_TRANSPARENT] = True
            renderer._scene_option.frame = mujoco.mjtFrame.mjFRAME_BODY

            #* Ejecutamos en el tiempo establecido
            for i in range(n_frames):

                #* Propagamos la simulación por el tiempo que indiquen los parámetros del GUI
                while self.simulation_data.time < i/self.video_fps:
                    mujoco.mj_step(self.simulation_object, self.simulation_data)

                #* Asignamos un setpoint sinusoidal arbitrario
                self.simulation_data.ctrl[0] = np.sin(self.simulation_data.time)*2.
                self.simulation_data.ctrl[1] = np.sin(self.simulation_data.time)*0.5
                self.simulation_data.ctrl[2] = np.sin(self.simulation_data.time)*0.5
                self.simulation_data.ctrl[3] = -np.abs(np.sin(self.simulation_data.time)*0.2)
                

                #* Guardamos las joint positions
                self.pose_array = self.simulation_data.qpos

                # ic(self.pose_array)

                ic(self.simulation_data.geom_xpos[self.simulation_data.geom("fourth_joint_geom").id].copy())

                #! Mostramos en pantalla
                renderer.update_scene(self.simulation_data, "fixed")
                img_frame = renderer.render()
                img_frame = cv2.cvtColor(img_frame,cv2.COLOR_BGR2RGB)
                cv2.imshow("Global",img_frame)
                cv2.waitKey(25) & 0xFF == ord('q') # Exit if 'q' is pressed
        
            cv2.destroyAllWindows()



def main():
    #* Iniciamos rclpy
    rclpy.init(args=None)
    #* Creamos el nodo
    simulator = MujocoSimulator(MJCF)

    #! ---------------Ejecutamos la simulación --------------------
    t = threading.Thread(target=simulator.start_sim, args=())
    t.start()
    #! ------------------------------------------------------------

    #* Matamos el simulador
    rclpy.spin(simulator)
    simulator.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()