#pragma once
#include "vector"
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

#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/twist.hpp"
#include "eigen3/Eigen/Dense"
#include "std_msgs/msg/float32_multi_array.hpp"

#include <CppLinuxSerial/SerialPort.hpp>

//! Ros2 control stuff....
#include "hardware_interface/system_interface.hpp" //! -> system for simplicity.

using namespace mn::CppLinuxSerial;

using FloatArray32 = std_msgs::msg::Float32MultiArray;



namespace scara_hardware_layer {

class ScaraHardwareInterface : public hardware_interface::SystemInterface
{
   
    public:

    ~ScaraHardwareInterface();

    hardware_interface::CallbackReturn
        on_configure(const rclcpp_lifecycle::State & previus_state) override;
    hardware_interface::CallbackReturn
        on_activate(const rclcpp_lifecycle::State & previus_state) override;
    hardware_interface::CallbackReturn
        on_deactivate(const rclcpp_lifecycle::State & previus_state) override;

    hardware_interface::CallbackReturn
        on_init(const hardware_interface::HardwareInfo &info) override;
    hardware_interface::return_type
        read(const rclcpp::Time & time, const rclcpp::Duration & period) override;
    hardware_interface::return_type
        write(const rclcpp::Time & time, const rclcpp::Duration & period) override;

    std::vector<hardware_interface::StateInterface>
        export_state_interfaces() override;
    
    std::vector<hardware_interface::CommandInterface>
        export_command_interfaces() override;
    void    
        cleanup();

    private:
        std::array<double, 4> joint_positions_;
        std::array<double, 4> joint_position_targets_;
        SerialPort serial_port_;
        std::string delimiter = "|";

    //! --------------------------------------------

};

}