# Attribution

- ROS 2 Humble: https://docs.ros.org/en/humble/ (Apache-2.0)
- Gazebo Classic: https://classic.gazebosim.org/ and gazebo_ros_pkgs: https://github.com/ros-simulation/gazebo_ros_pkgs
- TurtleBot3 (ROBOTIS), `turtlebot3_gazebo`: https://emanual.robotis.com/docs/en/platform/turtlebot3/simulation/ ,
  https://github.com/ROBOTIS-GIT/turtlebot3_simulations (Apache-2.0)
- Key layout and idea inspired by `teleop_twist_keyboard`: https://github.com/ros2/teleop_twist_keyboard (BSD-3-Clause)
- Test environment packages: RoboStack https://robostack.github.io/ and conda-forge.

## Earlier prototype
The author and a friend built a rough earlier prototype (custom 4-wheel robot, basic and advanced teleop
nodes). The ideas for speed smoothing, a deadman switch and the key bindings come from it. The launch and
packaging files of that prototype did not run as shipped (details in REPORT.md), so this project is a new,
smaller implementation on TurtleBot3 and its code was rewritten and tested. The author should state this
prior collaboration to the instructor if the course requires disclosure of shared work.

## AI assistance
The code and documents in this repository were produced with AI assistance (the course permits AI help
for code, as confirmed by the author). The author is expected to understand and demonstrate the work.
