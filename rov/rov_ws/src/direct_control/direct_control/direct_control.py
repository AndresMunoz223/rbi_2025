import rclpy
from rclpy.node import Node
import serial
import time

from geometry_msgs.msg import Twist
from icecream import ic

import numpy as np

np.set_printoptions(precision=2)

class DirectControlNode(Node):
    def __init__(self):
        super().__init__("Direct_control")
        self.subscriber = self.create_subscription(Twist, "/cmd_vel", self.twist_callback,10)
        self.serial = serial.Serial("/dev/ttyACM1", 115200, timeout=1)  # Timeout of 1 second
        self.clock =self.create_timer(0.2,self.clock_szs)

    
        self.objective_forces = None
    
        self.forces_to_motors_direction_matrix = np.linalg.pinv(np.array([[1, 1, 0, 0, 0, 0],
                                                                    [0, 0, 0, 0, 0, 0],
                                                                    [0, 0, -1, -1, -1, -1],
                                                                    [0, 0, -1, -1, 1, 1],
                                                                    [0, 0, -1, 1, -1, 1],
                                                                    [1,-1, 0, 0, 0, 0,]]))

        self.motor_action_matrix = None

    def twist_callback(self, msg :Twist):
        self.objective_forces = np.array([[msg.linear.x],
                                          [msg.linear.y],
                                          [msg.linear.z],
                                          [msg.angular.x],
                                          [msg.angular.y],
                                          [msg.angular.z]])
        
        self.motor_action_matrix = self.forces_to_motors_direction_matrix @ self.objective_forces
        # ic(self.forces_to_motors_direction_matrix)
        # ic(self.motor_action_matrix)
        
        
    def clock_szs(self):
        if self.motor_action_matrix is not None:
            msg = f"{-self.motor_action_matrix[2][0]:.2f}|{-self.motor_action_matrix[3][0]:.2f}|{-self.motor_action_matrix[4][0]:.2f}|{-self.motor_action_matrix[5][0]:.2f}|{self.motor_action_matrix[0][0]:.2f}|{self.motor_action_matrix[1][0]:.2f}\n"
            self.serial.write(msg.encode())
            ic(msg)


def main():
    rclpy.init(args=None)
    node = DirectControlNode()
    try:
        rclpy.spin(node)
    except:
        node.serial.close()
    finally:
        node.serial.close()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()