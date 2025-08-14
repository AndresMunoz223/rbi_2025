#include "rov_sim/mujoco_sim_interface.hpp"

namespace rov_simulator_layer {

hardware_interface::CallbackReturn RovSimulatorInterface::on_init
(const hardware_interface::HardwareInfo &info){
    
    
    if(hardware_interface::SystemInterface::on_init(info) != hardware_interface::CallbackReturn::SUCCESS){
        return hardware_interface::CallbackReturn::ERROR;
    }

    info_ = info;

    RCLCPP_INFO(rclcpp::get_logger("rov sim"), "I STARTED");
    return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn RovSimulatorInterface::on_configure
(const rclcpp_lifecycle::State & previus_state){

    (void)previus_state;
    //? Loading up the model.
    this->sim_model_object = mj_loadXML(filename, NULL, err_string, sizeof(err_string));
    if (!this->sim_model_object) {
        printf("MuJoCo load error: %s\n", err_string);
        RCLCPP_INFO(rclcpp::get_logger("rov sim"), "FAILED ");
        mj_deleteModel(this->sim_model_object);
        return hardware_interface::CallbackReturn::FAILURE;
    }else{
        this->sim_data_object = mj_makeData(this->sim_model_object);
    }

        //! Getting the body id
    hull_name_id = mj_name2id(sim_model_object, mjOBJ_BODY, body_name.c_str());

    this->thruster_efforts_[0] = 0.;
    this->thruster_efforts_[1] = 0.;
    this->thruster_efforts_[2] = 0.;
    this->thruster_efforts_[3] = 0.;
    this->thruster_efforts_[4] = 0.;
    this->thruster_efforts_[5] = 0.;

    RCLCPP_INFO(rclcpp::get_logger("rov sim"), "I CONFIG");
    return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn RovSimulatorInterface::on_activate
(const rclcpp_lifecycle::State & previous_state){
    (void)previous_state;
    RCLCPP_INFO(rclcpp::get_logger("rov sim"), "I'M ACTIVATING'");
    start_sim();
    return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn RovSimulatorInterface::on_deactivate
(const rclcpp_lifecycle::State & previous_state){

    (void)previous_state;
    sim_stop_flag = true;
    return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::return_type RovSimulatorInterface::read
(const rclcpp::Time & time, const rclcpp::Duration & period){
    
    (void)time;
    (void)period;
    std::vector<double> linear_vel =  {0., 0., 0.};

    free_joint_pos[0] = 0.;
    free_joint_pos[1] = 0.;
    free_joint_pos[2] = 0.;
    q.x() = 0.;
    q.y() = 0.;
    q.z() = 0.;
    q.w() = 0.;

    return hardware_interface::return_type::OK;
}

hardware_interface::return_type RovSimulatorInterface::write
(const rclcpp::Time & time, const rclcpp::Duration & period){
    
    (void)time;
    (void)period;

    // this->sim_data_object->ctrl[0] = thruster_commands_[0];
    // this->sim_data_object->ctrl[1] = thruster_commands_[1];
    // this->sim_data_object->ctrl[2] = thruster_commands_[2];
    // this->sim_data_object->ctrl[3] = thruster_commands_[3];
    // this->sim_data_object->ctrl[4] = thruster_commands_[4];
    // this->sim_data_object->ctrl[5] = thruster_commands_[5];

    // target_accel_to_forces_map << (hull_mass/2)*u_input_ + mu_x,
    //                                     0,
    //                             (hull_mass/6)*z_input_ + mu_z,
    //                         (hull_lw*hull_inertia_xx/8)*roll_input_,
    //                         (hull_ld*hull_inertia_yy/8)*pitch_input_,
    //                         (hull_lb*hull_inertia_zz/8)*yaw_input_;

    return hardware_interface::return_type::OK;

}

std::vector<hardware_interface::StateInterface>
RovSimulatorInterface::export_state_interfaces()
{
    std::vector<hardware_interface::StateInterface> state_interfaces;
    for (size_t i = 0; i < 6; ++i) {
        state_interfaces.emplace_back(
            "thruster_joint_" + std::to_string(i+1),
            "effort",
            &thruster_efforts_[i] // You need to define this array
        );
    }
    return state_interfaces;
}

std::vector<hardware_interface::CommandInterface>
RovSimulatorInterface::export_command_interfaces()
{
    std::vector<hardware_interface::CommandInterface> command_interfaces;
    for (size_t i = 0; i < 6; ++i) {
        command_interfaces.emplace_back(
            "thruster_joint_" + std::to_string(i+1),
            "effort",
            &thruster_commands_[i] // You need to define this array
        );
    }
    return command_interfaces;
}

void RovSimulatorInterface::sim_thread(){

            GLFWwindow* window;

            if(!glfwInit())
                mju_error("Could not initialize GLFW");

            // create window, make OpenGL context current, request v-sync
            window = glfwCreateWindow(1244, 700, "Demo", NULL, NULL);
            glfwMakeContextCurrent(window);
            glfwSwapInterval(1);

            // initialize visualization data structures

            mjv_defaultCamera(&this->sim_cam);
            mjv_defaultOption(&this->sim_opt);
            mjv_defaultScene(&this->sim_scn);
            mjr_defaultContext(&this->sim_con);
            mjv_makeScene(this->sim_model_object, &this->sim_scn, 2000);                // space for 2000 objects
            mjr_makeContext(this->sim_model_object, &this->sim_con, mjFONTSCALE_150);   // model-specific context
 
            int body_id = mj_name2id(this->sim_model_object, mjOBJ_BODY, "hull_link");
            if (body_id == -1) {
                RCLCPP_ERROR(rclcpp::get_logger("interface_logger"), "Body 'hull_link' not found");
            } else {
                this->sim_cam.type = mjCAMERA_TRACKING;
                this->sim_cam.trackbodyid = body_id;
            }

            this->sim_cam.type = mjCAMERA_TRACKING;
            this->sim_cam.trackbodyid = mj_name2id(sim_model_object, mjOBJ_BODY, "hull_link");

            // Eigen::VectorXd input_vector = target_accel_to_forces_map * target_forces_to_actuator_map;

            //! Get body parameters.
            hull_inertia_xx = sim_model_object->body_inertia[3 * hull_name_id + 0];
            hull_inertia_yy = sim_model_object->body_inertia[3 * hull_name_id + 1];
            hull_inertia_zz = sim_model_object->body_inertia[3 * hull_name_id + 2];


            while( !glfwWindowShouldClose(window) && !sim_stop_flag){   
                mjtNum simstart = this->sim_data_object->time;
                while( this->sim_data_object->time - simstart < 1.0/60.0 ){
                    mj_step(this->sim_model_object, this->sim_data_object);
                }

                mjrRect viewport = {0, 0, 0, 0};
                glfwGetFramebufferSize(window, &viewport.width, &viewport.height);
        
                //! Control stuff ------------------------------

                this->sim_data_object->ctrl[0] = thruster_commands_[0];
                this->sim_data_object->ctrl[1] = thruster_commands_[1];
                this->sim_data_object->ctrl[2] = thruster_commands_[2];
                this->sim_data_object->ctrl[3] = thruster_commands_[3];
                this->sim_data_object->ctrl[4] = thruster_commands_[4];
                this->sim_data_object->ctrl[5] = thruster_commands_[5];

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
            RCLCPP_INFO(rclcpp::get_logger("interface_logger"), "Exit screen");
        }

void RovSimulatorInterface::start_sim(){
    this->simulation_thread_ = std::thread(&RovSimulatorInterface::sim_thread,this);
}

RovSimulatorInterface::~RovSimulatorInterface(){
    this->cleanup();

    sim_stop_flag = true;
    // 2. Wait for the simulation thread to finish
    if (this->simulation_thread_.joinable()) {
        this->simulation_thread_.join();
    }
}

void RovSimulatorInterface::cleanup(){
    mj_deleteModel(this->sim_model_object);
    mj_deleteData(this->sim_data_object);
}

}

#include "pluginlib/class_list_macros.hpp"


PLUGINLIB_EXPORT_CLASS(rov_simulator_layer::RovSimulatorInterface,hardware_interface::SystemInterface)
