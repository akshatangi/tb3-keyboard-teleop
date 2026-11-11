#!/usr/bin/env python3
"""ROS 2 keyboard teleoperation node for a simulated TurtleBot3.

Reads single key presses from the terminal and publishes geometry_msgs/Twist
on /cmd_vel (TurtleBot3 on ROS 2 Humble uses plain Twist).
Run it in its own terminal: it needs a real keyboard (TTY).
"""
import os
import select
import sys
import termios
import tty

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions

from tb3_keyboard_teleop.teleop_logic import TeleopState

HELP = """
---------------------------------------------
 TurtleBot3 keyboard teleoperation
---------------------------------------------
   q  w  e        w/s : forward / backward
   a     d        a/d : rotate left / right
   z  s  c        q/e/z/c : move while turning

 SPACE or x : stop
 u/j : linear speed  +/-      i/k : angular speed  +/-
 p : toggle deadman (auto-stop when no key arrives)
 v : print current velocity
 CTRL-C : quit
---------------------------------------------
"""


class KeyboardTeleop(Node):
    def __init__(self):
        super().__init__('keyboard_teleop')
        self.declare_parameter('cmd_vel_topic', '/cmd_vel')
        self.declare_parameter('max_linear', 0.22)
        self.declare_parameter('max_angular', 2.84)
        self.declare_parameter('linear_step', 0.02)
        self.declare_parameter('angular_step', 0.2)
        self.declare_parameter('start_linear', 0.12)
        self.declare_parameter('start_angular', 1.0)
        self.declare_parameter('linear_accel', 0.5)
        self.declare_parameter('angular_accel', 3.0)
        self.declare_parameter('deadman_timeout', 0.6)
        self.declare_parameter('publish_rate', 20.0)
        p = lambda n: self.get_parameter(n).value

        self.state = TeleopState(
            max_linear=p('max_linear'), max_angular=p('max_angular'),
            linear_step=p('linear_step'), angular_step=p('angular_step'),
            start_linear=p('start_linear'), start_angular=p('start_angular'),
            linear_accel=p('linear_accel'), angular_accel=p('angular_accel'),
            deadman_timeout=p('deadman_timeout'))
        self.rate = p('publish_rate')
        self.pub = self.create_publisher(Twist, p('cmd_vel_topic'), 10)
        self.fd = sys.stdin.fileno()
        self.old_settings = termios.tcgetattr(self.fd)
        tty.setcbreak(self.fd)  # cbreak keeps CTRL-C and output formatting working
        self.timer = self.create_timer(1.0 / self.rate, self.tick)
        print(HELP)
        print('speed: linear=%.2f m/s angular=%.2f rad/s' %
              (self.state.linear_speed, self.state.angular_speed))

    def now(self):
        return self.get_clock().now().nanoseconds / 1e9

    def read_keys(self):
        keys = []
        while select.select([sys.stdin], [], [], 0)[0]:
            data = os.read(self.fd, 64).decode(errors='ignore')
            if not data:
                break
            keys.extend(data)
        return keys

    def tick(self):
        for key in self.read_keys():
            if key == '\x03':
                raise KeyboardInterrupt
            msg = self.state.press(key.lower() if key.isalpha() else key, self.now())
            if msg:
                print(msg)
        lin, ang = self.state.update(self.now(), 1.0 / self.rate)
        twist = Twist()
        twist.linear.x = float(lin)
        twist.angular.z = float(ang)
        self.pub.publish(twist)

    def shutdown(self):
        for _ in range(3):  # always leave the robot stopped (repeat in case of loss)
            self.pub.publish(Twist())
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)


def main(args=None):
    # Handle CTRL-C ourselves so the context is still valid when we publish the final stop
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    node = KeyboardTeleop()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.shutdown()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
