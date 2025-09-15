#include "scara_hardware_interface/scara_hardware_interface.hpp"

namespace scara_hardware_layer {


hardware_interface::CallbackReturn ScaraHardwareInterface::on_init(const hardware_interface::HardwareInfo &info){
    
    if(hardware_interface::SystemInterface::on_init(info) != hardware_interface::CallbackReturn::SUCCESS){
        return hardware_interface::CallbackReturn::ERROR;
    }

    info_ = info;

    RCLCPP_INFO(rclcpp::get_logger("scara_hardware_abstraction"), "I STARTED");
    
    return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn ScaraHardwareInterface::on_configure
(const rclcpp_lifecycle::State & previus_state){

    (void)previus_state;

    joint_position_targets_[0] = 0.;
    joint_position_targets_[1] = 0.;
    joint_position_targets_[2] = 0.;
    joint_position_targets_[3] = 0.;

    try {
    serial_port_ = SerialPort("/dev/ttyUSB1", BaudRate::B_115200, NumDataBits::EIGHT, Parity::NONE, NumStopBits::ONE);
	serial_port_.SetTimeout(100); // Block for up to 100ms to receive data
	serial_port_.Open();
    }catch(Exception e){
        RCLCPP_INFO(rclcpp::get_logger("scara_sim"), "Failed to config the serial port");
        return hardware_interface::CallbackReturn::FAILURE;
    }

    RCLCPP_INFO(rclcpp::get_logger("scara_sim"), "I CONFIG");
    return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn ScaraHardwareInterface::on_activate
(const rclcpp_lifecycle::State & previous_state){
    (void)previous_state;
    RCLCPP_INFO(rclcpp::get_logger("scara_hardware_abstraction"), "I'M ACTIVATING'");
    return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn ScaraHardwareInterface::on_deactivate
(const rclcpp_lifecycle::State & previous_state){
    
    try{
    serial_port_.Close();
    }catch(Exception e){
    RCLCPP_INFO(rclcpp::get_logger("scara_hardware_abstraction"), "Failed to config the serial port");   
    }
    
    (void)previous_state;
    return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::return_type ScaraHardwareInterface::read
(const rclcpp::Time & time, const rclcpp::Duration & period){
    
    (void)time;
    (void)period;

    joint_positions_[0] = joint_position_targets_[0];
    joint_positions_[1] = joint_position_targets_[1];
    joint_positions_[2] = joint_position_targets_[2];
    joint_positions_[3] = joint_position_targets_[3];
 

    return hardware_interface::return_type::OK;
}

hardware_interface::return_type ScaraHardwareInterface::write
(const rclcpp::Time & time, const rclcpp::Duration & period){
    
    (void)time;
    (void)period;

    std::string writeData = std::to_string(joint_position_targets_[0]*180/M_PI) + "|" +
    std::to_string(joint_position_targets_[1]*180/M_PI) + "|" + 
    std::to_string(joint_position_targets_[2]) + "\n";

    RCLCPP_INFO(rclcpp::get_logger("scara_sim"), writeData.c_str());

    try{
        serial_port_.Write(writeData);
    }catch(Exception e){
         RCLCPP_INFO(rclcpp::get_logger("scara_hardware_abstraction"), "Failed to write to serial port");   
    }

    return hardware_interface::return_type::OK;

}

std::vector<hardware_interface::StateInterface>
ScaraHardwareInterface::export_state_interfaces()
{
    std::vector<hardware_interface::StateInterface> state_interfaces;
    for (size_t i = 0; i < 4; ++i) {
        state_interfaces.emplace_back(
            "joint_" + std::to_string(i),
            "position",
            &joint_positions_[i] // You need to define this array
        );
    }
    return state_interfaces;
}

std::vector<hardware_interface::CommandInterface>
ScaraHardwareInterface::export_command_interfaces()
{
    std::vector<hardware_interface::CommandInterface> command_interfaces;
    for (size_t i = 0; i < 4; ++i) {
        command_interfaces.emplace_back(
            "joint_" + std::to_string(i),
            "position",
            &joint_position_targets_[i] // You need to define this array
        );
    }
    return command_interfaces;
}

ScaraHardwareInterface::~ScaraHardwareInterface(){
    this->cleanup();
}

void ScaraHardwareInterface::cleanup(){}

}

#include "pluginlib/class_list_macros.hpp"

PLUGINLIB_EXPORT_CLASS(scara_hardware_layer::ScaraHardwareInterface,hardware_interface::SystemInterface)
