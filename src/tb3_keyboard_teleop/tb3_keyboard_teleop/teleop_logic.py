"""Pure-Python teleoperation logic (no ROS imports, so it is unit-testable anywhere).

The ROS node feeds key presses in with `press()` and calls `update()` at a
fixed rate; `update()` returns the velocity command to publish.
"""

# key -> (linear direction, angular direction)
MOVE_KEYS = {
    'w': (1, 0),    # forward
    's': (-1, 0),   # backward
    'a': (0, 1),    # rotate left (counter-clockwise)
    'd': (0, -1),   # rotate right (clockwise)
    'q': (1, 1),    # forward + left
    'e': (1, -1),   # forward + right
    'z': (-1, -1),  # backward + left (mirrors forward arc when reversing)
    'c': (-1, 1),   # backward + right
}
STOP_KEYS = (' ', 'x')


def clamp(value, low, high):
    return max(low, min(high, value))


def ramp(current, target, max_delta):
    """Move `current` toward `target` by at most `max_delta`."""
    diff = target - current
    if abs(diff) <= max_delta:
        return target
    return current + (max_delta if diff > 0 else -max_delta)


class TeleopState:
    def __init__(self, max_linear=0.22, max_angular=2.84,
                 linear_step=0.02, angular_step=0.2,
                 start_linear=0.12, start_angular=1.0,
                 linear_accel=0.5, angular_accel=3.0,
                 deadman_timeout=0.6):
        self.max_linear = max_linear
        self.max_angular = max_angular
        self.linear_step = linear_step
        self.angular_step = angular_step
        self.linear_speed = clamp(start_linear, 0.0, max_linear)
        self.angular_speed = clamp(start_angular, 0.0, max_angular)
        self.linear_accel = linear_accel
        self.angular_accel = angular_accel
        self.deadman_timeout = deadman_timeout
        self.target_linear = 0.0
        self.target_angular = 0.0
        self.linear = 0.0
        self.angular = 0.0
        self.last_move_time = None
        self.deadman_enabled = deadman_timeout > 0
        self._saved_timeout = deadman_timeout if deadman_timeout > 0 else 0.6

    def press(self, key, now):
        """Handle one key press. Returns a short message for the UI, or ''."""
        if key in MOVE_KEYS:
            lin_dir, ang_dir = MOVE_KEYS[key]
            self.target_linear = lin_dir * self.linear_speed
            self.target_angular = ang_dir * self.angular_speed
            self.last_move_time = now
            return ''
        if key in STOP_KEYS:
            self.target_linear = 0.0
            self.target_angular = 0.0
            return 'STOP'
        if key == 'u':
            self.linear_speed = clamp(self.linear_speed + self.linear_step, 0.0, self.max_linear)
        elif key == 'j':
            self.linear_speed = clamp(self.linear_speed - self.linear_step, 0.0, self.max_linear)
        elif key == 'i':
            self.angular_speed = clamp(self.angular_speed + self.angular_step, 0.0, self.max_angular)
        elif key == 'k':
            self.angular_speed = clamp(self.angular_speed - self.angular_step, 0.0, self.max_angular)
        elif key == 'p':
            self.deadman_enabled = not self.deadman_enabled
            return 'deadman ' + ('ON' if self.deadman_enabled else 'OFF')
        elif key == 'v':
            return ('velocity: linear=%.2f m/s angular=%.2f rad/s' % (self.linear, self.angular))
        else:
            return ''
        # a speed change also rescales a command that is currently held
        if self.target_linear:
            self.target_linear = (1 if self.target_linear > 0 else -1) * self.linear_speed
        if self.target_angular:
            self.target_angular = (1 if self.target_angular > 0 else -1) * self.angular_speed
        return 'speed: linear=%.2f m/s angular=%.2f rad/s' % (self.linear_speed, self.angular_speed)

    def update(self, now, dt):
        """Advance smoothing/deadman by dt seconds; return (linear, angular)."""
        if (self.deadman_enabled and self.last_move_time is not None
                and now - self.last_move_time > self._saved_timeout):
            self.target_linear = 0.0
            self.target_angular = 0.0
        self.linear = ramp(self.linear, self.target_linear, self.linear_accel * dt)
        self.angular = ramp(self.angular, self.target_angular, self.angular_accel * dt)
        return self.linear, self.angular
