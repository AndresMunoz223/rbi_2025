#include "rov_controllers/rov_forward_controller.hpp"

namespace rov_controller
{

    RovController::RovController() : controller_interface::ControllerInterface()
    {

        target_forces_to_actuator_map << 1, 1, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0,
            0, 0, 1, 1, 1, 1,
            0, 0, 1, 1, -1, -1,
            0, 0, 1, -1, 1, -1,
            1, -1, 0, 0, 0, 0;

        target_forces_to_actuator_map = target_forces_to_actuator_map.completeOrthogonalDecomposition().pseudoInverse();

        target_accel_to_forces_map << 0.,
            0.,
            0.,
            0.,
            0.,
            0.;
    }

    controller_interface::CallbackReturn
    RovController::on_init()
    {

        joint_names_ = auto_declare<std::vector<std::string>>("joints", {});
        interface_name_ = auto_declare<std::string>("interface_name", "effort");

        printf("Trying...");

        return controller_interface::CallbackReturn::SUCCESS;
    }

    controller_interface::CallbackReturn
    RovController::on_configure(const rclcpp_lifecycle::State &previous_state)
    {
        (void)previous_state;

        auto callback = [this](const Twist::SharedPtr msg) -> void
        {
            u_cmd_ = msg->linear.x;
            z_cmd_ = msg->linear.z;
            roll_cmd_ = msg->angular.x;
            pitch_cmd_ = msg->angular.y;
            yaw_cmd_ = msg->angular.z;

            target_accel_to_forces_map << (hull_mass / 2) * u_cmd_,
                0,
                (hull_mass / 4) * z_cmd_,
                (hull_inertia_xx / (2 * hull_lw)) * roll_cmd_,
                (hull_inertia_yy / (hull_ld * 2)) * pitch_cmd_,
                (hull_inertia_zz / (hull_lb * 2)) * yaw_cmd_;
        };

        tf_broadcaster_ = std::make_unique<tf2_ros::TransformBroadcaster>(get_node());

        twist_subs_ = this->get_node()->create_subscription<Twist>("/rov/cmd_vel", 10, callback);
        imu_pub_ = this->get_node()->create_publisher<sensor_msgs::msg::Imu>("/imu/data", 10);

        return controller_interface::CallbackReturn::SUCCESS;
    }

    controller_interface::InterfaceConfiguration
    RovController::command_interface_configuration() const
    {

        controller_interface::InterfaceConfiguration config;
        config.type = controller_interface::interface_configuration_type::INDIVIDUAL;
        config.names.reserve(joint_names_.size());
        for (auto joint_name : joint_names_)
        {
            config.names.push_back(joint_name + "/" + interface_name_);
        }

        return config;
    }

    controller_interface::InterfaceConfiguration
    RovController::state_interface_configuration() const
    {

        controller_interface::InterfaceConfiguration config;
        config.type = controller_interface::interface_configuration_type::INDIVIDUAL;
        // config.names.reserve(joint_names_.size() + 7);
        config.names.reserve(13);
        config.names.push_back("pose1/state");
        config.names.push_back("pose2/state");
        config.names.push_back("pose3/state");
        config.names.push_back("pose4/state");
        config.names.push_back("pose5/state");
        config.names.push_back("pose6/state");
        config.names.push_back("pose7/state");
        config.names.push_back("IMU_accel/1/state");
        config.names.push_back("IMU_accel/2/state");
        config.names.push_back("IMU_accel/3/state");
        config.names.push_back("IMU_vel/1/state");
        config.names.push_back("IMU_vel/2/state");
        config.names.push_back("IMU_vel/3/state");

        // for (auto joint_name : joint_names_){
        //     config.names.push_back(joint_name + "/" + interface_name_);
        // }

        return config;
    }

    controller_interface::CallbackReturn
    RovController::on_activate(const rclcpp_lifecycle::State &previous_state)
    {

        (void)previous_state;

        this->u_cmd_ = 0.;
        this->z_cmd_ = 0.;

        this->pitch_cmd_ = 0.;
        this->yaw_cmd_ = 0.;
        this->roll_cmd_ = 0.;

        return CallbackReturn::SUCCESS;
    }

