"""Start Gazebo with the TurtleBot3 world and the TurtleBot3 robot.

The keyboard node is NOT started here because it needs its own terminal
(a real keyboard). Run it separately:  ros2 run tb3_keyboard_teleop keyboard_teleop

Arguments:
  world:=turtlebot3_world.world | empty_world.world | turtlebot3_house.world
  gui:=true|false         (false = headless gzserver only)
  x_pose:=-2.0 y_pose:=-0.5
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    gazebo_ros = get_package_share_directory('gazebo_ros')
    tb3 = get_package_share_directory('turtlebot3_gazebo')

    world = PathJoinSubstitution([FindPackageShare('turtlebot3_gazebo'), 'worlds',
                                  LaunchConfiguration('world')])
    gzserver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(gazebo_ros, 'launch', 'gzserver.launch.py')),
        launch_arguments={'world': world}.items())
    gzclient = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(gazebo_ros, 'launch', 'gzclient.launch.py')),
        condition=IfCondition(LaunchConfiguration('gui')))
    robot_state = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(tb3, 'launch', 'robot_state_publisher.launch.py')),
        launch_arguments={'use_sim_time': 'true'}.items())
    spawn = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(tb3, 'launch', 'spawn_turtlebot3.launch.py')),
        launch_arguments={'x_pose': LaunchConfiguration('x_pose'),
                          'y_pose': LaunchConfiguration('y_pose')}.items())

    return LaunchDescription([
        DeclareLaunchArgument('world', default_value='turtlebot3_world.world'),
        DeclareLaunchArgument('gui', default_value='true'),
        DeclareLaunchArgument('x_pose', default_value='-2.0'),
        DeclareLaunchArgument('y_pose', default_value='-0.5'),
        gzserver, gzclient, robot_state, spawn,
    ])
