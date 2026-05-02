import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution

def generate_launch_description():
    pkg_pcb_bringup = FindPackageShare("pcb_bringup")

    pos_x = LaunchConfiguration('x')
    pos_y = LaunchConfiguration('y')
    pos_yaw = LaunchConfiguration('yaw')

    declare_x = DeclareLaunchArgument('x', default_value='0.25')
    declare_y = DeclareLaunchArgument('y', default_value='1.75')
    declare_yaw = DeclareLaunchArgument('yaw', default_value='0.0')


    # Chemin vers les paramètres du contrôleur réel
    # Attention: Assure-toi que ce dossier/fichier existe bien dans pcb_bringup !
    real_controller_path = PathJoinSubstitution([
        pkg_pcb_bringup, "config", "real", "robot_controller.yaml"
    ])

    # 1. LE MATÉRIEL : Lancement du Controller Manager natif
    # Il va charger ton plugin MicroRosHardwareInterface et faire le lien avec l'ESP32
    controller_manager = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[real_controller_path],
        # Remapping essentiel pour que le manager trouve l'URDF publié par autonomy
        remappings=[
            ('~/robot_description', '/robot_description'),
        ],
        output="screen"
    )

    # 2. LES CAPTEURS : Driver Lidar Physique
    # lidar_node = Node(
    #     package='ldlidar_stl_ros2',
    #     executable='ldlidar_stl_ros2_node',
    #     name='LD19',
    #     output='screen',
    #     parameters=[
    #         {'product_name': 'LDLiDAR_LD19'},
    #         {'topic_name': 'scan'},
    #         {'frame_id': 'lidar_link'},
    #         {'port_name': '/dev/ttyUSB0'},
    #         {'port_baudrate': 230400},
    #         {'laser_scan_dir': True},
    #         {'enable_angle_crop_func': False},
    #         {'angle_crop_min': 135.0},
    #         {'angle_crop_max': 225.0}
    #     ]
    # )

    # (Optionnel) Bridge topic relay pour micro_ros si utilisé directement sans hardware_interface
    # relay_node = Node(
    #     package='topic_tools',
    #     executable='relay',
    #     arguments=['/micro_controller/joint_states', '/joint_states'],
    #     output='screen'
    # )

    # 3. LE CERVEAU : Lancement de l'Autonomie
    # On force 'use_sim_time' à 'false' car on est sur le robot physique
    autonomy = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([pkg_pcb_bringup, "launch", "autonomy.launch.py"])
        ]),
        launch_arguments={
            'use_sim_time': 'false',
            'x': pos_x,
            'y': pos_y,
            'yaw': pos_yaw
        }.items()
    )

    return LaunchDescription([
        declare_x,
        declare_y,
        declare_yaw,
        controller_manager,
        #lidar_node,
        autonomy
    ])