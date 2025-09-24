# Electronic desing

For this proyect, as using 4 DC brushed motors was required by the challenge, the motor driver array and microcontroller were integrated into a single PCB, and were taken as a single input-output system to further symplify the control flow structure.

A preview of the final design is shown bellow:

<img src="../media/pcb/pcb_final.jpeg" height="380"/>

## MCU

The chosen MCU for the motor control board was an STM32F401. The F401 series was chosen due to the availability of the device's explerimental board ([Nucleo-Board](https://www.st.com/en/evaluation-tools/nucleo-f401re.html)) in the EIA University, wich allowed for the early experimetation with STM32 boards. For a quick review on MCU descriptions and capabilites:

The STM32 MCU family offers different microcontrollers depending on the user's requierements, specifically depending on the aplication. Some information on different STM32 MCU types is displayed bellow, taken from the manufacturer *ST*.

<img src="../media/pcb/stm_32_selector.png" height="580"/>

More indepht information can be found in online guides as [this one](https://www.digikey.com/en/maker/tutorials/2020/understanding-stm32-naming-conventions) offered by DigiKey.

### STM32F401RE

Some of the capabilites of the selected MCU are listed bellow as an [ST-Infograpic](https://www.st.com/en/microcontrollers-microprocessors/stm32f401re.html).

<img src="../media/pcb/stm32f401_diag.png" height="380"/>

## Drivers

The motor driver choosed for this application was the [TB6612FNG](https://cdn.sparkfun.com/assets/0/1/b/b/3/TB6612FNG.pdf), manufactured by toshiba. The driver its is ment for controlling a dual DC motor set-up, with per-channel current limitation of up to $1.2 A$(avg) and $3.2 A$ peak. The driver also integrates integrated thermal shut-down.

The driver operates at a maximum motor voltage of $13.5V$, which allows for the $12V$ motor operational voltage, but the current restrictions generate a restriction on the motor's ussage that must be adressed. Describing the thermal properties of the device, maximum power dissipation stands at $1.36 W$.

The driver is commonly found in the form of a bread-board [module](https://www.sparkfun.com/sparkfun-motor-driver-dual-tb6612fng-1a.html):

<img src="../media/pcb/tb6612fng.png" height="180"/>

# Motor current identification

The motor used in the project, as previously stated, are [brushed CW waterproff off-the-shelve motors](https://www.amazon.com/-/es/BM70/dp/B0BF5KZVPN/ref=sr_1_6?crid=MQD4XE0IY6RU&keywords=underwater%2Bthruster&qid=1706275905&sprefix=underwater%2Bthru%2Caps%2C182&sr=8-6&th=1), which by early test drawed over 1.5 Amps at expected load operation. To make shure that the motor operation wont put at risk the motor drivers, the power output must be capped.

The current was identified by measuring the drawn current and plotting it against the control signal input:


<img src="../media/pcb/current_ident_curve.jpeg" height="180"/>

At the moment of testing, there wasnt available all 4 motor for identification, but considering the close response of the first two motors, it was safe to assume that the other pair would behave as expected.

# Programming & Testing

The pcb design was oriented towards creating a device wich would be interfaced with via VCP, and by the use of formatted strings, send motor actuation commands to the board. By using the available USB_driver from [Cube-IDE](https://www.st.com/en/development-tools/stm32cubeide.html), the board was quickly setted up, and test where performed on the resulting device.

Testing was performed at EIA's University Electronics lab, and current bounds and power consumption was again verified with the new set-up, and new motors.

![Video](../media/pcb/pcb_testing.mp4)