# CMake generated Testfile for 
# Source directory: /home/eia/repo/rbi_2025_2/abb/abb_bridge/src/abb_ros2/abb_bringup
# Build directory: /home/eia/repo/rbi_2025_2/abb/abb_bridge/build/abb_bringup
# 
# This file includes the relevant testing commands required for 
# testing this directory and lists subdirectories to be tested as well.
add_test(test_launch_test_command_topics.test.py "/usr/bin/python3" "-u" "/opt/ros/humble/share/ament_cmake_test/cmake/run_test.py" "/home/eia/repo/rbi_2025_2/abb/abb_bridge/build/abb_bringup/test_results/abb_bringup/test_launch_test_command_topics.test.py.xunit.xml" "--package-name" "abb_bringup" "--output-file" "/home/eia/repo/rbi_2025_2/abb/abb_bridge/build/abb_bringup/ros_test/test_launch_test_command_topics.test.py.txt" "--command" "ros2" "test" "/home/eia/repo/rbi_2025_2/abb/abb_bridge/src/abb_ros2/abb_bringup/test/launch/test_command_topics.test.py" "test_binary_dir:=/home/eia/repo/rbi_2025_2/abb/abb_bridge/build/abb_bringup" "--junit-xml=/home/eia/repo/rbi_2025_2/abb/abb_bridge/build/abb_bringup/test_results/abb_bringup/test_launch_test_command_topics.test.py.xunit.xml" "--package-name=abb_bringup")
set_tests_properties(test_launch_test_command_topics.test.py PROPERTIES  TIMEOUT "120" WORKING_DIRECTORY "/home/eia/repo/rbi_2025_2/abb/abb_bridge/build/abb_bringup" _BACKTRACE_TRIPLES "/opt/ros/humble/share/ament_cmake_test/cmake/ament_add_test.cmake;125;add_test;/opt/ros/humble/share/ros_testing/cmake/add_ros_test.cmake;73;ament_add_test;/home/eia/repo/rbi_2025_2/abb/abb_bridge/src/abb_ros2/abb_bringup/CMakeLists.txt;19;add_ros_test;/home/eia/repo/rbi_2025_2/abb/abb_bridge/src/abb_ros2/abb_bringup/CMakeLists.txt;0;")
subdirs("gtest")
