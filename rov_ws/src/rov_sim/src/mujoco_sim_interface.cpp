#include "include/rov_sim/mujoco_sim_interface.hpp"

namespace rov_simulator_layer {

hardware_interface::CallbackReturn RovSimulatorInterface::on_init
(const hardware_interface::HardwareInfo &info){
    
    if(hardware_interface::SystemInterface::on_init(info) != hardware_interface::CallbackReturn::SUCCESS){
        return hardware_interface::CallbackReturn::ERROR;
    }

    info_ = info;

    //! Getting the body id
    hull_name_id = mj_name2id(sim_model_object, mjOBJ_BODY, body_name.c_str());

    target_forces_to_actuator_map  = Eigen::MatrixXd(6,6);
    target_forces_to_actuator_map << 1,  1,  0,  0,  0,  0,
                                     0,  0,  0,  0,  0,  0,
                                     1,  1,  1,  1,  1,  1,
                                     0,  0, -1, -1,  1,  1,
                                     1, -1,  0,  0,  0,  0;  

    target_forces_to_actuator_map = target_forces_to_actuator_map.inverse();

    target_accel_to_forces_map = Eigen::MatrixXd(6,1);

    set_point_to_accel_map = Eigen::MatrixXd(6,1);

    return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn RovSimulatorInterface::on_configure
(const rclcpp_lifecycle::State & previus_state){

    //? Loading up the model.
    this->sim_model_object = mj_loadXML(filename, NULL, err_string, sizeof(err_string));
    if (!this->sim_model_object) {
        printf("MuJoCo load error: %s\n", err_string);
        mj_deleteModel(this->sim_model_object);
        return hardware_interface::CallbackReturn::FAILURE;
    }else{
        this->sim_data_object = mj_makeData(this->sim_model_object);
    }

    return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn RovSimulatorInterface::on_activate
(const rclcpp_lifecycle::State & previous_state){
    (void)previous_state;
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

    target_accel_to_forces_map << (hull_mass/2)*u_input_ + mu_x,
                                        0,
                                (hull_mass/6)*z_input_ + mu_z,
                            (hull_lw*hull_inertia_xx/8)*roll_input_,
                            (hull_ld*hull_inertia_yy/8)*pitch_input_,
                            (hull_lb*hull_inertia_zz/8)*yaw_input_;

}

std::vector<hardware_interface::StateInterface>
RovSimulatorInterface::export_state_interfaces()
{
    std::vector<hardware_interface::StateInterface> state_interfaces;

    state_interfaces.emplace_back("base_joint", "x", &free_joint_pos[0]);
    state_interfaces.emplace_back("base_joint", "y", &free_joint_pos[1]);
    state_interfaces.emplace_back("base_joint", "z", &free_joint_pos[2]);
    state_interfaces.emplace_back("base_joint", "q0", &q.x());
    state_interfaces.emplace_back("base_joint", "q1", &q.y());
    state_interfaces.emplace_back("base_joint", "q2", &q.z());
    state_interfaces.emplace_back("base_joint", "q3", &q.w());

    return state_interfaces;
}

std::vector<hardware_interface::CommandInterface> 
RovSimulatorInterface::export_command_interfaces()
{
    std::vector<hardware_interface::CommandInterface> command_interfaces;

    command_interfaces.emplace_back("base_joint", "u", &u_input_);
    command_interfaces.emplace_back("base_joint", "z", &z_input_);
    command_interfaces.emplace_back("base_joint", "roll", &roll_input_);
    command_interfaces.emplace_back("base_joint", "pith", &pitch_input_);
    command_interfaces.emplace_back("base_joint", "yaw", &yaw_input_);

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

            Eigen::VectorXd input_vector = target_accel_to_forces_map * target_forces_to_actuator_map;

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

                this->sim_data_object->ctrl[0] = input_vector(0);
                this->sim_data_object->ctrl[1] = input_vector(1);
                this->sim_data_object->ctrl[2] = input_vector(2);
                this->sim_data_object->ctrl[3] = input_vector(3);
                this->sim_data_object->ctrl[4] = input_vector(4);
                this->sim_data_object->ctrl[5] = input_vector(5);

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