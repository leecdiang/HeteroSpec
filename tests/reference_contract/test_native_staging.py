import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts/reference_contract'/f'{name}.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
port=load('port_observer').port
harden=load('harden_native').harden
cuda_stage=load('stage_cuda_audit').stage
class NativeStagingTests(unittest.TestCase):
    def test_cuda_requires_staged_tree(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):cuda_stage(Path(d))
    def test_observer_port(self):
        text='#include <windows.h>\n#include <psapi.h>\ninline j modules(){return {};}\ninline int decode(){}'
        actual=port(text)
        self.assertIn('#ifdef _WIN32',actual);self.assertIn('dl_iterate_phdr',actual)
        self.assertIn('inline j modules(){return {};}',actual)
        self.assertTrue(actual.endswith('inline int decode(){}'))
    def test_observer_missing_anchor(self):
        with self.assertRaises(ValueError):port('unknown')
    def test_hardening_missing_anchor(self):
        with self.assertRaises(ValueError):harden('unknown')
    def test_hardening_wrong_assertion_count(self):
        with self.assertRaises(ValueError):
            harden('    if (hs_query_batch && hs_scope::layout95()==1 && q->ne[2] > 1) {\n    const bool v_trans = false;')
if __name__=='__main__':unittest.main()
