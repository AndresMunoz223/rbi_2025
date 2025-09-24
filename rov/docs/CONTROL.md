# Control proposal

## ROV - AUV simplified model

Considering that the system behaves as a 6 DOF body, the necessary description for its behaviour its extracted from a simplified dynamic model, proposed as follows:

<img src="../media/control/Diagrama_Caja_Negra.png" height="180"/>

It was desired to arrange the actuators on the system so the final structure has 5 DOF directly actuated, conviniently dividing the system into a QuadCopter-Like and Differential-thrust systems.

<img src="../media/control/rov_diagram.png" height="280"/>

Simplifying the system in this way makes the control task straightforward.

## Position controller




### Further simplifications

Considering that the motors response its way faster than the overalls system's dynamics, they can be considered as having no dynamics. 