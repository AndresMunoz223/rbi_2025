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
#include "eigen3/Eigen/Dense"


//! Ros2 control stuff....
#include "hardware_interface/system_interface.hpp" //! -> system for simplicity.

char filename[] = "/home/eia/rbi_2025/abb/abb_ws/src/abb_mujoco_sim/description/abb.xml";

namespace abb_simulator_layer {

class AbbSimulatorInterface : public hardware_interface::SystemInterface
{
    public:

    mjvCamera sim_cam;                      // abstract camera
    mjvOption sim_opt;                      // visualization options
    mjvScene sim_scn;                       // abstract scene
    mjrContext sim_con;    

    ~AbbSimulatorInterface();

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
        start_sim();

    void
        sim_thread();

    void    
        cleanup();

    private:

    //! Sim related vars
    std::atomic<bool> sim_stop_flag;
    std::thread simulation_thread_;
    char err_string[1000] = "Could not load binary model";

    mjModel* sim_model_object = NULL;
    mjData* sim_data_object = NULL;

    const std::string body_name = "hull_link";
    int hull_name_id;

    std::array<double, 6> motor_positions_{};
    std::array<double, 6> motor_commands_{};

    //! --------------------------------------------

};

}