import os

from launch.actions import SetEnvironmentVariable

import launch
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

from launch.substitutions import Command, PathJoinSubstitution
from launch_ros.parameter_descriptions import ParameterValue

from launch_ros.actions import LifecycleNode
from launch.actions import EmitEvent, RegisterEventHandler
from launch_ros.events.lifecycle import ChangeState
from launch_ros.event_handlers import OnStateTransition
from launch.events import matches_action
import lifecycle_msgs.msg

import launch_ros

from launch.actions import TimerAction


packageName = "car"
worldRelativePath            = "worlds/arena.sdf"
rvizConfigRelativePath       = "config/rviz/config.rviz"
controllerParamsRelativePath = "config/sim/controller_params.yaml"
robotControllerRelativePath  = "config/sim/robot_controller.yaml"
nav2ParamsRelativePath       = "config/sim/nav2_params.yaml"
ekfConfigRelativePath        = "config/ekf.yaml"
mapFileRelativePath          = "config/map/map_cdfr_simple.yaml"

def generate_launch_description():

    pkgPath              = launch_ros.substitutions.FindPackageShare(package=packageName).find(packageName)
    world_path           = os.path.join(pkgPath, worldRelativePath)
    rvizConfigPath       = os.path.join(pkgPath, rvizConfigRelativePath)
    controllerParamsPath = os.path.join(pkgPath, controllerParamsRelativePath)
    robotControllerPath  = os.path.join(pkgPath, robotControllerRelativePath)
    #ekfConfigPath        = os.path.join(pkgPath, ekfConfigRelativePath)
    nav2ParamsPath       = os.path.join(pkgPath, nav2ParamsRelativePath)
    mapFilePath          = os.path.join(pkgPath, mapFileRelativePath)    

    # Paramètres du jenga_manager
    jengaParamsPath = PathJoinSubstitution([
        FindPackageShare("jenga_manager"),
        "config",
        "params.yaml"
    ])  
    
    robot_description = ParameterValue(
        Command([
            'xacro ',
            PathJoinSubstitution([
                FindPackageShare(packageName), 
                "urdf",
                #"localization-robot",
                "robot.xacro"
            ])
        ]),
        value_type=str
    )

    # --- GAZEBO (ton style) ---
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                PathJoinSubstitution([
                    FindPackageShare("ros_gz_sim"),
                    "launch",
                    "gz_sim.launch.py"
                ])
            ]
        ),
        launch_arguments={
            "gz_args": [
                "-r -v 4 --physics-engine gz-physics-dartsim-plugin ",
                world_path
            ]
        }.items(),
    )

    return LaunchDescription([

        SetEnvironmentVariable(
            name='GZ_SIM_RESOURCE_PATH',
            value=pkgPath
        ),
        
        launch_ros.actions.SetParameter(name='use_sim_time', value=True),

        gazebo,

        # Bridges

        #Clock
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
            parameters=[{'use_sim_time': True}],
            output='screen'
        ),

        # Lidar
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            parameters=[{'use_sim_time': True}],
            arguments=[
                '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            ]
        ),

        # Imu
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            parameters=[{'use_sim_time': True}],
            arguments=[
                '/imu@sensor_msgs/msg/Imu[gz.msgs.IMU',
            ]
        ),


        # Spawn robot in Gazebo
        Node(
            package='ros_gz_sim',
            executable='create',
            arguments=[
                '-name', 'simple_robot',
                '-topic', 'robot_description',
                '-x', '0.3',
                '-y', '0.3',
                '-z', '0.0'
            ],
            parameters=[{
                'use_sim_time': True
            }],
            output='screen'
        ),

        # robot_state_publisher
        TimerAction(
            period=2.0,
            actions=[
                Node(
                    package="robot_state_publisher",
                    executable="robot_state_publisher",
                    output="both",
                    parameters=[{
                        "robot_description":robot_description,
                        "use_sim_time": True
                    }]
                ),
            ]
        ),

        Node( 
            package='tf2_ros', 
            executable='static_transform_publisher', 
            arguments=['--x', '0.3', '--y', '0.3', '--z', '0',
           '--roll', '0', '--pitch', '0', '--yaw', '0',
           '--frame-id', 'map', '--child-frame-id', 'odom'], 
            parameters=[{'use_sim_time': True}], 
        ),

        # RViz
        Node(
            package='rviz2',
            executable='rviz2',
            parameters=[{'use_sim_time': True}],
            arguments=["-d", rvizConfigPath],
            output='screen'
        ),


        # Controllers
        TimerAction(
            period=3.0,
            actions=[
                Node(
                    package="controller_manager",
                    executable="spawner",
                    arguments=["joint_state_broadcaster"],
                    parameters=[{'use_sim_time': True}],
                ),
                Node(
                    package="controller_manager",
                    executable="spawner",
                    arguments=["omni_wheel_drive_controller", "--param-file", robotControllerPath],
                    parameters=[{'use_sim_time': True}],
                ),
            ],
        ),

        Node(
            package="car",
            executable="car_controller",
            parameters = [controllerParamsPath, {'use_sim_time': True}]
        ),

        Node(
            package="car",
            executable="gt_node"
        ),

        # EKF
        # TimerAction(
        #     period=3.5,
        #     actions=[
        #         Node(
        #             package="robot_localization",
        #             executable="ekf_node",
        #             name="ekf_filter_node",
        #             output="screen",
        #             parameters=[ekfConfigPath, {'use_sim_time': True}],
        #         ),
        #     ]
        # ),

        # NAV2
        TimerAction(
            period=7.0,
            actions=[
                Node(
                    package='jenga_manager',
                    executable='jenga_manager_node',
                    name='jenga_manager',
                    output='screen',
                    parameters=[{'use_sim_time': True}, jengaParamsPath]
                ),
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        PathJoinSubstitution([
                            # FindPackageShare("nav2_bringup"),
                            FindPackageShare("car"),
                            "launch",
                            "bringup_launch.py"
                        ])
                    ),
                    launch_arguments={
                        "slam": "False",
                        "map": mapFilePath,
                        "use_sim_time": "true",
                        "params_file": nav2ParamsPath,
                        "autostart": "true"
                    }.items(),
                ),
            ]
        ),



    ])