#include "scara_mujoco_sim/mujoco_sim_interface.hpp"

namespace scara_simulator_layer {

hardware_interface::CallbackReturn ScaraSimulatorInterface::on_init
(const hardware_interface::HardwareInfo &info){
    
    
    if(hardware_interface::SystemInterface::on_init(info) != hardware_interface::CallbackReturn::SUCCESS){
        return hardware_interface::CallbackReturn::ERROR;
    }

    info_ = info;

    RCLCPP_INFO(rclcpp::get_logger("scara_sim"), "I STARTED");
    return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn ScaraSimulatorInterface::on_configure
(const rclcpp_lifecycle::State & previus_state){

    (void)previus_state;
    //? Loading up the model.
    this->sim_model_object = mj_loadXML(filename, NULL, err_string, sizeof(err_string));
    if (!this->sim_model_object) {
        printf("MuJoCo load error: %s\n", err_string);
        RCLCPP_INFO(rclcpp::get_logger("scara_sim"), "FAILED ");
        mj_deleteModel(this->sim_model_object);
        return hardware_interface::CallbackReturn::FAILURE;
    }else{
        this->sim_data_object = mj_makeData(this->sim_model_object);
    }

    this->joint_position_targets_[0] = 0.;
    this->joint_position_targets_[1] = 0.;
    this->joint_position_targets_[2] = 0.;
    this->joint_position_targets_[3] = 0.;

    this->joint_positions_[0] = 0.;
    this->joint_positions_[1] = 0.;
    this->joint_positions_[2] = 0.;
    this->joint_positions_[3] = 0.;

    RCLCPP_INFO(rclcpp::get_logger("scara_sim"), "I CONFIG");
    return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn ScaraSimulatorInterface::on_activate
(const rclcpp_lifecycle::State & previous_state){
    (void)previous_state;
    RCLCPP_INFO(rclcpp::get_logger("scara_sim"), "I'M ACTIVATING'");
    start_sim();
    return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn ScaraSimulatorInterface::on_deactivate
(const rclcpp_lifecycle::State & previous_state){

    (void)previous_state;
    sim_stop_flag = true;
    return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::return_type ScaraSimulatorInterface::read
(const rclcpp::Time & time, const rclcpp::Duration & period){
    
    (void)time;
    (void)period;

    return hardware_interface::return_type::OK;
}

hardware_interface::return_type ScaraSimulatorInterface::write
(const rclcpp::Time & time, const rclcpp::Duration & period){
    
    (void)time;
    (void)period;

    return hardware_interface::return_type::OK;

}

std::vector<hardware_interface::StateInterface>
ScaraSimulatorInterface::export_state_interfaces()
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
ScaraSimulatorInterface::export_command_interfaces()
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

void ScaraSimulatorInterface::sim_thread(){

            GLFWwindow* window;

            if(!glfwInit())
                mju_error("Could not initialize GLFW");

            // create window, make OpenGL context current, request v-sync
            window = glfwCreateWindow(1244, 700, "Scara Simulation", NULL, NULL);
            glfwMakeContextCurrent(window);
            glfwSwapInterval(1);

            // initialize visualization data structures
            mjv_defaultCamera(&this->sim_cam);
            mjv_defaultOption(&this->sim_opt);
            mjv_defaultScene(&this->sim_scn);
            mjr_defaultContext(&this->sim_con);
            mjv_makeScene(this->sim_model_object, &this->sim_scn, 2000);                // space for 2000 objects
            mjr_makeContext(this->sim_model_object, &this->sim_con, mjFONTSCALE_150);   // model-specific context
 
            int body_id = mj_name2id(this->sim_model_object, mjOBJ_BODY, "fourth_joint_body");
            if (body_id == -1) {
                RCLCPP_ERROR(rclcpp::get_logger("scara_sim"), "Body '{fourth_joint_body}' not found");
            } else {
                this->sim_cam.type = mjCAMERA_TRACKING;
                this->sim_cam.trackbodyid = body_id;
            }

            while( !glfwWindowShouldClose(window) && !sim_stop_flag){   
                mjtNum simstart = this->sim_data_object->time;
                while( this->sim_data_object->time - simstart < 1.0/60.0 ){
                    mj_step(this->sim_model_object, this->sim_data_object);
                }

                mjrRect viewport = {0, 0, 0, 0};
                glfwGetFramebufferSize(window, &viewport.width, &viewport.height);
        
                //! Control stuff ------------------------------

                this->sim_data_object->qpos[0] = joint_position_targets_[0];
                this->sim_data_object->qpos[1] = joint_position_targets_[1];
                this->sim_data_object->qpos[2] = joint_position_targets_[2];
                this->sim_data_object->qpos[3] = joint_position_targets_[3];

                this->joint_positions_[0] = this->sim_data_object->qpos[0];
                this->joint_positions_[1] = this->sim_data_object->qpos[1];
                this->joint_positions_[2] = this->sim_data_object->qpos[2];
                this->joint_positions_[3] = this->sim_data_object->qpos[3];

                //! ------------------------------------------

                // update scene and render
                this->sim_opt.frame = mjFRAME_WORLD;

                mjv_updateScene(this->sim_model_object, this->sim_data_object, &this->sim_opt, NULL, &this->sim_cam, mjCAT_ALL, &this->sim_scn);
                mjr_render(viewport, &this->sim_scn, &this->sim_con);

                glfwSwapBuffers(window);
                glfwPollEvents();
            }
            // free visualization storage
            mjv_freeScene(&this->sim_scn);
            mjr_freeContext(&this->sim_con);

            // free MuJoCo model and data, deactivate
            mj_deleteData(this->sim_data_object);
            mj_deleteModel(this->sim_model_object);

            glfwTerminate();
            RCLCPP_INFO(rclcpp::get_logger("scara_sim"), "Exit screen");
        }

void ScaraSimulatorInterface::start_sim(){
    this->simulation_thread_ = std::thread(&ScaraSimulatorInterface::sim_thread,this);
}

ScaraSimulatorInterface::~ScaraSimulatorInterface(){
    this->cleanup();
    sim_stop_flag = true;
    // 2. Wait for the simulation thread to finish
    if (this->simulation_thread_.joinable()) {
        this->simulation_thread_.join();
    }
}

void ScaraSimulatorInterface::cleanup(){
    mj_deleteModel(this->sim_model_object);
    mj_deleteData(this->sim_data_object);
}

}

#include "pluginlib/class_list_macros.hpp"

PLUGINLIB_EXPORT_CLASS(scara_simulator_layer::ScaraSimulatorInterface,hardware_interface::SystemInterface)
