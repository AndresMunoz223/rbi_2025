cmake_minimum_required(VERSION 3.8)
project(scara_hardware_interface)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()


find_package(ament_cmake REQUIRED)
find_package(CppLinuxSerial REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_lifecycle REQUIRED)
find_package(hardware_interface REQUIRED)
find_package(pluginlib REQUIRED)
include_directories(include)

add_library(
  ${PROJECT_NAME}
  SHARED
  src/${PROJECT_NAME}.cpp
)

target_link_libraries(${PROJECT_NAME} CppLinuxSerial::CppLinuxSerial)

ament_target_dependencies(${PROJECT_NAME} rclcpp rclcpp_lifecycle hardware_interface pluginlib CppLinuxSerial)

pluginlib_export_plugin_description_file(hardware_interface scara_hardware_interface.xml)

install(
  TARGETS ${PROJECT_NAME}
  DESTINATION lib
)

install(
  DIRECTORY include
  DESTINATION include
)

ament_export_libraries(
  ${PROJECT_NAME}
)

ament_export_dependencies(
  hardware_interface
  pluginlib
  rclcpp
  rclcpp_lifecycle
  CppLinuxSerial
)

ament_package()
