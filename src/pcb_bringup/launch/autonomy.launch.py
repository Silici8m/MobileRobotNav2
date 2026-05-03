import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node, SetParameter
from launch_ros.substitutions import FindPackageShare

from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution, PythonExpression
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    pkg_pcb_bringup = FindPackageShare("pcb_bringup")

    # Position initiale
    
    # 1. DÉCLARATION DE L'ARGUMENT DYNAMIQUE

    pos_x = LaunchConfiguration('x')
    pos_y = LaunchConfiguration('y')
    pos_yaw = LaunchConfiguration('yaw')
    # C'est sim.launch ou real.launch qui décude la valeur de use_sim_time
    use_sim = LaunchConfiguration('use_sim')
    use_sim_time = LaunchConfiguration('use_sim_time')

    declare_x = DeclareLaunchArgument('x', default_value='0.25', description='Initial X')
    declare_y = DeclareLaunchArgument('y', default_value='1.75', description='Initial Y')
    declare_yaw = DeclareLaunchArgument('yaw', default_value='0.0', description='Initial Yaw')
    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation (Gazebo) clock if true'
    )
    declare_use_sim = DeclareLaunchArgument('use_sim', default_value='false', description='Force Gazebo plugins if true')

    # RViz est maintenant dans pcb_description
    rvizConfigPath = PathJoinSubstitution([FindPackageShare("pcb_description"), "config", "rviz", "config.rviz"])
    
    # La carte reste statique dans pcb_bringup
    mapFilePath = PathJoinSubstitution([pkg_pcb_bringup, "config", "map", "map_cdfr_simple.yaml"])

    # LA MAGIE ROS 2 : Sélectionne le dossier "sim" ou "real" selon l'argument use_sim
    config_folder = PythonExpression(['"sim" if "', use_sim, '" == "true" else "real"'])

    # Construction dynamique des chemins
    controllerParamsPath = PathJoinSubstitution([pkg_pcb_bringup, "config", config_folder, "controller_params.yaml"])
    robotControllerPath  = PathJoinSubstitution([pkg_pcb_bringup, "config", config_folder, "robot_controller.yaml"])
    nav2ParamsPath       = PathJoinSubstitution([pkg_pcb_bringup, "config", config_folder, "nav2_params.yaml"])

    lifecycle_nodes = [
        'jenga_manager',
    ]

    # Paramètres du jenga_manager
    jengaParamsPath = PathJoinSubstitution([
        FindPackageShare("jenga_manager"),
        "config",
        "params.yaml"
    ])
    
    # 2. XACRO DYNAMIQUE
    # On passe la variable use_sim_time à l'argument use_sim du xacro
    robot_description = ParameterValue(
        Command([
            'xacro ',
            PathJoinSubstitution([FindPackageShare("pcb_description"), "urdf", "robot.xacro"]),
            ' use_sim:=', use_sim
        ]),
        value_type=str
    )

    return LaunchDescription([
        # On ajoute la déclaration au LaunchDescription
        declare_use_sim_time,
        declare_use_sim,
        declare_x,
        declare_y,
        declare_yaw,

        # Configure automatiquement tous les noeuds de ce launch file pour utiliser use_sim_time
        SetParameter(name='use_sim_time', value=use_sim_time),

        # robot_state_publisher
        TimerAction(
            period=2.0,
            actions=[
                Node(
                    package="robot_state_publisher",
                    executable="robot_state_publisher",
                    output="both",
                    parameters=[{
                        "robot_description": robot_description,
                        "use_sim_time": use_sim_time
                    }]
                ),
            ]
        ),

        Node( 
            package='tf2_ros', 
            executable='static_transform_publisher', 
            arguments=['--x', pos_x, '--y', pos_y, '--z', '0',
                       '--roll', '0', '--pitch', '0', '--yaw', pos_yaw,
                       '--frame-id', 'map', '--child-frame-id', 'odom'],
            parameters=[{'use_sim_time': use_sim_time}], 
        ),

        # RViz
        Node(
            package='rviz2',
            executable='rviz2',
            parameters=[{'use_sim_time': use_sim_time}],
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
                    parameters=[{'use_sim_time': use_sim_time}],
                ),
                Node(
                    package="controller_manager",
                    executable="spawner",
                    arguments=["omni_wheel_drive_controller", "--param-file", robotControllerPath],
                    parameters=[{'use_sim_time': use_sim_time}],
                ),
            ],
        ),

        Node(
            package="car",
            executable="car_controller",
            parameters = [controllerParamsPath, {'use_sim_time': use_sim_time}]
        ),

        Node(
            package="car",
            executable="gt_node",
            parameters=[{'use_sim_time': use_sim_time}]
        ),

        # NAV2 & JENGA
        TimerAction(
            period=7.0,
            actions=[
                Node(
                    package='jenga_manager',
                    executable='jenga_manager_node',
                    name='jenga_manager',
                    output='screen',
                    parameters=[{'use_sim_time': use_sim_time}, jengaParamsPath]
                ),
                Node(
                    package='nav2_lifecycle_manager',
                    executable='lifecycle_manager',
                    name='lifecycle_manager_application',
                    output='screen',
                    parameters=[
                        {'use_sim_time': use_sim_time},
                        {'autostart': True},
                        {'node_names': lifecycle_nodes},
                        {'bond_timeout': 0.0} # Pas de bonds pour ce petit manager
                    ]
                ),
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        PathJoinSubstitution([pkg_pcb_bringup, "launch", "bringup_launch.py"])
                    ),
                    launch_arguments={
                        "slam": "False",
                        "map": mapFilePath,
                        "use_sim_time": use_sim_time,
                        "params_file": nav2ParamsPath,
                        "autostart": "true"
                    }.items(),
                ),
            ]
        ),
    ])