# Keyboard-Based Teleoperation of a Simulated TurtleBot3 (ROS 2 + Gazebo)

Course project (ROS 2 & Robotics Simulation, option 2): control a simulated
TurtleBot3 with keyboard commands and test different movement commands.

Target stack: **Ubuntu 22.04, ROS 2 Humble, Gazebo Classic 11, TurtleBot3 (burger)**.

## What it does
- `keyboard_teleop` node: reads keys from the terminal, publishes `geometry_msgs/Twist` on `/cmd_vel`.
- Smooth acceleration (no instant jumps), speed limits of the TurtleBot3 burger (0.22 m/s, 2.84 rad/s),
  adjustable speeds, a deadman timeout (robot stops if keys stop arriving), and a final zero-velocity command on CTRL-C.
- `sim.launch.py`: starts Gazebo + TurtleBot3 (world selectable, headless option).
- `scripted_test`: automated movement test that checks `/odom` against the commands.

## Keys
| Key | Action |
|---|---|
| w / s | forward / backward |
| a / d | rotate left / right |
| q / e | forward + turn left / right |
| z / c | backward + turn (reverse arcs) |
| SPACE or x | stop |
| u / j | linear speed + / - |
| i / k | angular speed + / - |
| p | toggle deadman |
| v | print current velocity |
| CTRL-C | quit (robot is stopped first) |

Hold a movement key (terminal key-repeat keeps it alive). With the deadman on, the robot stops
after 0.6 s without a movement key plus the ramp-down time.

## Install (Ubuntu 22.04 + ROS 2 Humble, apt)
First install ROS 2 Humble using the official Ubuntu Debian-package guide below, including its repository setup. These commands assume that setup is complete. Check `lsb_release -rs` (must be 22.04) and `uname -m` first. On an M1 VM, aarch64 is expected but not yet verified here. This legacy Gazebo Classic stack is end-of-life; it is retained for compatibility with the tested project.

```bash
sudo apt update
sudo apt install ros-humble-desktop ros-humble-gazebo-ros-pkgs \
     ros-humble-turtlebot3-gazebo python3-colcon-common-extensions
echo "export TURTLEBOT3_MODEL=burger" >> ~/.bashrc
source /opt/ros/humble/setup.bash
```
(Official guides: https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html and
https://emanual.robotis.com/docs/en/platform/turtlebot3/simulation/ )

## Build
```bash
git clone https://github.com/akshat-jarvis/tb3-keyboard-teleop.git
cd tb3-keyboard-teleop
source /opt/ros/humble/setup.bash
colcon build
source install/setup.bash
export TURTLEBOT3_MODEL=burger
```

## Run (two terminals)
Terminal 1 (simulation):
```bash
ros2 launch tb3_keyboard_teleop sim.launch.py            # TurtleBot3 world, with GUI
ros2 launch tb3_keyboard_teleop sim.launch.py world:=empty_world.world
ros2 launch tb3_keyboard_teleop sim.launch.py gui:=false # headless
```
Terminal 2 (keyboard, needs its own terminal):
```bash
source /opt/ros/humble/setup.bash
source install/setup.bash && export TURTLEBOT3_MODEL=burger
ros2 run tb3_keyboard_teleop keyboard_teleop
```
Optional RViz: `ros2 run rviz2 rviz2` (add RobotModel, LaserScan `/scan`, Odometry `/odom`).

## Tests
```bash
PYTHONPATH=src/tb3_keyboard_teleop python3 -m pytest src/tb3_keyboard_teleop/test              # logic tests, no ROS needed
# with the simulation running (empty world recommended):
ros2 service call /reset_simulation std_srvs/srv/Empty
ros2 run tb3_keyboard_teleop scripted_test                  # prints PASS/FAIL per command
python3 scripts/pty_keyboard_test.py                        # types keys into the real node
```

## What has actually been verified (and what has not)
Tested environment (not the same as an apt install): x86_64 Ubuntu 22.04 container, ROS 2 Humble and
Gazebo Classic 11.15 from conda-forge/RoboStack, `turtlebot3_gazebo` 2.3.8, Python 3.14, 2 CPU cores,
headless `gzserver`; one run with `gzclient` on a virtual display for the screenshots in `docs/`.
- 11/11 unit tests pass.
- `scripted_test`: 7/7 passed (see `docs/scripted_test_run.txt`).
- `pty_keyboard_test.py` (real node, keys typed through a pseudo-terminal): 8/8 passed in two clean
  runs (`docs/pty_keyboard_test_run*.txt`).
- Not tested: the apt install steps above, an ARM64 (Apple M1) Ubuntu VM, the TurtleBot3 *house*
  world, RViz, a physical keyboard on a real desktop, and ROS 2 distributions other than Humble.
  If something breaks on your VM, send the error text.

## Layout
```
src/tb3_keyboard_teleop/
  tb3_keyboard_teleop/teleop_logic.py          key map, speed limits, smoothing, deadman (pure Python)
  tb3_keyboard_teleop/keyboard_teleop_node.py  ROS 2 node (terminal input -> /cmd_vel)
  tb3_keyboard_teleop/scripted_test.py         automated movement test
  launch/sim.launch.py   config/teleop.yaml   test/test_teleop_logic.py
scripts/pty_keyboard_test.py   docs/   REPORT.md   ATTRIBUTION.md
```

## Credits
See [ATTRIBUTION.md](ATTRIBUTION.md).

Configuration: `ros2 run tb3_keyboard_teleop keyboard_teleop --ros-args --params-file src/tb3_keyboard_teleop/config/teleop.yaml` loads the supplied parameters. Do not run more than one teleop/test publisher at a time. Stop the keyboard node before starting either automated test.
