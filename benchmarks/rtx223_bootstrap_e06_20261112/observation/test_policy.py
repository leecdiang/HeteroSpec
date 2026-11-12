"""CPU-only fault injection against the actual observer policy and ETW receipt checks."""
import ctypes
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "runner"))
from observation import GIB, Observer, REQUIRED_AT_LOAD, TraceRecord, validate_watermarks


class Watermarks(unittest.TestCase):
    def test_failed_or_crossed_watermarks(self):
        for free, used, disk, occupants, first in (
                (7*GIB, 0, 2*GIB, [], True), (7*GIB-1, 0, GIB, [], False),
                (8*GIB, GIB, GIB, [], False), (8*GIB, 0, GIB-1, [], False),
                (8*GIB, 0, 2*GIB, [254], False)):
            with self.subTest(free=free, used=used, disk=disk, occupants=occupants, first=first):
                with self.assertRaises(RuntimeError):
                    validate_watermarks((12*GIB, free, used, disk, occupants), 0, 123, first)

    def test_permitted_edges(self):
        validate_watermarks((12*GIB, 8*GIB, GIB, 2*GIB, []), GIB, 0, True)
        validate_watermarks((12*GIB, 7*GIB, 2*GIB-1, GIB, [123]), GIB, 123, False)


class TraceFaults(unittest.TestCase):
    def fixture(self, events, losses=0, stop_status=0):
        o = object.__new__(Observer)
        o._watermarks = lambda: None
        o.emit = lambda row: None
        o.pid = 123
        o.creation = 456
        o.counts = {1: 0, 2: 0, 5: 0, 6: 0}
        o.loaded = set()
        o.session = True
        names = REQUIRED_AT_LOAD | {"native-probe.exe", "nvcuda.dll"}
        o._image = lambda s: {"path": s, "sha256": "a"*64} if s in names else self.fail_image()
        rows = iter(events)

        def stop(lost):
            lost[2] = losses
            return stop_status

        def read(target, size):
            self.assertEqual(ctypes.sizeof(TraceRecord), size)
            try:
                event, created, path = next(rows)
            except StopIteration:
                return 259
            row = ctypes.cast(target, ctypes.POINTER(TraceRecord)).contents
            row.pid, row.event, row.creation, row.path = 123, event, created, path
            return 0
        o.end_trace, o.read_trace = stop, read
        return o

    @staticmethod
    def fail_image():
        raise RuntimeError("unapproved image")

    def rows(self):
        names = REQUIRED_AT_LOAD | {"native-probe.exe", "nvcuda.dll"}
        return [(1, 456, "")] + [(5, 0, n) for n in names] + [(2, 456, "")]

    def test_complete_synthetic_interval(self):
        self.assertTrue(self.fixture(self.rows()).finish()["valid"])

    def test_loss_or_unconfirmed_stop(self):
        for dropped, rc in [(1, 0), (0, 1460)]:
            with self.assertRaises(RuntimeError):
                self.fixture(self.rows(), dropped, rc).finish()

    def test_missing_endpoint_image_or_wrong_instance(self):
        rows = self.rows()
        for sequence in (rows[:-1], rows[1:], rows[:1]+rows[2:],
                         rows + [rows[-1]], rows[:-1]+[(2,999,"")],
                         rows[:1]+[(5,0,"unknown.dll")]+rows[1:]):
            with self.assertRaises(RuntimeError):
                self.fixture(sequence).finish()


if __name__ == "__main__":
    unittest.main(verbosity=2)
