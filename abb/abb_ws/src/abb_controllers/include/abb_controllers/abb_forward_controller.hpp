#ifndef ABBCONTROLLER
#define ABBCONTROLLER

#include <array>
#include <cmath>
#include <memory>
#include "rclcpp/create_timer.hpp"
#include "rclcpp/rclcpp.hpp"

#include "controller_interface/controller_interface.hpp"
#include "eigen3/Eigen/Dense"
#include "eigen3/Eigen/Geometry"
#include "std_msgs/msg/float32_multi_array.hpp"
#include "tf2_ros/transform_broadcaster.h"

#include "geometry_msgs/msg/twist.hpp"
#include "geometry_msgs/msg/transform_stamped.hpp"
#include "sensor_msgs/msg/imu.hpp"
#include "geometry_msgs/msg/vector3.hpp"

// using FloatArray32 = geometry_msgs::msg::Twist;

using FloatArray32 = std_msgs::msg::Float32MultiArray;

namespace abb_controller{

class ABBController : public controller_interface::ControllerInterface{

public:

    ABBController();

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

    rclcpp::Publisher<FloatArray32>::SharedPtr joint_pub_;
    rclcpp::Subscription<FloatArray32>::SharedPtr joint_subs_;

    std::vector<float> joint_desired_positions_;

    protected:
        std::vector<std::string> joint_names_;
        std::string interface_name_;
};

} // El szs

#endif