"""Negative evidence tests, without GPU execution or controller imports."""
import pathlib, tempfile, unittest
import verify
class EvidenceRisks(unittest.TestCase):
    def test_early_eos(self):
        with self.assertRaises(AssertionError):verify.endpoint([151645,42],['EOS'])
    def test_cap_overshoot(self):
        with self.assertRaises(AssertionError):verify.endpoint([42]*129,['limit'])
    def test_eog_at_cap_requires_both_markers(self):
        self.assertEqual(verify.endpoint([42]*127+[151645],['limit','EOS']),'EOS')
        with self.assertRaises(AssertionError):verify.endpoint([42]*127+[151645],['limit'])
    def test_missing_endpoint(self):
        with self.assertRaises(AssertionError):verify.endpoint([42]*128,[])
    def test_duplicate_matrix_key(self):
        with self.assertRaises(AssertionError):verify.validate_keys(['x','x'],['x','y'])
    def test_mixed_attempts(self):
        with self.assertRaises(AssertionError):verify.validate_attempt_files({'attempt-01/log':{},'attempt-02/log':{}},'attempt-01')
    def test_truncated_capture(self):
        root=pathlib.Path(__file__).resolve().parents[3]
        p=next((root/'work/rtx-target-only-bridge-v1/engineering/HumanEval-15-U2-r1').glob('attempt-*/native.log'))
        with tempfile.TemporaryDirectory() as temp:
            q=pathlib.Path(temp)/'truncated.log';q.write_bytes(p.read_bytes()[:p.stat().st_size//2])
            with self.assertRaises(AssertionError):verify.raw_native(q)
if __name__=='__main__':unittest.main()
