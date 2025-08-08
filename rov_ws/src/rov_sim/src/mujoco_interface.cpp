#include "rov_sim/mujoco_interface.hpp"

//!---------------------------------- Includes up from here -----------------------------------

using std::placeholders::_1;

char filename[] = "/home/eia/repo/rbi_2025_2/rov_ws/src/rov_sim/description/basic_scenario.xml";

class RovSimulator : public rclcpp::Node
{
    public:
        mjModel* sim_model_object = NULL;
        mjData* sim_data_object = NULL;
        mjvCamera sim_cam;                      // abstract camera
        mjvOption sim_opt;                      // visualization options
        mjvScene sim_scn;                       // abstract scene
        mjrContext sim_con;                     // custom GPU context

        RovSimulator() : 
            Node("rov_simulator"),
            sim_stop_flag(false)
            {
            //! ROS2 related elements
            subscription_ = this->create_subscription<geometry_msgs::msg::Twist>("cmd_vel",10,std::bind(&RovSimulator::input_callback, this, _1));
            //! ---------------------_ (•◡•) /_----------------------

            //? Firing up the simulation
            this->sim_model_object = mj_loadXML(filename, NULL, err_string, sizeof(err_string));
            if (!this->sim_model_object) {
                printf("MuJoCo load error: %s\n", err_string);
                mj_deleteModel(this->sim_model_object);
            }else{
            this->sim_data_object = mj_makeData(this->sim_model_object);
            }

            start_sim_thread();
        }

        ~RovSimulator(){
            this->cleanup();

            sim_stop_flag = true;
            // 2. Wait for the simulation thread to finish
            if (this->simulation_thread_.joinable()) {
                RCLCPP_INFO(this->get_logger(), "Joining simulation thread...");
                this->simulation_thread_.join();
                RCLCPP_INFO(this->get_logger(), "Simulation thread joined.");
            }
        }

        void start_sim_thread(){
            this->simulation_thread_ = std::thread(&RovSimulator::sim_thread,this);
        }

        void sim_thread(){

            GLFWwindow* window;

            if(!glfwInit())
                mju_error("Could not initialize GLFW");

            window = glfwCreateWindow(1244, 700, "Demo", NULL, NULL);
            glfwMakeContextCurrent(window);
            glfwSwapInterval(1);


            mjv_defaultCamera(&this->sim_cam);
            mjv_defaultOption(&this->sim_opt);
            mjv_defaultScene(&this->sim_scn);
            mjr_defaultContext(&this->sim_con);
            mjv_makeScene(this->sim_model_object, &this->sim_scn, 2000);                // space for 2000 objects
            mjr_makeContext(this->sim_model_object, &this->sim_con, mjFONTSCALE_150);   // model-specific context
 
            int body_id = mj_name2id(this->sim_model_object, mjOBJ_BODY, "hull_link");
            if (body_id == -1) {
                RCLCPP_ERROR(rclcpp::get_logger("my_logger"), "Body 'hull_link' not found");
            } else {
                this->sim_cam.type = mjCAMERA_TRACKING;
                this->sim_cam.trackbodyid = body_id;
            }

            RCLCPP_INFO(rclcpp::get_logger("my_logger"), "Entered thread");

            this->sim_cam.type = mjCAMERA_TRACKING;
            this->sim_cam.trackbodyid = mj_name2id(sim_model_object, mjOBJ_BODY, "hull_link");

            while( !glfwWindowShouldClose(window) && !sim_stop_flag){   
                mjtNum simstart = this->sim_data_object->time;
                while( this->sim_data_object->time - simstart < 1.0/60.0 ){
                    mj_step(this->sim_model_object, this->sim_data_object);
                }

                mjrRect viewport = {0, 0, 0, 0};
                glfwGetFramebufferSize(window, &viewport.width, &viewport.height);

                this->sim_data_object->ctrl[0] = this->velocity_input[0];
                this->sim_data_object->ctrl[1] = this->velocity_input[0];
                this->sim_data_object->ctrl[2] = this->velocity_input[0];
                this->sim_data_object->ctrl[3] = this->velocity_input[0];
                this->sim_data_object->ctrl[4] = this->velocity_input[0];
                this->sim_data_object->ctrl[5] = this->velocity_input[0];
        
                // update scene and render
                this->sim_opt.frame = mjFRAME_WORLD;

                mjv_updateScene(this->sim_model_object, this->sim_data_object, &this->sim_opt, NULL, &this->sim_cam, mjCAT_ALL, &this->sim_scn);
                mjr_render(viewport, &this->sim_scn, &this->sim_con);

                glfwSwapBuffers(window);
                glfwPollEvents();
            }

            mjv_freeScene(&this->sim_scn);
            mjr_freeContext(&this->sim_con);

            mj_deleteData(this->sim_data_object);
            mj_deleteModel(this->sim_model_object);

            glfwTerminate();
            RCLCPP_INFO(rclcpp::get_logger("my_logger"), "Exit screen");
        }

    private:

        void cleanup(){
            mj_deleteModel(this->sim_model_object);
            mj_deleteData(this->sim_data_object);
        }

        void input_callback(const geometry_msgs::msg::Twist::SharedPtr msg){
           //! Convention: -> [x, y, z, phi, theta, psi] ._aka roll, pitch, yaw
            //!                [0, 1, 2,  3 ,   4 ,    5]
                this->velocity_input = {
                    (float)msg->linear.x,
                    (float)msg->linear.y,
                    (float)msg->linear.z,
                    (float)msg->angular.x,
                    (float)msg->angular.y,
                    (float)msg->angular.z
                };

                RCLCPP_INFO(this->get_logger(), "I heard: '%f'", msg->linear.x);
            }

        //! Sim related vars
        std::atomic<bool> sim_stop_flag;
        std::thread simulation_thread_;
        char err_string[1000] = "Could not load binary model";
        //! --------------------------------------------

        std::array<float, 6> velocity_input;    
        rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr subscription_;
};


int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<RovSimulator>();
  rclcpp::executors::MultiThreadedExecutor executor;
  executor.add_node(node);
  executor.spin();
  rclcpp::shutdown();
  return 0;
}
