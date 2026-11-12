import unittest

from communication import protocol as p
from communication.simulator import SimulatedMachine


class FakeClock:
    def __init__(self) -> None:
        self.t = 1000.0

    def __call__(self) -> float:
        return self.t

    def run(self, sim: SimulatedMachine, seconds: float, poll: float | None = None) -> None:
        """Avance le temps ; ``poll`` envoie M111 à cette période (comme l'application)."""
        step = poll or seconds
        while seconds > 1e-9:
            dt = min(step, seconds)
            self.t += dt
            seconds -= dt
            if poll:
                send(sim, "M111")


def send(sim: SimulatedMachine, text: str) -> str:
    sim.write((text + "\n").encode())
    return sim.read(0).decode("ascii", errors="replace").strip()


def status(sim: SimulatedMachine) -> p.MachineStatus:
    return p.MachineStatus.from_reply(p.parse_reply(send(sim, "M111")))


class SimulatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = FakeClock()
        self.sim = SimulatedMachine(travel_mm=(300, 200), start_mm=(120, 80), clock=self.clock)
        self.sim.open()

    def manual(self) -> None:
        self.assertEqual(send(self.sim, "M112 S1"), "ok M112 S1")

    def home(self) -> None:
        self.manual()
        self.assertEqual(send(self.sim, "M130 X1 Y1 F2097"), "ok M130 X1 Y1 F2097")
        self.clock.run(self.sim, 15.0, poll=0.05)

    def test_boot_state(self):
        st = status(self.sim)
        self.assertEqual((st.x, st.y, st.window_us), (0, 0, 0))
        self.assertFalse(st.manual_mode or st.homed_x or st.moving)

    def test_v1_binary_replies(self):
        self.sim.write(b"M100\n")
        self.assertEqual(self.sim.read(0), b"\x46\x00")
        self.sim.write(b"M101\n")
        self.assertEqual(self.sim.read(0), b"\x00")
        self.sim.write(b"M102\n")
        self.assertEqual(self.sim.read(0), b"\x00")

    def test_errors(self):
        self.assertEqual(send(self.sim, "M999"), "err M999 1")
        self.assertEqual(send(self.sim, "G1 X50"), "err M0 7")
        self.assertEqual(send(self.sim, "M120 X100"), "err M120 5")
        self.manual()
        self.assertEqual(send(self.sim, "M120 X40000"), "err M120 2")
        self.assertEqual(send(self.sim, "M120 Z1"), "err M120 2")
        self.assertEqual(send(self.sim, "M123 X10"), "err M123 3")
        self.assertEqual(send(self.sim, "M" + "1" * 70), "err M0 7")
        self.assertEqual(status(self.sim).x, 0)  # « G1 X50 » n'a rien déplacé

    def test_speed_with_ramp(self):
        self.manual()
        self.assertEqual(send(self.sim, "M120 X2097"), "ok M120 X2097 Y0")
        self.clock.run(self.sim, 1.0, poll=0.05)
        # 2097 unités = 1600 µpas/s ; la rampe (80 000 µpas/s²) coûte 16 µpas
        self.assertAlmostEqual(status(self.sim).x, 1584, delta=3)
        send(self.sim, "M120 X0")
        self.clock.run(self.sim, 0.1, poll=0.05)
        self.assertFalse(status(self.sim).moving)

    def test_homing_then_absolute_and_relative_moves(self):
        self.home()
        st = status(self.sim)
        self.assertTrue(st.homed_x and st.homed_y)
        self.assertEqual((st.x, st.y), (0, 0))
        self.assertFalse(st.endstops.x_min or st.endstops.y_min)
        send(self.sim, "M121 A400000 V20000")
        self.assertEqual(send(self.sim, "M123 X8000 Y-0"), "ok M123 X8000 Y0")
        self.clock.run(self.sim, 2.0, poll=0.05)
        self.assertEqual(status(self.sim).x, 8000)
        self.assertEqual(send(self.sim, "M122 X-8"), "ok M122 X-8")
        self.clock.run(self.sim, 0.2, poll=0.05)
        st = status(self.sim)
        self.assertEqual(st.x, 7992)
        self.assertFalse(st.moving)

    def test_endstop_stops_motion_and_raises_info_alarm(self):
        self.manual()
        send(self.sim, "M121 V30000")
        send(self.sim, "M120 X-30000")
        self.clock.run(self.sim, 10.0, poll=0.05)
        st = status(self.sim)
        self.assertTrue(st.endstops.x_min)
        self.assertFalse(st.moving_x)
        self.assertTrue(st.alarms & p.Alarm.LIMIT_X)
        self.assertFalse(st.blocking_alarm)
        self.assertEqual(send(self.sim, "M120 X-100"), "ok M120 X-100 Y0")  # non bloquant
        self.clock.run(self.sim, 0.5, poll=0.05)
        self.assertTrue(status(self.sim).endstops.x_min)

    def test_watchdog(self):
        self.manual()
        send(self.sim, "M113 T500")
        send(self.sim, "M120 X1000")
        self.clock.run(self.sim, 0.4, poll=0.1)  # interrogé : pas de déclenchement
        self.assertFalse(status(self.sim).alarms)
        self.clock.run(self.sim, 0.6)  # silence > 500 ms
        st = status(self.sim)
        self.assertTrue(st.alarms & p.Alarm.WATCHDOG)
        self.assertFalse(st.moving)
        self.assertEqual(send(self.sim, "M120 X1000"), "err M120 6")
        self.assertEqual(send(self.sim, "M114"), "ok M114")
        self.assertFalse(status(self.sim).alarms)

    def test_watchdog_quiet_when_idle(self):
        send(self.sim, "M113 T500")
        self.clock.run(self.sim, 2.0)
        self.assertFalse(status(self.sim).alarms)

    def test_stop_is_immediate(self):
        self.manual()
        send(self.sim, "M120 X2000 Y2000")
        self.clock.run(self.sim, 0.5, poll=0.05)
        self.assertEqual(send(self.sim, "M110"), "ok M110")
        x = status(self.sim).x
        self.clock.run(self.sim, 0.5, poll=0.05)
        st = status(self.sim)
        self.assertEqual(st.x, x)
        self.assertFalse(st.moving)

    def test_legacy_speed_gated_by_window_in_embroidery_mode(self):
        send(self.sim, "X2097")  # v1 : pas de réponse
        self.assertEqual(self.sim.read(0), b"")
        self.clock.run(self.sim, 0.5, poll=0.05)
        self.assertEqual(status(self.sim).x, 0)  # fenêtre fermée
        self.sim.set_window_open(True)
        self.clock.run(self.sim, 0.5, poll=0.05)
        self.sim.set_window_open(False)
        st = status(self.sim)
        self.assertAlmostEqual(st.x, 800, delta=2)
        self.assertAlmostEqual(st.window_us, 500_000, delta=1000)

    def test_reopen_reboots(self):
        self.home()
        self.sim.open()
        st = status(self.sim)
        self.assertFalse(st.homed_x or st.manual_mode)
        self.assertEqual(st.x, 0)

    def test_link_cut(self):
        self.sim.link_cut = True
        self.sim.write(b"M111\n")
        self.assertEqual(self.sim.read(0), b"")


if __name__ == "__main__":
    unittest.main()
