#include "abb_controllers/abb_forward_controller.hpp"

namespace abb_controller
{

    ABBController::ABBController() : controller_interface::ControllerInterface(){
    }

    controller_interface::CallbackReturn
    ABBController::on_init()
    {

        joint_names_ = auto_declare<std::vector<std::string>>("joints", {});
        interface_name_ = auto_declare<std::string>("interface_name", "position");

        printf("Trying...");

        return controller_interface::CallbackReturn::SUCCESS;
    }

    controller_interface::CallbackReturn
    ABBController::on_configure(const rclcpp_lifecycle::State &previous_state)
    {
        (void)previous_state;


        auto callback_joint = [this](const FloatArray32::SharedPtr msg) -> void
        {
            for (int ii = 0; ii < 6; ii++ ) {
                joint_desired_positions_[ii] = msg->data[ii];
            }

        };

        joint_subs_ = this->get_node()->create_subscription<FloatArray32>("/ABBController/desired_joint_pos", 10, callback_joint);
        joint_pub_ = this->get_node()->create_publisher<FloatArray32>("/ABBController/current_joint_pos", 10);

        return controller_interface::CallbackReturn::SUCCESS;
    }

    controller_interface::InterfaceConfiguration
    ABBController::command_interface_configuration() const
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
    ABBController::state_interface_configuration() const
    {

        controller_interface::InterfaceConfiguration config;
        config.type = controller_interface::interface_configuration_type::INDIVIDUAL;
        // config.names.reserve(joint_names_.size() + 7);
        config.names.reserve(6);
        config.names.push_back("position_joint_0/position");
        config.names.push_back("position_joint_1/position");
        config.names.push_back("position_joint_2/position");
        config.names.push_back("position_joint_3/position");
        config.names.push_back("position_joint_4/position");
        config.names.push_back("position_joint_5/position");

        return config;
    }

    controller_interface::CallbackReturn
    ABBController::on_activate(const rclcpp_lifecycle::State &previous_state)
    {

        (void)previous_state;

        joint_desired_positions_ = {0., 0., 0., 0., 0., 0.,};

        return CallbackReturn::SUCCESS;
    }

    controller_interface::return_type
    ABBController::update(const rclcpp::Time &time, const rclcpp::Duration &period)
    {

        (void)time;
        (void)period;

        (void)command_interfaces_[0].set_value(joint_desired_positions_[0]);
        (void)command_interfaces_[1].set_value(joint_desired_positions_[1]);
        (void)command_interfaces_[2].set_value(joint_desired_positions_[2]);
        (void)command_interfaces_[3].set_value(joint_desired_positions_[3]);
        (void)command_interfaces_[4].set_value(joint_desired_positions_[4]);
        (void)command_interfaces_[5].set_value(joint_desired_positions_[5]);

        FloatArray32 msg;

        msg.data = {(float)state_interfaces_[0].get_value(),
                    (float)state_interfaces_[1].get_value(),
                    (float)state_interfaces_[2].get_value(),
                    (float)state_interfaces_[3].get_value(),
                    (float)state_interfaces_[4].get_value(),
                    (float)state_interfaces_[5].get_value()};

        // Publish the complete IMU message
        joint_pub_->publish(msg);
        return controller_interface::return_type::OK;
    }

}

#include "pluginlib/class_list_macros.hpp"

PLUGINLIB_EXPORT_CLASS(abb_controller::ABBController, controller_interface::ControllerInterface)