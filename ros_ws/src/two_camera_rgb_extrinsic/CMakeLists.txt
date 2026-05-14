cmake_minimum_required(VERSION 3.0.2)
project(two_camera_rgb_extrinsic)

find_package(catkin REQUIRED COMPONENTS
  cv_bridge
  message_filters
  rospy
  sensor_msgs
  std_msgs
)

catkin_package()

catkin_install_python(PROGRAMS
  scripts/capture_rgb_pairs.py
  scripts/estimate_rgb_extrinsics.py
  scripts/launch_dual_d435i_rgb.py
  scripts/print_realsense_devices.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)
