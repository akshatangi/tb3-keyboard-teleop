import pytest
from tb3_keyboard_teleop.teleop_logic import TeleopState, ramp


def run(s, t0, seconds, dt=0.05):
    t = t0
    out = (s.linear, s.angular)
    for _ in range(int(seconds / dt)):
        t += dt
        out = s.update(t, dt)
    return t, out


def test_ramp_limits_step():
    assert ramp(0.0, 1.0, 0.1) == pytest.approx(0.1)
    assert ramp(0.95, 1.0, 0.1) == 1.0
    assert ramp(0.0, -1.0, 0.1) == pytest.approx(-0.1)


def test_forward_backward_signs():
    s = TeleopState(deadman_timeout=0)
    s.press('w', 0.0)
    _, (lin, ang) = run(s, 0.0, 1.0)
    assert lin == pytest.approx(0.12) and ang == 0
    s.press('s', 1.0)
    _, (lin, _) = run(s, 1.0, 2.0)
    assert lin == pytest.approx(-0.12)


def test_turn_signs():
    s = TeleopState(deadman_timeout=0)
    s.press('a', 0.0)
    _, (lin, ang) = run(s, 0.0, 1.0)
    assert lin == 0 and ang == pytest.approx(1.0)
    s.press('d', 1.0)
    _, (_, ang) = run(s, 1.0, 1.0)
    assert ang == pytest.approx(-1.0)


def test_arc_keys():
    s = TeleopState(deadman_timeout=0)
    s.press('q', 0.0)
    assert s.target_linear > 0 and s.target_angular > 0
    s.press('e', 0.0)
    assert s.target_linear > 0 and s.target_angular < 0
    s.press('z', 0.0)
    assert s.target_linear < 0 and s.target_angular < 0
    s.press('c', 0.0)
    assert s.target_linear < 0 and s.target_angular > 0


def test_smoothing_is_gradual():
    s = TeleopState(deadman_timeout=0, linear_accel=0.5)
    s.press('w', 0.0)
    lin, _ = s.update(0.05, 0.05)
    assert 0 < lin < 0.12


def test_stop_keys():
    for key in (' ', 'x'):
        s = TeleopState(deadman_timeout=0)
        s.press('w', 0.0)
        run(s, 0.0, 1.0)
        assert s.press(key, 1.0) == 'STOP'
        _, (lin, ang) = run(s, 1.0, 1.0)
        assert lin == 0 and ang == 0


def test_speed_keys_and_limits():
    s = TeleopState(deadman_timeout=0)
    for _ in range(20):
        s.press('u', 0.0)
    assert s.linear_speed == pytest.approx(0.22)
    for _ in range(20):
        s.press('j', 0.0)
    assert s.linear_speed == 0.0
    for _ in range(30):
        s.press('i', 0.0)
    assert s.angular_speed == pytest.approx(2.84)
    for _ in range(30):
        s.press('k', 0.0)
    assert s.angular_speed == 0.0


def test_speed_change_applies_to_held_command():
    s = TeleopState(deadman_timeout=0)
    s.press('w', 0.0)
    s.press('u', 0.0)
    assert s.target_linear == pytest.approx(0.14)


def test_deadman_stops_without_keys():
    s = TeleopState(deadman_timeout=0.6)
    s.press('w', 0.0)
    t, (lin, _) = run(s, 0.0, 0.5)
    assert lin > 0
    _, (lin, _) = run(s, t, 2.0)
    assert lin == 0


def test_deadman_toggle_keeps_moving():
    s = TeleopState(deadman_timeout=0.6)
    s.press('w', 0.0)
    assert s.press('p', 0.0) == 'deadman OFF'
    _, (lin, _) = run(s, 0.0, 3.0)
    assert lin == pytest.approx(0.12)


def test_unknown_key_ignored():
    s = TeleopState()
    assert s.press('?', 0.0) == ''
    assert s.target_linear == 0
