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

char filename[] = "/scara_ws/src/scara_mujoco_sim/description/scara.xml";

namespace scara_simulator_layer {

class ScaraSimulatorInterface : public hardware_interface::SystemInterface
{
    public:

    mjvCamera sim_cam;                      // abstract camera
    mjvOption sim_opt;                      // visualization options
    mjvScene sim_scn;                       // abstract scene
    mjrContext sim_con;    

    ~ScaraSimulatorInterface();

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

    std::array<double, 6> thruster_efforts_{};
    std::array<double, 6> thruster_commands_{};

    std::vector<double> free_joint_pos = {0., 0., 0.};
    Eigen::Quaterniond q;

    double u_input_;
    double z_input_;
    double roll_input_;
    double pitch_input_;
    double yaw_input_;
    //! --------------------------------------------

    Eigen::MatrixXd target_forces_to_actuator_map;
    Eigen::MatrixXd target_accel_to_forces_map;
    Eigen::MatrixXd set_point_to_accel_map;

    double hull_inertia_xx = 0.;
    double hull_inertia_yy = 0.;
    double hull_inertia_zz = 0.;
    double hull_mass = 0.;

    double f_1 = 0.;
    double f_2 = 0.;
    double f_3 = 0.;
    double f_4 = 0.;
    double f_5 = 0.;
    double f_6 = 0.;

    double mu_x = 0.;
    double mu_z = 0.;

    double hull_lw = 0.;
    double hull_ld = 0.;
    double hull_lb = 0.;

};

}