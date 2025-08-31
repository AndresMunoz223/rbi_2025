#ifndef ROVCONTROLLER
#define ROVCONTROLLER

#include <array>
#include <cmath>
#include <memory>
#include "rclcpp/rclcpp.hpp"
#include "controller_interface/controller_interface.hpp"
#include "geometry_msgs/msg/twist.hpp"
#include "eigen3/Eigen/Dense"
#include "eigen3/Eigen/Geometry"
#include "geometry_msgs/msg/transform_stamped.hpp"
#include "tf2_ros/transform_broadcaster.h"
#include "sensor_msgs/msg/imu.hpp"
#include "geometry_msgs/msg/vector3.hpp"
#include "rclcpp/create_timer.hpp"

using Twist = geometry_msgs::msg::Twist;

namespace rov_controller{

class RovController : public controller_interface::ControllerInterface{

public:

    RovController();

    controller_interface::CallbackReturn
    on_init() override;

    controller_interface::CallbackReturn
    on_configure(const rclcpp_lifecycle::State & previous_state) override;

    controller_interface::CallbackReturn
    on_activate(const rclcpp_lifecycle::State & previous_state) override;

    controller_interface::return_type
    update(const rclcpp::Time & time, const rclcpp::Duration & period) override;

    controller_interface::InterfaceConfiguration
    command_interface_configuration() const override;

    controller_interface::InterfaceConfiguration
    state_interface_configuration() const override;



    double u_cmd_;
    double z_cmd_;
    double pitch_cmd_;
    double roll_cmd_;
    double yaw_cmd_;

    Eigen::Matrix<double, 6, 6> target_forces_to_actuator_map;
    Eigen::Matrix<double, 6, 1> target_accel_to_forces_map;

    double hull_inertia_xx = 0.05;
    double hull_inertia_yy = 0.05;
    double hull_inertia_zz = 0.05;
    double hull_mass = 8.43;

    double hull_lw = 0.13;
    double hull_ld = 0.13;
    double hull_lb = 0.13;


    std::unique_ptr<tf2_ros::TransformBroadcaster> tf_broadcaster_;

    // IMU Publishers
    rclcpp::Publisher<sensor_msgs::msg::Imu>::SharedPtr imu_pub_;
    
    // IMU message objects
    sensor_msgs::msg::Imu imu_msg_;


protected:
    std::vector<std::string> joint_names_;
    std::string interface_name_;

    rclcpp::Subscription<Twist>::SharedPtr twist_subs_;
};

} // El szs

#endif