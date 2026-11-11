#!/usr/bin/env python3
"""End-to-end test of the REAL keyboard node.

Starts `ros2 run tb3_keyboard_teleop keyboard_teleop` inside a pseudo-terminal,
types keys into it like a person would, and checks /odom from the running
Gazebo simulation. Needs the simulation to be running already.
"""
import math
import os
import pty
import select
import subprocess
import sys
import time

import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data


def yaw_of(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


rclpy.init()
node = Node('pty_keyboard_test')
pose = [None]
node.create_subscription(Odometry, '/odom', lambda m: pose.__setitem__(
    0, (m.pose.pose.position.x, m.pose.pose.position.y, yaw_of(m.pose.pose.orientation))),
    qos_profile_sensor_data)


def spin(sec):
    end = time.time() + sec
    while time.time() < end:
        rclpy.spin_once(node, timeout_sec=0.02)


spin(8.0)
if pose[0] is None:
    print('FAIL: no /odom (start the simulation first)')
    sys.exit(2)

master, slave = pty.openpty()
proc = subprocess.Popen(['ros2', 'run', 'tb3_keyboard_teleop', 'keyboard_teleop'],
                        stdin=slave, stdout=slave, stderr=slave, close_fds=True,
                        start_new_session=True)  # own process group, like a terminal job
out = b''


def drain():
    global out
    while select.select([master], [], [], 0)[0]:
        out += os.read(master, 4096)


def hold(key, seconds):
    """Type `key` repeatedly (like terminal key-repeat) for `seconds`."""
    end = time.time() + seconds
    while time.time() < end:
        os.write(master, key.encode())
        spin(0.1)
        drain()


t_end = time.time() + 30
while b'speed: linear' not in out and time.time() < t_end:
    spin(0.2); drain()   # wait until the node printed its banner (ready)
spin(1.0)
results = []


def check(name, ok, detail):
    results.append(ok)
    print('%-28s %s  %s' % (name, 'PASS' if ok else 'FAIL', detail))


p0 = pose[0]
hold('w', 3.0)
spin(0.1)
p1 = pose[0]
check('hold w -> moves forward', (p1[0] - p0[0]) * math.cos(p0[2]) + (p1[1] - p0[1]) * math.sin(p0[2]) > 0.05,
      'dx=%.2f dy=%.2f' % (p1[0] - p0[0], p1[1] - p0[1]))

# deadman: no more keys -> robot must stop by itself
spin(3.0)
pa = pose[0]
spin(1.5)
pb = pose[0]
check('deadman auto-stop', math.hypot(pb[0] - pa[0], pb[1] - pa[1]) < 0.01, 'moved %.3f m while idle' %
      math.hypot(pb[0] - pa[0], pb[1] - pa[1]))

p0 = pose[0]
hold('a', 1.5)
spin(1.5)
p1 = pose[0]
check('hold a -> turns left', math.atan2(math.sin(p1[2] - p0[2]), math.cos(p1[2] - p0[2])) > 0.2,
      'dyaw=%.2f rad' % math.atan2(math.sin(p1[2] - p0[2]), math.cos(p1[2] - p0[2])))

p0 = pose[0]
hold('s', 3.0)
spin(2.0)
p1 = pose[0]
check('hold s -> moves backward', (p1[0] - p0[0]) * math.cos(p0[2]) + (p1[1] - p0[1]) * math.sin(p0[2]) < -0.03,
      'dx=%.2f dy=%.2f' % (p1[0] - p0[0], p1[1] - p0[1]))

# space stops a held command immediately
os.write(master, b'w'); spin(1.0)
os.write(master, b' '); spin(2.0)
pa = pose[0]; spin(1.5); pb = pose[0]
check('space stops', math.hypot(pb[0] - pa[0], pb[1] - pa[1]) < 0.01, 'moved %.3f m after stop' %
      math.hypot(pb[0] - pa[0], pb[1] - pa[1]))

os.write(master, b'u'); os.write(master, b'v'); spin(1.0); drain()
check('u/v keys print speed', b'speed: linear=0.14' in out, 'terminal output shows speed change')

import signal
hold('w', 1.5)
pw = pose[0]
os.killpg(proc.pid, signal.SIGINT)  # what CTRL-C does in a real terminal
end = time.time() + 8
while proc.poll() is None and time.time() < end:
    spin(0.1); drain()   # keep draining the pty so the node can flush and exit
if proc.poll() is None:
    os.killpg(proc.pid, signal.SIGKILL); proc.wait()
spin(2.0); pw = pose[0]; spin(1.5)
check('robot stopped after CTRL-C', math.hypot(pose[0][0] - pw[0], pose[0][1] - pw[1]) < 0.01,
      'moved %.3f m after exit' % math.hypot(pose[0][0] - pw[0], pose[0][1] - pw[1]))
check('SIGINT (CTRL-C) exits cleanly', proc.returncode in (0, -2, 130), 'exit code %s' % proc.returncode)
print('--- node terminal output (tail) ---'); print(out.decode(errors='ignore')[-700:])
print('RESULT: %d/%d passed' % (sum(results), len(results)))
node.destroy_node(); rclpy.shutdown()
sys.exit(0 if all(results) else 1)
