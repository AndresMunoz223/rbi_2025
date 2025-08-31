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

#include <CppLinuxSerial/SerialPort.hpp>

//! Ros2 control stuff....
#include "hardware_interface/system_interface.hpp" //! -> system for simplicity.

using namespace mn::CppLinuxSerial;

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
        start_controllers();

    void
        controller_thread();

    void    
        cleanup();

    private:


    std::array<double, 4> joint_positions_{};
    std::array<double, 4> actuator_commands_{};
    std::array<double, 4> joint_position_targets_{};
    SerialPort serial_port_;
    std::string delimiter = "|";

    std::thread simulation_thread_;

    //! --------------------------------------------

};

}