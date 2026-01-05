# Repository purpose

This repository recalls my little journey inside ros2 development stack. If you find this, either by chance or due to Rozo's guidance, i expect that these projects will help you navigate this environment.

| Robot   | Description                            | Requirements                                                           | Concepts to apply                                                      | Readme                              |
| ------- | -------------------------------------- | ---------------------------------------------------------------------- | ---------------------------------------------------------------------- | ----------------------------------- |
| ABB     | Serial Manipulator 6 DOF (6R)          | - Ros2 Humble<br />- ros2_control + controllers<br />- gazebo ignition | - Trajectory planning<br />- Motion control<br />- Hardware interfaces | [ABB](./abb/README.md "abb readme")       |
| SCARA   | Serial Manipulator 4 DOF (2RPR)        | - Ros2 Humble<br />- ros2_control + controllers<br />- gazebo ignition | - Trajectory planning<br />- Motion control<br />- Hardware interfaces | [SCARA](./scara/README.md "scara readme") |
| AGV-EIA | Mecanum wheeled mobile robot           | - Ros2 Humble                                                          | - Obstacle avoidance<br />- Live mapping and navigation                | Private Pkg                         |
| ROV-EIA | Underactuated underwater vehicle 5 DOF | - Ros2 Humble<br />- ros2_control + controllers                        | - Trajectory planning in 3D<br />- Motion control in 5 DOF             | <br />[ROV](./rov/README.md "rov readme") |

> Table.1 Projects undertaken over this timespan


# ABB IRB140 robot (WIP)

<img src="media/ABB_robot.png" width="600" height="480"/>

> Fig.1 IRB140-ABB robot

# SCARA robot (WIP)

<img src="media/Scara_robot.png" width="600" height="480"/>

> Fig.2 EIA's In-house SCARA robot

# ROV-AUV robot (WIP)

<img src="media/Rov_robot.png" width="250" height="280"/>

<img src="media/Rov_robot_2.png" width="250" height="280"/>

> Fig.3 early prototype underwater vehicle