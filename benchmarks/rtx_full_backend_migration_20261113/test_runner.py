import json
from pathlib import Path
import sys
import tempfile
import unittest
from run_session import completed, run
class RunnerTests(unittest.TestCase):
    def test_partial(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x';p.write_bytes(b'{"event":"loaded"}\n{"eve');self.assertEqual(len(completed(p)),1)
    def test_success(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x';cmd=[sys.executable,'-c','import pathlib,sys;pathlib.Path(sys.argv[1]).write_text(\'{"event":"done"}\\n\')',str(p)]
            self.assertEqual(run(cmd,p)[-1]['event'],'done')
    def test_failure(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(RuntimeError):run([sys.executable,'-c','raise SystemExit(3)'],Path(d)/'x')
    def test_missing_done(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(RuntimeError):run([sys.executable,'-c','pass'],Path(d)/'x')
    def test_timeout(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(TimeoutError):run([sys.executable,'-c','import time;time.sleep(10)'],Path(d)/'x',timeout=.1)
if __name__=='__main__':unittest.main()
