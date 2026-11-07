"""CPU-only execution-boundary regressions; does not invoke qh-vulkan."""
import copy, io, pathlib, sys, unittest
from unittest.mock import patch
from common import ROOT, load, save, sha, modules
import run_s1
sys.path.insert(0,str(ROOT))
import evidence, plan, core

class HostTests(unittest.TestCase):
    def test_wrong_or_missing_author_F0_denied_before_launch(self):
        f0=load(ROOT/'host/S1_F0.json')
        with patch('subprocess.Popen',side_effect=AssertionError('no host launch allowed')):
            for wrong in (None,'','0'*64,False):
                with self.assertRaises(ValueError):run_s1.admission(f0,wrong)

    def test_current_F0_static_files_bind_without_device(self):
        f0=load(ROOT/'host/S1_F0.json')
        with patch('subprocess.Popen',side_effect=AssertionError('no host launch allowed')):
            run_s1.admission(f0,sha(ROOT/'host/S1_F0.json'))

    def test_changed_source_denied(self):
        f0=load(ROOT/'host/S1_F0.json');f0['sources']['native/query_head.h']='0'*64
        with self.assertRaises(ValueError):run_s1.admission(f0,sha(ROOT/'host/S1_F0.json'))

    def test_CPU_fallback_module_denied(self):
        f0=load(ROOT/'host/S1_F0.json');event=dict(modules=[x['path'] for x in f0['dependencies']])
        run_s1.runtime_gate(event,f0)
        event['modules'].append(str(ROOT/'build/Release/ggml-cpu.dll'))
        with self.assertRaises(ValueError):run_s1.runtime_gate(event,f0)

    def test_partial_failed_attempt_is_not_unstarted(self):
        slots=[dict(id=x) for x in ('one','two','three')]
        r=run_s1.slot_accounting(slots,['one'],[],[])
        self.assertEqual(r,dict(failed=['one'],unstarted=['two','three']))

    def test_unsupported_skip_is_not_execution(self):
        slots=[dict(id=x) for x in ('one','two','three')]
        r=run_s1.slot_accounting(slots,['one'],['one'],['two'])
        self.assertEqual(r,dict(failed=[],unstarted=['three']))
        with self.assertRaises(ValueError):run_s1.slot_accounting(slots,['one','one'],[],[])

    def test_complete_census_grid_required_without_numeric_fields(self):
        f0sha=sha(ROOT/'host/S1_F0.json');rows=[]
        for c in plan.operator_cells():
            for m in plan.GPU_MODES:rows.append(dict(cell_sha256=core.sha(c),mode=m,compute_nodes=[dict(id='test',op='MUL_MAT',supports_op=True)],raw_sha256='a'*64))
        synthetic=dict(binding_sha256=f0sha,observations=rows)
        self.assertEqual(evidence.choose_from_capabilities(synthetic,f0sha),'QH_C')
        bad=copy.deepcopy(synthetic);bad['observations'].pop()
        with self.assertRaises(ValueError):evidence.choose_from_capabilities(bad,f0sha)
        bad=copy.deepcopy(synthetic);bad['latency']=0
        with self.assertRaises(ValueError):evidence.choose_from_capabilities(bad,f0sha)

if __name__=='__main__':
    before=modules();stream=io.StringIO();r=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(HostTests))
    save(ROOT/'host/HOST_CONTROL_TESTS.json',dict(tests=r.testsRun,success=r.wasSuccessful(),log=stream.getvalue(),
         F0_sha256=sha(ROOT/'host/S1_F0.json'),
         scope='CPU/synthetic gate regressions, not a capability census or Vulkan result; test SHA checks are not author approval',
         S1_executable_launched=False,device_queries=0,GPU_starts=0,modules_before=before,modules_after=modules()))
    print(stream.getvalue());raise SystemExit(0 if r.wasSuccessful() else 1)
