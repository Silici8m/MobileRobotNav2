import os

from launch.actions import SetEnvironmentVariable

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

from launch.substitutions import Command, PathJoinSubstitution
from launch_ros.parameter_descriptions import ParameterValue

import launch_ros



packageName = "pcb_bringup"
worldRelativePath            = "worlds/arena.sdf"

def generate_launch_description():

    pkgPath              = launch_ros.substitutions.FindPackageShare(package=packageName).find(packageName)
    world_path           = os.path.join(pkgPath, worldRelativePath) 
    
    robot_description = ParameterValue(
        Command([
            'xacro ',
            PathJoinSubstitution([
                FindPackageShare(packageName), 
                "urdf",
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


        Node(
            package="car",
            executable="gt_node"
        ),

    ])