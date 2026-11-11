#!/usr/bin/env python3
"""Automated movement test (no keyboard needed).

Drives the SAME TeleopState logic as the keyboard node with a scripted key
sequence, publishes /cmd_vel, and checks from /odom that the robot really
moved as expected (forward, backward, left turn, right turn, stop).
Prints a PASS/FAIL table and exits non-zero on failure.
"""
import math
import sys

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data

from tb3_keyboard_teleop.teleop_logic import TeleopState

# (name, key, seconds, check(dx, dy, dyaw, dist) -> bool, expectation text)
STEPS = [
    ('forward (w)', 'w', 3.0, lambda fwd, dyaw, d: fwd > 0.2 and abs(dyaw) < 0.2, 'moves forward > 0.2 m, no rotation'),
    ('backward (s)', 's', 3.0, lambda fwd, dyaw, d: fwd < -0.2 and abs(dyaw) < 0.2, 'moves backward > 0.2 m'),
    ('rotate left (a)', 'a', 1.5, lambda fwd, dyaw, d: dyaw > 0.8 and d < 0.1, 'yaw increases > 0.8 rad'),
    ('rotate right (d)', 'd', 1.5, lambda fwd, dyaw, d: dyaw < -0.8 and d < 0.1, 'yaw decreases > 0.8 rad'),
    ('forward-left arc (q)', 'q', 1.5, lambda fwd, dyaw, d: d > 0.08 and 0.5 < dyaw < 2.5, 'moves and turns left'),
    ('forward-right arc (e)', 'e', 1.5, lambda fwd, dyaw, d: d > 0.08 and -2.5 < dyaw < -0.5, 'moves and turns right'),
    ('stop (space)', ' ', 1.5, lambda fwd, dyaw, d: d < 0.1 and abs(dyaw) < 0.2, 'robot stays (after ramp-down)'),
]


def yaw_of(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


class ScriptedTest(Node):
    def __init__(self):
        # pace everything on Gazebo's clock so results do not depend on how fast the sim runs
        super().__init__('scripted_test', parameter_overrides=[Parameter('use_sim_time', value=True)])
        self.declare_parameter('rate', 20.0)
        self.rate = self.get_parameter('rate').value
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.create_subscription(Odometry, '/odom', self.on_odom, qos_profile_sensor_data)
        self.pose = None

    def on_odom(self, msg):
        p = msg.pose.pose
        self.pose = (p.position.x, p.position.y, yaw_of(p.orientation))

    def spin_for(self, seconds):
        end = self.get_clock().now().nanoseconds / 1e9 + seconds
        while rclpy.ok() and self.get_clock().now().nanoseconds / 1e9 < end:
            rclpy.spin_once(self, timeout_sec=0.01)

    def sim_now(self):
        return self.get_clock().now().nanoseconds / 1e9

    def drive(self, state, seconds):
        """Publish the state's command at `rate` Hz for `seconds` of SIMULATED time."""
        dt = 1.0 / self.rate
        t0 = last = self.sim_now()
        while rclpy.ok() and self.sim_now() - t0 < seconds:
            now = self.sim_now()
            lin, ang = state.update(now, max(now - last, 1e-3))
            last = now
            tw = Twist()
            tw.linear.x, tw.angular.z = lin, ang
            self.pub.publish(tw)
            self.spin_for(dt)

    def run(self):
        print('Waiting for /odom ...')
        for _ in range(300):
            rclpy.spin_once(self, timeout_sec=0.1)
            if self.pose:
                break
        if not self.pose:
            print('FAIL: no /odom received (is the simulation running?)')
            return False
        state = TeleopState(deadman_timeout=0)
        results = []
        for name, key, secs, check, expect in STEPS:
            # settle: stop and wait, so the previous step cannot leak into this one
            state.press(' ', 0.0)
            self.drive(state, 2.0)
            self.spin_for(0.3)
            start = self.pose
            state.press(key, 0.0)
            self.drive(state, secs)
            self.spin_for(0.1)
            end = self.pose
            dx, dy = end[0] - start[0], end[1] - start[1]
            dyaw = math.atan2(math.sin(end[2] - start[2]), math.cos(end[2] - start[2]))
            dist = math.hypot(dx, dy)
            fwd = dx * math.cos(start[2]) + dy * math.sin(start[2])
            ok = bool(check(fwd, dyaw, dist))
            results.append(ok)
            print('%-24s %-4s dist=%.2f m  dyaw=%+.2f rad   (%s)' %
                  (name, 'PASS' if ok else 'FAIL', dist, dyaw, expect))
        self.pub.publish(Twist())
        print('RESULT: %d/%d passed' % (sum(results), len(results)))
        return all(results)


def main(args=None):
    rclpy.init(args=args)
    node = ScriptedTest()
    ok = node.run()
    node.destroy_node()
    rclpy.shutdown()
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
