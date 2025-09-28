#include "rov_controllers/rov_hardware_controller.hpp"

namespace rov_hardware_controller
{

    RovHardwareController::RovHardwareController() : controller_interface::ControllerInterface()
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
    RovHardwareController::on_init()
    {
        joint_names_ = auto_declare<std::vector<std::string>>("joints", {});
        interface_name_ = auto_declare<std::string>("interface_name", "effort");

        printf("Trying...");

        return controller_interface::CallbackReturn::SUCCESS;
    }

    controller_interface::CallbackReturn
    RovHardwareController::on_configure(const rclcpp_lifecycle::State &previous_state)
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

        twist_subs_ = this->get_node()->create_subscription<Twist>("/rov/cmd_vel", 10, callback);
        return controller_interface::CallbackReturn::SUCCESS;
    }

    controller_interface::InterfaceConfiguration
    RovHardwareController::command_interface_configuration() const
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
    RovHardwareController::state_interface_configuration() const
    {

        controller_interface::InterfaceConfiguration config;
        config.type = controller_interface::interface_configuration_type::INDIVIDUAL;
        config.names.reserve(joint_names_.size());
        for (auto joint_name : joint_names_){
            config.names.push_back(joint_name + "/" + interface_name_);
        }
        return config;
    }

    controller_interface::CallbackReturn
    RovHardwareController::on_activate(const rclcpp_lifecycle::State &previous_state)
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
    RovHardwareController::update(const rclcpp::Time &time, const rclcpp::Duration &period)
    {

        (void)time;
        (void)period;


        Eigen::Matrix<double, 6, 1> input_vector = target_forces_to_actuator_map * target_accel_to_forces_map;

        for (int ii = 0; ii < 6; ii++)
        {
            if (input_vector(ii) < 0.)
            {
                input_vector(ii) = 0.;
            }
        }


        (void)command_interfaces_[0].set_value(input_vector(0));
        (void)command_interfaces_[1].set_value(input_vector(1));
        (void)command_interfaces_[2].set_value(input_vector(2));
        (void)command_interfaces_[3].set_value(input_vector(3));
        (void)command_interfaces_[4].set_value(input_vector(4));
        (void)command_interfaces_[5].set_value(input_vector(5));

        return controller_interface::return_type::OK;
    }

}

#include "pluginlib/class_list_macros.hpp"

PLUGINLIB_EXPORT_CLASS(rov_hardware_controller::RovHardwareController, controller_interface::ControllerInterface)