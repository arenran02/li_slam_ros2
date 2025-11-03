# this version is fit to walking dataset. 

import os

import launch
import launch.actions
import launch.substitutions
import launch_ros.actions
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    # params
    mapping_param_dir = LaunchConfiguration(
        "mapping_param_dir",
        default=os.path.join(
            get_package_share_directory("scanmatcher"),
            "param",
            "lio.yaml",
        ),
    )

    use_sim_time = LaunchConfiguration("use_sim_time", default="true")
    packets_to_deskewed = LaunchConfiguration("packets_to_deskewed", default="true")

    # Common remaps based on your bag
    # IMU: prefer the corrected one
    imu_remaps = [("/imu", "/imu_correct")]
    # LiDAR packets
    packet_remaps = [("/velodyne_packets", "/velodyne_packets")]
    # Raw point cloud
    raw_pc_remaps = [("/velodyne_points", "/points_raw"), ("/points_raw", "/points_raw")]

    # image_projection: turns packets+imu into /cloud_deskewed
    img_pro = launch_ros.actions.Node(
        package="scanmatcher",
        executable="image_projection",
        name="image_projection",
        parameters=[{"use_sim_time": use_sim_time}, mapping_param_dir],
        remappings=packet_remaps + imu_remaps + raw_pc_remaps,
        output="screen",
        condition=launch.conditions.IfCondition(packets_to_deskewed),
    )

    # scanmatcher: consume either /cloud_deskewed (preferred) or /points_raw
    # We create two nodes and enable exactly one with conditions for clarity.
    scanmatcher_from_deskewed = launch_ros.actions.Node(
        package="scanmatcher",
        executable="scanmatcher_node",
        name="scanmatcher",
        parameters=[{"use_sim_time": use_sim_time}, mapping_param_dir],
        remappings=[("/input_cloud", "/cloud_deskewed")],
        output="screen",
        condition=launch.conditions.IfCondition(packets_to_deskewed),
    )

    scanmatcher_from_raw = launch_ros.actions.Node(
        package="scanmatcher",
        executable="scanmatcher_node",
        name="scanmatcher_raw",
        parameters=[{"use_sim_time": use_sim_time}, mapping_param_dir],
        remappings=[("/input_cloud", "/points_raw")] + raw_pc_remaps,
        output="screen",
        condition=launch.conditions.UnlessCondition(packets_to_deskewed),
    )

    # IMU preintegration: subscribe to corrected IMU, publish odom (keep /odom, or remap to bag’s INS odom if you want to fuse)
    imu_pre = launch_ros.actions.Node(
        package="scanmatcher",
        executable="imu_preintegration",
        name="imu_preintegration",
        parameters=[{"use_sim_time": use_sim_time}, mapping_param_dir],
        remappings=imu_remaps + [("/odometry", "/odom")],  # publishes /odom
        output="screen",
    )

    # If graph_based_slam expects /odom and/or a keyframe/scan topic, it will pick them up.
    # Add remaps here if your graph_based_slam wants different names.
    graphbasedslam = launch_ros.actions.Node(
        package="graph_based_slam",
        executable="graph_based_slam_node",
        name="graph_based_slam",
        parameters=[{"use_sim_time": use_sim_time}, mapping_param_dir],
        # Example (uncomment/adjust if needed):
        # remappings=[("/odom_in", "/odom"),
        #             ("/scan_in", "/cloud_deskewed")],
        output="screen",
    )

    # static TF: velodyne relative to base_link (translation 0,0,0; quaternion 0,0,0,1)
    tf = launch_ros.actions.Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=["0", "0", "0", "0", "0", "0", "1", "base_link", "velodyne"],
        output="screen",
    )

    # Declarations
    return launch.LaunchDescription(
        [
            launch.actions.DeclareLaunchArgument(
                "mapping_param_dir",
                default_value=mapping_param_dir,
                description="Full path to mapping parameter file to load",
            ),
            launch.actions.DeclareLaunchArgument(
                "use_sim_time",
                default_value=use_sim_time,
                description="Use /clock from rosbag2 (recommended when playing bags)",
            ),
            launch.actions.DeclareLaunchArgument(
                "packets_to_deskewed",
                default_value=packets_to_deskewed,
                description="If true, use image_projection(/velodyne_packets+IMU) → /cloud_deskewed for scanmatcher. If false, use /points_raw directly.",
            ),
            # Nodes
            tf,
            img_pro,
            scanmatcher_from_deskewed,
            scanmatcher_from_raw,
            imu_pre,
            graphbasedslam,
        ]
    )
