cmake_minimum_required(VERSION 3.8)
project(rov_sim)

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

add_executable(rov_mujoco_sim src/mujoco_interface.cpp)

target_link_libraries(rov_mujoco_sim mujoco ${GLFW_LIBRARIES})


find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(hardware_interface REQUIRED)  # <--- Add this line


ament_target_dependencies(rov_mujoco_sim rclcpp std_msgs geometry_msgs hardware_interface)

install(TARGETS rov_mujoco_sim
  DESTINATION lib/${PROJECT_NAME}
)

set_target_properties(rov_mujoco_sim PROPERTIES
  BUILD_RPATH "${MUJOCO_LIB_DIR}/lib"
  INSTALL_RPATH "${MUJOCO_LIB_DIR}/lib"
)

ament_package()
