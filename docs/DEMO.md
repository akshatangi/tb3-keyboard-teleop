# Demo and explanation guide

Use this project only if it matches your instructor's rules. AI assistance and the earlier shared prototype are disclosed in ATTRIBUTION.md. Read the code and practise the demo yourself before submitting.

## Before the demo
1. Confirm the VM is Ubuntu 22.04 and the installed stack is ROS 2 Humble + Gazebo Classic 11. Do not run the Humble instructions on Ubuntu 24.04.
2. Build and source the workspace as README.md describes.
3. Run the unit tests. Start the empty world and check that the robot appears.
4. Keep only one command publisher running. Do not run the keyboard node and scripted test together.

## A short demonstration
- Terminal 1: `ros2 launch tb3_keyboard_teleop sim.launch.py world:=empty_world.world x_pose:=0.0 y_pose:=0.0`.
- Terminal 2, after sourcing ROS and this workspace: `ros2 run tb3_keyboard_teleop keyboard_teleop`.
- Hold w and show forward motion. Release it and show the deadman stop.
- Hold s, a and d in turn. Use SPACE between commands.
- Try q and e for forward turning arcs, then SPACE.
- Use u/j to change linear speed, i/k for angular speed, v to print the current command.
- Press CTRL-C and show that the robot stops and the terminal returns normally.
- Stop the keyboard node, then run `ros2 run tb3_keyboard_teleop scripted_test` to show the measured checks.
- Record your own short video or screenshots on the VM, noting its actual versions. Existing evidence in docs/ was captured during the development tests, not on your M1.

## Explain the system in your own words
- The node does not move a motor directly. It publishes a Twist message on /cmd_vel. linear.x is forward speed in m/s; angular.z is yaw speed in rad/s.
- Gazebo's differential-drive plugin converts the command to wheel motion. /odom reports motion back.
- A movement key chooses a target velocity. Each update moves the current velocity toward the target, limited by acceleration.
- SPACE sets the target to zero; it ramps down rather than stopping instantly. CTRL-C sends zero before shutdown.
- The deadman sets the target to zero when no movement key arrives for 0.6 seconds. Terminal auto-repeat provides repeated keys while held. It is not obstacle avoidance.
- Logic tests check key maps, limits, smoothing and timeout without ROS. Simulation tests check real odometry. The pseudo-terminal test exercises the actual keyboard node.

## If something fails
Save the complete error, `lsb_release -a`, `uname -m`, `printenv ROS_DISTRO`, and the commands you ran. Keep the error text free of passwords or tokens. Do not invent a successful result or paste development results as measurements from your own VM.
