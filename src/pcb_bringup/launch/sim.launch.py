import os

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import PathJoinSubstitution

def generate_launch_description():
    # Définition des packages
    pkg_pcb_bringup = FindPackageShare("pcb_bringup")
    pkgPath = pkg_pcb_bringup.find("pcb_bringup")
    
    world_path = PathJoinSubstitution([pkg_pcb_bringup, "worlds", "arena.sdf"])

    # 1. L'ENVIRONNEMENT : GAZEBO
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([FindPackageShare("ros_gz_sim"), "launch", "gz_sim.launch.py"])
        ]),
        launch_arguments={
            "gz_args": ["-r -v 4 --physics-engine gz-physics-dartsim-plugin ", world_path]
        }.items(),
    )

    # 2. LE CERVEAU : Lancement de l'Autonomie
    # On force 'use_sim_time' à 'true' car on est dans le simulateur
    autonomy = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([pkg_pcb_bringup, "launch", "autonomy.launch.py"])
        ]),
        launch_arguments={
            'use_sim_time': 'true'
        }.items()
    )

    return LaunchDescription([
        # Variables d'environnement pour Gazebo
        SetEnvironmentVariable(
            name='GZ_SIM_RESOURCE_PATH',
            value=pkgPath
        ),

        gazebo,

        # 3. LES PONTS (BRIDGES) : Connecter Gazebo à ROS 2
        # Horloge
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
            arguments=['/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan']
        ),
        # IMU
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            parameters=[{'use_sim_time': True}],
            arguments=['/imu@sensor_msgs/msg/Imu[gz.msgs.IMU']
        ),

        # 4. APPARITION DU ROBOT (SPAWN)
        # Gazebo écoute le topic /robot_description publié par autonomy.launch.py
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
            parameters=[{'use_sim_time': True}],
            output='screen'
        ),

        # Démarrage de la logique robotique
        autonomy
    ])