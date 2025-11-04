import os

import launch
import launch_ros.actions

from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    mapping_param_dir = launch.substitutions.LaunchConfiguration(
        'mapping_param_dir',
        default=os.path.join(
            get_package_share_directory('scanmatcher'),
            'param',
            'lio.yaml')
    )

    # --- Mapping (LIO) ---
    # 현재 deskew 토픽이 없으므로 임시로 /points_raw를 바로 입력에 연결
    mapping = launch_ros.actions.Node(
        package='scanmatcher',
        executable='scanmatcher_node',
        parameters=[mapping_param_dir],
        remappings=[
            ('/input_cloud', '/points_raw'),   # TODO: /cloud_deskewed로 바꿀 예정
            ('/imu', '/imu_raw'),              # rqt_graph 기준 실제 들어오는 IMU
        ],
        output='screen'
    )

    # --- Graph-based backend ---
    graphbasedslam = launch_ros.actions.Node(
        package='graph_based_slam',
        executable='graph_based_slam_node',
        parameters=[mapping_param_dir],
        remappings=[
            ('/gps/fix', '/gx5/gps/fix'),
            ('/odometry', '/gx5/nav/odom'),
        ],
        output='screen'
    )

    # --- Static TF: velodyne -> base_link ---
    tf = launch_ros.actions.Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0','0','0','0','0','0','1','base_link','velodyne']
    )

    # --- IMU Preintegration ---
    imu_pre = launch_ros.actions.Node(
        package='scanmatcher',
        executable='imu_preintegration',
        parameters=[mapping_param_dir],
        remappings=[
            ('/odometry', '/gx5/nav/odom'),
            ('/imu', '/imu_raw'),              # 실제 들어오는 IMU 사용
        ],
        output='screen'
    )

    # --- Image/Scan Projection ---
    # 실행은 유지하되, 출력 토픽명이 무엇인지 확인 후 아래 라인 교체 예정
    # 예: 실제가 /deskewed_points면 ('/cloud_deskewed','/deskewed_points') 로 수정
    img_pro = launch_ros.actions.Node(
        package='scanmatcher',
        executable='image_projection',
        parameters=[mapping_param_dir],
        remappings=[
            ('/points_raw', '/points_raw'),
            ('/imu', '/imu_raw'),
            # ('/cloud_deskewed', '/deskewed_points'),  # ← 실제 퍼블 이름 확인 후 사용
        ],
        output='screen'
    )

    return launch.LaunchDescription([
        launch.actions.DeclareLaunchArgument(
            'mapping_param_dir',
            default_value=mapping_param_dir,
            description='Full path to mapping parameter file to load'
        ),
        mapping,
        tf,
        imu_pre,
        img_pro,
        graphbasedslam,
    ])
