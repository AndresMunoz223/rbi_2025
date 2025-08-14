#pragma once
#include "vector"
#include "mujoco.h"
#include "GLFW/glfw3.h"
#include "stdio.h"
#include "stdlib.h"
#include "string.h"
#include <stdbool.h> 
#include <math.h>
#include <thread>
#include <cstdio>
#include <chrono>
#include <functional>
#include <memory>
#include <string>
#include <vector>
#include <iostream>
#include <atomic>
#include <mujoco/mjvisualize.h> // For mjVISFLAG_* and mjtVisFlag
#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/twist.hpp"

//! Ros2 control stuff....
#include "hardware_interface/system_interface.hpp" //! -> system for simplicity.