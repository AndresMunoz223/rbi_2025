# SCARA

# Definition

An SCARA robot (Selective-Compliance Articulated), is a disctinct type of robot manipulator widely used in the industry. The SCARA robot usually takes the configuration of a 2RP manipulator, used for pick and place tasks. Theese kind of robots rely in repeatability and acuracy on their movements.

In the EIA's University an SCARA robot sits at student's disposition, it uses 2 Servomotors *Schneider BSH0551T32A2A*, along with 2 *Schneider LMX32* drivers to interface with them. For its 3rd and fourth DOFS, the SCARA uses 2 *Nema 23HS30-2804S* stepper motors, connected with gears and a rack-pinion mechanism to achieve the translation and rotation of the end-effector.

A brief showcase of the elements is presented as follows:

| Element              | Ammount | Refference        |
| -------------------- | ------- | ----------------- |
| Servomotors          | 2       | BSH0551T32A2A     |
| Servomotor Drivers   | 2       | LMX32             |
| Stepper Motors       | 2       | Nema 23HS30-2804S |
| CAN Interface Driver | 1       |                   |
| Esp32                | 1       | WROOM32D          |

# Robot cabinet and its structure

Inside the robot's side cabinet, an arrange of components can be found, among them we have the main protection circuits, 12V power supplies, the stepper drivers, and the ESP32 circuit.

## Esp32 Circuit

The esp32 circuit inside the cabbinet uses the CAN interface to command the Servomotors through the CANopen protocol. It configures and comands the servomotor with read-write instructions.

# Associated DH parameters

| Link index | a-1[m] | alpha-1[°] | s[m]  | theta[°] |
| ---------- | ------ | ----------- | ----- | --------- |
| 1          | 0      | 0           | 0.254 | 0         |
| 2          | 0.210  | 0           | 0     | 0         |
| 3          | 0.250  | 0           | 0     | 0         |
| 4          | 0      | 0           | 0     | 0         |
