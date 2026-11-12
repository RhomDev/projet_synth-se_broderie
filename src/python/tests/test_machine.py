import json
import tempfile
import unittest
from pathlib import Path

from communication import protocol as p
from communication.link import LinkState
from machine.config import AppConfig, ZoneConfig, config_from_dict, default_config_path, load_config, save_config
from machine.safety import can_move, check_relative, check_target, speed_cap
from machine.state import MachineState, derive_state
from machine.units import AxisUnits


def make_status(**kw) -> p.MachineStatus:
    base = dict(t_ms=1, x=0, y=0, vx=0, vy=0, endstops=p.Endstops(), window_open=False, manual_mode=True,
                homed_x=True, homed_y=True, moving_x=False, moving_y=False, alarms=p.Alarm.NONE, window_us=0)
    base.update(kw)
    return p.MachineStatus(**base)


class UnitsTest(unittest.TestCase):
    def test_conversions(self):
        u = AxisUnits(80.0)
        self.assertEqual(u.mm_to_steps(0.1), 8)
        self.assertAlmostEqual(u.steps_to_mm(16000), 200.0)
        self.assertEqual(u.speed_to_fw(1.0), 105)  # 80 µpas/s × 32768/25000
        self.assertEqual(u.speed_to_fw(-20.0), -2097)
        self.assertEqual(u.speed_to_fw(10_000), 32768)  # borné
        self.assertAlmostEqual(u.max_speed_mm_s, 312.5)
        self.assertEqual(u.accel_to_fw(1000.0), 80_000)
        self.assertEqual(u.speed_magnitude_to_fw(0.0), 1)


class StateTest(unittest.TestCase):
    def test_derivation(self):
        st = make_status()
        self.assertIs(derive_state(LinkState.DISCONNECTED, st, True, False), MachineState.DISCONNECTED)
        self.assertIs(derive_state(LinkState.LOST, st, True, False), MachineState.LOST)
        self.assertIs(derive_state(LinkState.CONNECTED, st, False, False), MachineState.STALE)
        self.assertIs(derive_state(LinkState.CONNECTED, st, True, False), MachineState.READY)
        self.assertIs(derive_state(LinkState.CONNECTED, make_status(homed_y=False), True, False),
                      MachineState.UNREFERENCED)
        self.assertIs(derive_state(LinkState.CONNECTED, make_status(moving_x=True), True, True),
                      MachineState.HOMING)
        self.assertIs(derive_state(LinkState.CONNECTED, make_status(alarms=p.Alarm.WATCHDOG), True, False),
                      MachineState.ALARM)
        self.assertIs(derive_state(LinkState.CONNECTED, make_status(alarms=p.Alarm.LIMIT_X), True, False),
                      MachineState.READY)


class SafetyTest(unittest.TestCase):
    def setUp(self):
        self.cfg = AppConfig()
        self.cfg.x.travel_mm = 300.0
        self.cfg.y.travel_mm = 200.0

    def test_can_move(self):
        self.assertTrue(can_move(MachineState.READY, make_status()))
        self.assertTrue(can_move(MachineState.UNREFERENCED, make_status(homed_x=False)))
        for state in (MachineState.STALE, MachineState.LOST, MachineState.ALARM, MachineState.DISCONNECTED):
            self.assertFalse(can_move(state, make_status()))
        self.assertFalse(can_move(MachineState.READY, make_status(manual_mode=False)))

    def test_target(self):
        st = make_status()
        self.assertTrue(check_target(self.cfg, st, 150, 100))
        self.assertFalse(check_target(self.cfg, st, 299.5, 100))  # marge de 1 mm
        self.assertFalse(check_target(self.cfg, st, 0.5, 100))
        self.assertFalse(check_target(self.cfg, make_status(homed_x=False), 150, 100))
        self.cfg.y.travel_mm = None
        self.assertIn("course Y inconnue", check_target(self.cfg, st, 150, 100).reason)

    def test_forbidden_zone(self):
        self.cfg.view.forbidden_zones = [ZoneConfig("pied", 100, 50, 20, 20)]
        d = check_target(self.cfg, make_status(), 110, 60)
        self.assertFalse(d)
        self.assertIn("pied", d.reason)

    def test_relative(self):
        st = make_status(x=80 * 299)  # 299 mm
        self.assertFalse(check_relative(self.cfg, st, "X", 1.0))
        self.assertTrue(check_relative(self.cfg, st, "X", -10.0))
        self.assertTrue(check_relative(self.cfg, make_status(homed_x=False), "X", 1000.0))

    def test_speed_cap(self):
        self.assertEqual(speed_cap(self.cfg, homed=False), 10.0)
        self.assertEqual(speed_cap(self.cfg, homed=True), 250.0)


class ConfigTest(unittest.TestCase):
    def test_default_file_is_valid(self):
        data = json.loads(default_config_path().read_text(encoding="utf-8"))
        cfg = config_from_dict(data)
        self.assertEqual(cfg.validate(), [])
        self.assertEqual(cfg.x.steps_per_mm, 80.0)
        self.assertIsNone(cfg.x.travel_mm)

    def test_roundtrip(self):
        cfg = AppConfig()
        cfg.x.travel_mm = 287.5
        cfg.view.forbidden_zones = [ZoneConfig("pied", 1, 2, 3, 4)]
        cfg.safety.watchdog_enabled = False
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "machine.json"
            save_config(cfg, path)
            loaded = load_config(path)
        self.assertEqual(loaded.x.travel_mm, 287.5)
        self.assertEqual(loaded.view.forbidden_zones[0].name, "pied")
        self.assertFalse(loaded.safety.watchdog_enabled)

    def test_invalid_config_refused(self):
        cfg = AppConfig()
        cfg.x.steps_per_mm = 0
        with self.assertRaises(ValueError):
            save_config(cfg, Path(tempfile.gettempdir()) / "inutilise.json")


if __name__ == "__main__":
    unittest.main()
