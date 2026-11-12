"""Étape 4 : détection du firmware, simulateur v1, machine à coudre simulée, ligne de test."""
import unittest

from PySide6.QtCore import QCoreApplication

from communication import protocol as p
from communication.link import MachineLink
from communication.simulator import SimulatedMachine
from machine.config import AppConfig
from machine.line_test import LineTest, plan_line
from machine.state import MachineModel
from communication.link import LinkState
from tests.test_simulator import FakeClock, send, status

_app = QCoreApplication.instance() or QCoreApplication([])


class LegacySpeedsTest(unittest.TestCase):
    def test_encoding(self):
        self.assertEqual(p.LegacySpeeds(100, -200).encode(), b"X100 Y-200\n")
        self.assertEqual(p.LegacySpeeds(vy=0).encode(), b"Y0\n")
        self.assertFalse(p.LegacySpeeds(0, 0).expects_reply)
        self.assertTrue(p.LegacySpeeds(0, 0).is_motion)
        with self.assertRaises(ValueError):
            p.LegacySpeeds()
        with self.assertRaises(ValueError):
            p.LegacySpeeds(40000)


class FirmwareDetectionTest(unittest.TestCase):
    def detect(self, version: int) -> int:
        sim = SimulatedMachine(firmware_version=version)
        link = MachineLink(sim, reply_timeout=0.05)
        sim.open()
        return link.detect_protocol()

    def test_v2(self):
        self.assertEqual(self.detect(2), 2)

    def test_v1(self):
        self.assertEqual(self.detect(1), 1)

    def test_nothing(self):
        sim = SimulatedMachine()
        link = MachineLink(sim, reply_timeout=0.02)
        sim.open()
        sim.link_cut = True
        self.assertEqual(link.detect_protocol(), 0)


class SimulatorV1Test(unittest.TestCase):
    def test_v1_ignores_v2_commands(self):
        clock = FakeClock()
        sim = SimulatedMachine(clock=clock, firmware_version=1)
        sim.open()
        sim.write(b"M111\n")
        self.assertEqual(sim.read(0), b"")
        sim.write(b"G1 X50\n")
        self.assertEqual(sim.read(0), b"")
        sim.write(b"M101\n")
        self.assertEqual(sim.read(0), b"\x00")


class SewingWindowsTest(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.sim = SimulatedMachine(clock=self.clock)
        self.sim.open()

    def test_window_duration_at_600_rpm(self):
        self.sim.set_sewing_rpm(600)  # 100 ms par tour, fenêtre = 1/3 du tour
        self.clock.run(self.sim, 0.5, poll=0.01)
        self.assertAlmostEqual(status(self.sim).window_us, 33_333, delta=1500)

    def test_legacy_line_makes_one_stitch_per_window(self):
        self.sim.set_sewing_rpm(600)
        send(self.sim, "X2621")  # 2621 unités = 2000 µpas/s = 25 mm/s à 80 µpas/mm
        self.clock.run(self.sim, 1.0, poll=0.01)  # 10 tours
        x_mm = status(self.sim).x / 80
        self.assertAlmostEqual(x_mm, 10 * 25 * 0.0333, delta=1.0)  # ≈ 0,83 mm par point

    def test_embroidery_mode_halts_v2_motion(self):
        send(self.sim, "M112 S1")
        send(self.sim, "M120 X2000")
        self.clock.run(self.sim, 0.2, poll=0.05)
        self.assertEqual(send(self.sim, "M112 S0"), "ok M112 S0")
        self.clock.run(self.sim, 0.1, poll=0.05)
        self.assertFalse(status(self.sim).moving)


class FakeMotion:
    def __init__(self, config):
        self.config = config
        self.sent = []
        self.calibrating = False
        self.jogging = False

    def send(self, command, urgent=False):
        self.sent.append(str(command))
        return len(self.sent)


def make_status(x=0, y=0, moving=False, manual=True, va=30_000, es=p.Endstops()):
    return p.MachineStatus(t_ms=1, x=x, y=y, vx=0, vy=0, endstops=es, window_open=False, manual_mode=manual,
                           homed_x=True, homed_y=True, moving_x=moving, moving_y=False, alarms=p.Alarm.NONE,
                           window_us=va)


class LineTestTest(unittest.TestCase):
    def setUp(self):
        self.cfg = AppConfig()
        self.cfg.x.travel_mm, self.cfg.y.travel_mm = 300.0, 200.0
        self.model = MachineModel()
        self.model.set_link_state(LinkState.CONNECTED, protocol=2)
        self.model.update_status(make_status(x=80 * 50, y=80 * 50))
        self.motion = FakeMotion(self.cfg)
        self.line = LineTest(self.motion, self.model)
        self.results = []
        self.line.finished.connect(lambda level, text: self.results.append((level, text)))

    def test_plan(self):
        plan, d = plan_line(self.cfg, self.model.status, 50, 0, 1.0, 0.04)
        self.assertTrue(d)
        self.assertAlmostEqual(plan.speed_mm_s, 25.0)
        self.assertEqual(plan.stitches, 50)
        self.assertEqual((plan.vx_fw, plan.vy_fw), (2621, 0))
        self.assertAlmostEqual(plan.x1, 100.0)

    def test_plan_refusals(self):
        _, d = plan_line(self.cfg, self.model.status, 50, 0, 3.0, 0.03)  # 100 mm/s > 30
        self.assertIn("sans rampe", d.reason)
        _, d = plan_line(self.cfg, self.model.status, 300, 0, 1.0, 0.04)  # sort du plateau
        self.assertIn("hors limites", d.reason)
        _, d = plan_line(self.cfg, self.model.status, 50, 0, 1.0, 0.0)
        self.assertIn("fenêtre", d.reason)

    def test_run_to_the_end(self):
        plan, _ = plan_line(self.cfg, self.model.status, 50, 0, 1.0, 0.04)
        self.assertTrue(self.line.start(plan))
        self.assertEqual(self.motion.sent, ["M112 S0", "X2621 Y0"])
        self.line.on_status(make_status(x=80 * 75, y=80 * 50, moving=True, manual=False))
        self.assertEqual(len(self.motion.sent), 2)  # à mi-chemin : rien
        self.line.on_status(make_status(x=80 * 99.6, y=80 * 50, moving=True, manual=False))
        self.assertEqual(self.motion.sent[2:], ["X0 Y0", "M112 S1"])
        self.line.on_status(make_status(x=80 * 100, y=80 * 50, moving=False))
        self.assertFalse(self.line.running)
        self.assertEqual(self.results[-1][0], "info")
        self.assertIn("50.00 mm réalisés", self.results[-1][1])

    def test_endstop_aborts(self):
        plan, _ = plan_line(self.cfg, self.model.status, 50, 0, 1.0, 0.04)
        self.line.start(plan)
        self.line.on_status(make_status(x=80 * 60, y=80 * 50, moving=True, manual=False,
                                        es=p.Endstops(x_max=True)))
        self.assertFalse(self.line.running)
        self.assertEqual(self.results[-1][0], "error")
        self.assertEqual(self.motion.sent[-2:], ["X0 Y0", "M112 S1"])


if __name__ == "__main__":
    unittest.main()
