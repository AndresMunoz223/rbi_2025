cmake_minimum_required(VERSION 3.8)
project(scara_hardware_interface)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()


find_package(ament_cmake REQUIRED)
find_package(CppLinuxSerial REQUIRED)

# target_link_libraries(target CppLinuxSerial::CppLinuxSerial)

ament_package()
