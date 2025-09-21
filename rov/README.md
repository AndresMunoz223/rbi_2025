# ROV - AUV

## Description

This folder contains the project files for the EIA's autonomous underwater vehicle.

You'll find among the contents of this folder:

* PCB Related files for the electronics manufacturing and set-up.
* All related simulation files, including the whole ROS2 structure interfacing with MuJoCo.
* All CAD files and auxiliary information for manufacturing.
* Test, callibration, and major activities performed.

# Setting up simulations

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

# Robot proposed structure
