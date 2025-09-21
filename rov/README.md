# ROV - AUV

## Description

This folder contains the project files for the EIA's autonomous underwater vehicle.

You'll find among the contents of this folder:

* PCB Related files for the electronics manufacturing and set-up.
* All related simulation files, including the whole ROS2 structure interfacing with MuJoCo.
* All CAD files and auxiliary information for manufacturing.
* Test, callibration, and major activities performed.

# Robot overall structure

The robot is proposed as a 6 thruster underwater vehicle, with direct actuation over its forward-backward and up-down displacement, and mayor axis rotation capabilities, effectively becoming a 5 DOF robot.

<img src="media/CAD_view_1.png" width="300" height="260"/>

<img src="media/CAD_view_2.png" width="300" height="260"/>

<img src="media/CAD_view_3.png" width="380" height="260"/>

<img src="media/CAD_view_4.png" width="380" height="260"/>

The desing was created over a 4 inch PVC pipe hull for simplycity and impermeabilization effectiveness.

The **Electronics&Devices BOM** is found bellow ***(STILL IN DEVELOPMENT)***:

| Function                                          | Element                         | Qtty | Lik                                                                                                                                                                                                       | Status                   |
| ------------------------------------------------- | ------------------------------- | ---- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| Vertical thruster                                 | BM70 Brushed Submarine Thruster | 4    | **[Amazon](https://www.amazon.com/-/es/BM70/dp/B0BF5KZVPN/ref=sr_1_6?crid=MQD4XE0IY6RU&keywords=underwater%2Bthruster&qid=1706275905&sprefix=underwater%2Bthru%2Caps%2C182&sr=8-6&th=1 "Z motors link")** | Bought                   |
| Forward thrusters                                 |                                 | 2    |                                                                                                                                                                                                           | Bought                   |
| Running node structure                            | Raspberry Pi 5 - 8Gb            | 1    |                                                                                                                                                                                                           | Available at institution |
| Inertial variables mesuring/Forward motor control | PiXHAWK module                  | 1    |                                                                                                                                                                                                           | Available at institution |
| Vertical thruster control                         | Project PCB                     | 1    |                                                                                                                                                                                                           | Available at institution |
| Vehicle operation                                 | Generic joystick                | 1    |                                                                                                                                                                                                           | Available at institution |

For a deeper sight into the design process and manufacturing , go [here](docs/DESIGN.md "design and manufacturing process").

# Simulating the ROV - AUV on MuJoCo

The ROV-AUV simulator was built over ROS2, in integration with MuJoCo by ros2_control hardware interfaces.

The generated node structure is shown bellow:

<img src="media/ros2_node_structure.png" width="800" height="240"/>

Inside the node structure, two main componens are to be highlighted, `attitude_controller` and `path_follower` nodes. Both nodes handle the lower and highter level control tasks, stabilizing the system and commanding it to follow the desired path. The necessary information for control tasks is sent by the `/imu` topic and `/tf` .

For further description on the control proposal go [here](docs/CONTROL.md "control description").

---

The ROS2 structure is ment to be run inside a docker container by using vscode *[dev containers](https://code.visualstudio.com/docs/devcontainers/containers)* tools.

To run the simulation, reopen the rov_ws folder inside a dev container and build the simulator:

```shell
colcon build 
```

Then:

```shell
ros2 launch rov_mujoco_bringup rov_bringup_launch.launch.xml
```

The expected result should be:

<img src="media/simulator_main_screen.png" width="400" height="240"/>

With the following listed ros2_control hardware interfaces and controllers:

<img src="media/active_controller.png" width="400" height="18"/>

<img src="media/active_interfaces.png" width="400" height="350"/>

## Testing simulations

Once the simulator has started, you can interact with the rober by posting msgs into the `/goal_pose topic`.

To try it out in terminal, manually publish the goal pose:

```shell
ros2 topic pub /goal_pose geometry_msgs/msg/PoseStamped "{
  header: {
    stamp: {sec: 0, nanosec: 0},
    frame_id: 'world'
  },
  pose: {
    position: {x: 4., y: 0.0, z: 4.},
    orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}
  }
}" --once

```

Once the node structure recieves the msg, the following should happen on rviz2, as the simulator advances:

<img src="media/rviz_view.png" width="700" height="400"/>

In the rviz2 visualization, the generated path trajectory is displayed in green, as the traversed path generates with red color. the respective coordinate system transformations will also be displayed on screen.

<img src="media/rviz_view_description.png" width="500" height="400"/>

# System testing, assembling and tunning

On the system printing, assembling and tunning, the team is currently testing the PCB design output and corrobotating identified motor current curves.

<img src="media/manufacturing/electronics_testing.jpeg" width="550" height="400"/>