    controller_interface::return_type
    RovController::update(const rclcpp::Time &time, const rclcpp::Duration &period)
    {

        (void)time;
        (void)period;

        // for(int ii = 0; ii < (int)command_interfaces_.size(); ii++){
        //     (void)command_interfaces_[ii].set_value(2.);
        // }

        Eigen::Matrix<double, 6, 1> input_vector = target_forces_to_actuator_map * target_accel_to_forces_map;

        for (int ii = 0; ii < 6; ii++)
        {
            if (input_vector(ii) < 0.)
            {
                input_vector(ii) = 0.;
            }
        }
        // for (int i = 0; i < 6; ++i) {
        //     RCLCPP_INFO(rclcpp::get_logger("rov_controller"), "Input vector[%d]: %f", i, input_vector(i));
        // }

        (void)command_interfaces_[0].set_value(input_vector(0));
        (void)command_interfaces_[1].set_value(input_vector(1));
        (void)command_interfaces_[2].set_value(input_vector(2));
        (void)command_interfaces_[3].set_value(input_vector(3));
        (void)command_interfaces_[4].set_value(input_vector(4));
        (void)command_interfaces_[5].set_value(input_vector(5));

        // Your measured quaternion (from MuJoCo)
        Eigen::Quaterniond q_measured(state_interfaces_[3].get_value(),
                                      state_interfaces_[4].get_value(),
                                      state_interfaces_[5].get_value(),
                                      state_interfaces_[6].get_value());

        // Inverse of initial -90deg pitch about 'Y'
        Eigen::Quaterniond q_correction(0.70710678, 0, 0.70710678, 0);

        // Corrected orientation
        Eigen::Quaterniond q_corrected = q_correction * q_measured;

        auto coefs = q_corrected.coeffs();

        // Now convert to Euler angles as usual
        // Eigen::Vector3d euler = q_corrected.toRotationMatrix().eulerAngles(0, 1, 2); // roll, pitch, yaw

        geometry_msgs::msg::TransformStamped t;

        // Header
        t.header.stamp = this->get_node()->get_clock()->now();
        t.header.frame_id = "odom";     // parent frame
        t.child_frame_id = "base_link"; // child frame

        // Translation
        t.transform.translation.x = state_interfaces_[0].get_value();
        t.transform.translation.y = state_interfaces_[1].get_value();
        t.transform.translation.z = state_interfaces_[2].get_value();

        // Rotation (identity quaternion)
        t.transform.rotation.x = coefs(0);
        t.transform.rotation.y = coefs(1);
        t.transform.rotation.z = coefs(2);
        t.transform.rotation.w = coefs(3);

        // Send transform
        tf_broadcaster_->sendTransform(t);

        auto now = rclcpp::Clock().now();

        // Fill IMU message
        imu_msg_.header.stamp = now;

        // Linear acceleration (m/s²)
        imu_msg_.linear_acceleration.x = state_interfaces_[7].get_value();
        imu_msg_.linear_acceleration.y = state_interfaces_[8].get_value();
        imu_msg_.linear_acceleration.z = state_interfaces_[9].get_value();

        // Angular velocity (rad/s)
        imu_msg_.angular_velocity.x = state_interfaces_[10].get_value();
        imu_msg_.angular_velocity.y = state_interfaces_[11].get_value();
        imu_msg_.angular_velocity.z = state_interfaces_[12].get_value();


        // Publish the complete IMU message
        imu_pub_->publish(imu_msg_);

        // RCLCPP_INFO(rclcpp::get_logger("rov_x"),std::to_string(state_interfaces_[0].get_value()).c_str());
        // RCLCPP_INFO(rclcpp::get_logger("rov_y"),std::to_string(state_interfaces_[1].get_value()).c_str());
        // RCLCPP_INFO(rclcpp::get_logger("rov_z"),std::to_string(state_interfaces_[2].get_value()).c_str());
        // RCLCPP_INFO(rclcpp::get_logger("rov_roll"),std::to_string(euler[2]*(180/M_PI)).c_str());
        // RCLCPP_INFO(rclcpp::get_logger("rov_pitch"),std::to_string(euler[1]*(180/M_PI)).c_str());
        // RCLCPP_INFO(rclcpp::get_logger("rov_yaw"),std::to_string(euler[0]*(180/M_PI)).c_str());
        // RCLCPP_INFO(rclcpp::get_logger("rov_quat_w"), std::to_string(state_interfaces_[3].get_value()).c_str());
        // RCLCPP_INFO(rclcpp::get_logger("rov_quat_x"), std::to_string(state_interfaces_[4].get_value()).c_str());
        // RCLCPP_INFO(rclcpp::get_logger("rov_quat_y"), std::to_string(state_interfaces_[5].get_value()).c_str());
        // RCLCPP_INFO(rclcpp::get_logger("rov_quat_z"), std::to_string(state_interfaces_[6].get_value()).c_str());

        return controller_interface::return_type::OK;
    }

}

#include "pluginlib/class_list_macros.hpp"

PLUGINLIB_EXPORT_CLASS(rov_controller::RovController, controller_interface::ControllerInterface)