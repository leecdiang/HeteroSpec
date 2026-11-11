"""Ensure network recovery cannot become a scientific retry; CPU only."""
from pathlib import Path
import subprocess
import tempfile
import unittest
import experiment as e
import supervise_e2_transport as recovery

class TransportBoundaryTests(unittest.TestCase):
    def test_session_receipt_or_lock_blocks_recovery(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'ledger').mkdir()
            self.assertTrue(recovery.untouched(root,4))
            e.save(root/'SESSION-4.json',{'session':4})
            self.assertFalse(recovery.untouched(root,4))
            self.assertTrue(recovery.untouched(root,5))
            (root/'EXECUTION.lock').write_text('owned')
            self.assertFalse(recovery.untouched(root,5))

    def test_even_native_load_without_request_blocks_recovery(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'ledger').mkdir()
            e.save(root/'ledger/0000.json',{'slot':'formal/Qwen/s4/Qwen/b00/LOAD'})
            self.assertFalse(recovery.untouched(root,4))
            self.assertTrue(recovery.untouched(root,5))

    def test_only_gh_api_process_failure_is_control_recoverable(self):
        self.assertTrue(recovery.is_transport(subprocess.CalledProcessError(1,['gh','api','fixed-ref'])))
        self.assertFalse(recovery.is_transport(ValueError('remote bytes differ')))
        self.assertFalse(recovery.is_transport(subprocess.CalledProcessError(1,['llama-server.exe'])))

if __name__=='__main__':unittest.main(verbosity=2)
