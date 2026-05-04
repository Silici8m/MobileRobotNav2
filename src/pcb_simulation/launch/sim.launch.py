import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, PythonExpression

def generate_launch_description():
    # Définition des packages
    pkg_pcb_bringup = FindPackageShare("pcb_bringup")
    pkg_pcb_simulation = FindPackageShare("pcb_simulation")
    
    # Chemin absolu pour la variable d'environnement Gazebo
    pkg_sim_path = pkg_pcb_simulation.find("pcb_simulation")

    pos_x = LaunchConfiguration('x')
    pos_y = LaunchConfiguration('y')
    pos_yaw = LaunchConfiguration('yaw')
    headless = LaunchConfiguration('headless')
    


    declare_x = DeclareLaunchArgument('x', default_value='0.25')
    declare_y = DeclareLaunchArgument('y', default_value='1.75')
    declare_yaw = DeclareLaunchArgument('yaw', default_value='0.0')
    declare_headless = DeclareLaunchArgument(
        'headless', 
        default_value='false',
        description='Whether to run Gazebo without the GUI'
    )
    gz_extra_args = PythonExpression([
        "'-s' if '", headless, "' == 'true' else ''"
    ])

    # Changement ici : le monde est dans pcb_simulation
    world_path = PathJoinSubstitution([pkg_pcb_simulation, "worlds", "arena.sdf"])

    # 1. L'ENVIRONNEMENT : GAZEBO
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([FindPackageShare("ros_gz_sim"), "launch", "gz_sim.launch.py"])
        ]),
        launch_arguments={
            "gz_args": ["-r -v 4 --physics-engine gz-physics-dartsim-plugin ", world_path, " ", gz_extra_args]
        }.items(),
    )

    # 2. LE CERVEAU : Lancement de l'Autonomie
    # L'autonomie reste dans pcb_bringup
    autonomy = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([pkg_pcb_bringup, "launch", "autonomy.launch.py"])
        ]),
        launch_arguments={
            'use_sim_time': 'true',
            'use_sim': 'true',
            'x': pos_x,
            'y': pos_y,
            'yaw': pos_yaw
        }.items()
    )

    return LaunchDescription([
        declare_x,
        declare_y,
        declare_yaw,
        declare_headless,
        # Changement ici : la variable pointe vers pcb_simulation
        SetEnvironmentVariable(
            name='GZ_SIM_RESOURCE_PATH',
            value=pkg_sim_path
        ),

        gazebo,

        # 3. LES PONTS (BRIDGES) : Connecter Gazebo à ROS 2
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
            parameters=[{'use_sim_time': True}],
            output='screen'
        ),
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            parameters=[{'use_sim_time': True}],
            arguments=['/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan']
        ),
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            parameters=[{'use_sim_time': True}],
            arguments=['/imu@sensor_msgs/msg/Imu[gz.msgs.IMU']
        ),

        # 4. APPARITION DU ROBOT (SPAWN)
        Node(
            package='ros_gz_sim',
            executable='create',
            arguments=[
                '-name', 'simple_robot',
                '-topic', 'robot_description',
                '-x', pos_x,
                '-y', pos_y,
                '-z', '0.0',
                '-Y', pos_yaw
            ],
            parameters=[{'use_sim_time': True}],
            output='screen'
        ),

        Node(
            package="pcb_simulation",
            executable="gt_node",
            parameters=[{'use_sim_time': True}]
        ),

        autonomy
    ])