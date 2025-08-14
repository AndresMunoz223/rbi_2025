cmake_minimum_required(VERSION 3.8)
project(rov_mujoco_sim)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)

include_directories(include)

set(MUJOCO_LIB_DIR ${CMAKE_SOURCE_DIR}/../../mujoco)
set(MUJOCO_INCLUDE_DIR ${CMAKE_SOURCE_DIR}/../../mujoco/include/mujoco)
set(MUJOCO_INCLUDE_DIR_2 ${CMAKE_SOURCE_DIR}/../../mujoco/include)

include_directories(include ${MUJOCO_INCLUDE_DIR})
include_directories(${MUJOCO_INCLUDE_DIR_2})

link_directories(${MUJOCO_LIB_DIR}/lib)

find_package(PkgConfig REQUIRED)
pkg_check_modules(GLFW REQUIRED glfw3)

include_directories(${GLFW_INCLUDE_DIRS})
link_directories(${GLFW_LIBRARY_DIRS})

add_executable(rov_mujoco_sim_direct src/mujoco_interface.cpp)
target_link_libraries(rov_mujoco_sim_direct mujoco ${GLFW_LIBRARIES})

find_package(rclcpp REQUIRED)
find_package(rclcpp_lifecycle REQUIRED)
find_package(pluginlib REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(hardware_interface REQUIRED)  # <--- Add this line

add_library(
  rov_mujoco_sim
  SHARED
  src/mujoco_sim_interface.cpp
)

# Link MuJoCo and GLFW here
target_link_libraries(rov_mujoco_sim
  mujoco
  ${GLFW_LIBRARIES}
)

set_target_properties(rov_mujoco_sim PROPERTIES
  BUILD_RPATH "${MUJOCO_LIB_DIR}/lib"
  INSTALL_RPATH "${MUJOCO_LIB_DIR}/lib"
)

pluginlib_export_plugin_description_file(hardware_interface rov_hardware_interface.xml)

install(TARGETS ${PROJECT_NAME}
  DESTINATION lib
)


install(DIRECTORY include
  DESTINATION include
)

ament_export_libraries(
  ${PROJECT_NAME}
)

ament_target_dependencies(${PROJECT_NAME}
  rclcpp
  rclcpp_lifecycle
  pluginlib
  std_msgs
  geometry_msgs
  hardware_interface
)

ament_export_dependencies(
  rclcpp
  rclcpp_lifecycle
  pluginlib
  std_msgs
  geometry_msgs
  hardware_interface
)

install(TARGETS rov_mujoco_sim_direct
  DESTINATION lib/${PROJECT_NAME}
)

set_target_properties(rov_mujoco_sim_direct PROPERTIES
  BUILD_RPATH "${MUJOCO_LIB_DIR}/lib"
  INSTALL_RPATH "${MUJOCO_LIB_DIR}/lib"
)

ament_target_dependencies(rov_mujoco_sim_direct rclcpp std_msgs geometry_msgs hardware_interface pluginlib rclcpp_lifecycle)
ament_package()
