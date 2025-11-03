cmake_minimum_required(VERSION 3.5)
project(scanmatcher)

# C standards
if(NOT CMAKE_C_STANDARD)
  set(CMAKE_C_STANDARD 99)
endif()

# C++ standard
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

# Uncomment if you want to silence PCL_ROOT CMP0074 warnings
# cmake_policy(SET CMP0074 NEW)

# Build flags
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O2 -g")

# -----------------------
# Dependencies (ROS 2 + 3rd party)
# -----------------------
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_components REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2_sensor_msgs REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
find_package(tf2_eigen REQUIRED)
find_package(pcl_conversions REQUIRED)
find_package(pcl_msgs REQUIRED)
find_package(lidarslam_msgs REQUIRED)
find_package(ndt_omp_ros2 REQUIRED)
find_package(OpenCV REQUIRED)
find_package(OpenMP QUIET)

# PCL: 명시적인 컴포넌트를 적어주는 편이 안전합니다.
find_package(PCL REQUIRED COMPONENTS common io)

# GTSAM은 선택(imu_preintegration만 필요)
find_package(GTSAM QUIET)

# -----------------------
# Include / Compile defs
# -----------------------
# 프로젝트 공용 include (헤더 사용을 위해)
include_directories(
  include
  ${PCL_INCLUDE_DIRS}
  ${OpenCV_INCLUDE_DIRS}
)

add_definitions(${PCL_DEFINITIONS})

# -----------------------
# Component Library
# -----------------------
add_library(scanmatcher_component SHARED
  src/scanmatcher_component.cpp
)

target_compile_definitions(scanmatcher_component PRIVATE "GS_SM_BUILDING_DLL")

target_include_directories(scanmatcher_component
  PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

ament_target_dependencies(scanmatcher_component
  rclcpp
  rclcpp_components
  tf2_ros
  tf2_geometry_msgs
  tf2_sensor_msgs
  tf2_eigen
  pcl_conversions
  pcl_msgs
  geometry_msgs
  sensor_msgs
  nav_msgs
  lidarslam_msgs
  ndt_omp_ros2
  OpenCV
)

target_link_libraries(scanmatcher_component
  ${PCL_LIBRARIES}
  ${OpenCV_LIBRARIES}
)

if(OpenMP_CXX_FOUND)
  target_link_libraries(scanmatcher_component OpenMP::OpenMP_CXX)
endif()

# -----------------------
# Node Executable
# -----------------------
add_executable(scanmatcher_node
  src/scanmatcher_node.cpp
)

target_include_directories(scanmatcher_node
  PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

ament_target_dependencies(scanmatcher_node
  rclcpp
  pcl_conversions
  pcl_msgs
  geometry_msgs
  sensor_msgs
  nav_msgs
  tf2_ros
  tf2_geometry_msgs
  tf2_sensor_msgs
  tf2_eigen
  OpenCV
)

target_link_libraries(scanmatcher_node
  scanmatcher_component
  ${PCL_LIBRARIES}
  ${OpenCV_LIBRARIES}
)

if(OpenMP_CXX_FOUND)
  target_link_libraries(scanmatcher_node OpenMP::OpenMP_CXX)
endif()

# -----------------------
# image_projection (GTSAM 불필요 — 항상 빌드)
# -----------------------
add_executable(image_projection
  src/image_projection.cpp
)

target_include_directories(image_projection
  PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

ament_target_dependencies(image_projection
  rclcpp
  rclcpp_components
  tf2_ros
  tf2_geometry_msgs
  tf2_sensor_msgs
  tf2_eigen
  geometry_msgs
  sensor_msgs
  nav_msgs
  pcl_conversions
  pcl_msgs
  OpenCV
)

target_link_libraries(image_projection
  ${PCL_LIBRARIES}
  ${OpenCV_LIBRARIES}
)

if(OpenMP_CXX_FOUND)
  target_link_libraries(image_projection OpenMP::OpenMP_CXX)
endif()

# -----------------------
# imu_preintegration (GTSAM 필요 — 있을 때만 빌드)
# -----------------------
if(GTSAM_FOUND)
  add_executable(imu_preintegration
    src/imu_preintegration.cpp
  )

  target_include_directories(imu_preintegration
    PUBLIC
      $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
      $<INSTALL_INTERFACE:include>
  )

  ament_target_dependencies(imu_preintegration
    rclcpp
    rclcpp_components
    tf2_ros
    tf2_geometry_msgs
    tf2_sensor_msgs
    tf2_eigen
    geometry_msgs
    sensor_msgs
    nav_msgs
    pcl_msgs
    pcl_conversions
  )

  # GTSAM은 패키지에 따라 imported target(GTSAM::gtsam)을 제공하거나
  # 그냥 라이브러리 이름(gtsam)만 제공하는 경우가 있어 둘 다 시도합니다.
  if(TARGET GTSAM::gtsam)
    target_link_libraries(imu_preintegration GTSAM::gtsam)
  else()
    target_link_libraries(imu_preintegration gtsam)
  endif()

  target_link_libraries(imu_preintegration
    ${PCL_LIBRARIES}
    ${OpenCV_LIBRARIES}
  )

  if(OpenMP_CXX_FOUND)
    target_link_libraries(imu_preintegration OpenMP::OpenMP_CXX)
  endif()
endif()

# -----------------------
# Component registration
# -----------------------
rclcpp_components_register_nodes(scanmatcher_component
  "graphslam::ScanMatcherComponent"
)

# -----------------------
# Testing
# -----------------------
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

# -----------------------
# Export / Install
# -----------------------
ament_export_include_directories(include)
ament_export_libraries(scanmatcher_component)
ament_export_dependencies(
  rclcpp rclcpp_components
  tf2_ros tf2_geometry_msgs tf2_sensor_msgs tf2_eigen
  geometry_msgs sensor_msgs nav_msgs
  pcl_conversions pcl_msgs
  lidarslam_msgs ndt_omp_ros2
  OpenCV
)

install(
  DIRECTORY include/
  DESTINATION include
)

install(
  DIRECTORY launch param
  DESTINATION share/${PROJECT_NAME}
)

install(
  TARGETS
    scanmatcher_component
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

install(
  TARGETS
    scanmatcher_node
    image_projection
  RUNTIME DESTINATION lib/${PROJECT_NAME}
)

if(GTSAM_FOUND)
  install(
    TARGETS imu_preintegration
    RUNTIME DESTINATION lib/${PROJECT_NAME}
  )
endif()

ament_package()
