import unittest

from communication import protocol as p


class CommandEncodingTest(unittest.TestCase):
    def test_encodings(self):
        self.assertEqual(p.stop_all().encode(), b"M110\n")
        self.assertEqual(p.read_status().encode(), b"M111\n")
        self.assertEqual(p.set_mode(True).encode(), b"M112 S1\n")
        self.assertEqual(p.set_watchdog(500).encode(), b"M113 T500\n")
        self.assertEqual(p.set_watchdog(0).encode(), b"M113 T0\n")
        self.assertEqual(p.set_speeds(100, -200).encode(), b"M120 X100 Y-200\n")
        self.assertEqual(p.set_speeds(vy=0).encode(), b"M120 Y0\n")
        self.assertEqual(p.set_motion_limits(80000, 2097).encode(), b"M121 A80000 V2097\n")
        self.assertEqual(p.move_relative(-8, None).encode(), b"M122 X-8\n")
        self.assertEqual(p.move_absolute(0, 16000).encode(), b"M123 X0 Y16000\n")
        self.assertEqual(p.home(True, False, 1049).encode(), b"M130 X1 Y0 F1049\n")

    def test_ranges_are_checked(self):
        with self.assertRaises(ValueError):
            p.set_speeds(32769)
        with self.assertRaises(ValueError):
            p.set_watchdog(50)
        with self.assertRaises(ValueError):
            p.set_motion_limits(0, 100)
        with self.assertRaises(ValueError):
            p.move_relative(None, None)
        with self.assertRaises(ValueError):
            p.home(False, False)
        with self.assertRaises(TypeError):
            p.set_speeds(1.5)

    def test_motion_flag(self):
        self.assertTrue(p.set_speeds(1).is_motion)
        self.assertTrue(p.home().is_motion)
        self.assertFalse(p.stop_all().is_motion)
        self.assertFalse(p.set_motion_limits(1, 1).is_motion)

    def test_v1(self):
        self.assertEqual(p.encode_speed_v1("X", -200), b"X-200\n")
        self.assertEqual(p.decode_window_duration_v1(b"\x46\x00"), 70)
        self.assertEqual(p.decode_endstops_v1(b"\x05"), p.Endstops(True, False, True, False))
        self.assertTrue(p.decode_window_open_v1(b"\x01"))
        with self.assertRaises(p.ProtocolError):
            p.decode_endstops_v1(b"\x10")


class ReplyParsingTest(unittest.TestCase):
    def test_ok_and_err(self):
        r = p.parse_reply("ok M120 X100 Y-200\r\n")
        self.assertTrue(r.ok)
        self.assertEqual((r.code, r.values), (120, {"X": 100, "Y": -200}))
        e = p.parse_reply("err M123 3")
        self.assertFalse(e.ok)
        self.assertEqual(e.error, p.ErrorCode.NOT_HOMED)
        self.assertIn("origine", e.error_text)

    def test_malformed(self):
        for line in ("", "ok", "ok 120", "err M120", "err M120 99", "ok M120 X1.5", "bonjour M1"):
            with self.assertRaises(p.ProtocolError, msg=line):
                p.parse_reply(line)

    def test_status_roundtrip(self):
        line = "ok M111 t=123456 x=1200 y=3400 vx=0 vy=-800 es=5 win=1 mode=1 home=3 mv=2 al=4 va=28500"
        st = p.MachineStatus.from_reply(p.parse_reply(line))
        self.assertEqual((st.x, st.y, st.vy), (1200, 3400, -800))
        self.assertTrue(st.endstops.x_min and st.endstops.y_min and not st.endstops.x_max)
        self.assertTrue(st.homed and st.moving_y and not st.moving_x)
        self.assertEqual(st.alarms, p.Alarm.LIMIT_X)
        self.assertFalse(st.blocking_alarm)
        self.assertEqual(p.format_status(st), line)

    def test_status_missing_field(self):
        with self.assertRaises(p.ProtocolError):
            p.MachineStatus.from_reply(p.parse_reply("ok M111 t=1 x=0"))


if __name__ == "__main__":
    unittest.main()
