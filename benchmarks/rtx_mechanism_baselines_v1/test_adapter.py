import copy,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from common import V,load,save,sha
from prepare_rtx import root
from runner import Child,helper,env
class Adapter(unittest.TestCase):
    def test_parent_graph_identity(self):
        for name in ['graph_base.h','hs113_graph.h','core_gate.h']:
            self.assertEqual(sha(V/name),sha(V.parent/'rtx_boundary_confirmation_v1'/name))
    def test_Q_transpose_full_bytes(self):
        import numpy as np
        rows=load(root()/'INPUTS.json')
        for q in [2,4]:
            for v in [0,1]:
                a=rows[f'q{q}-k256-v{v}'];b=rows[f'q{q}-compact-v{v}']
                raw=(Path(a['root'])/'Q.bin').read_bytes();actual=np.frombuffer(raw,dtype='<f4').reshape(q,32,128).transpose(1,0,2).copy().tobytes()
                self.assertEqual(actual,(Path(b['root'])/'Q.bin').read_bytes())
                for role in ['K','V','mask']:self.assertEqual(sha(Path(a['root'])/(role+'.bin')),sha(Path(b['root'])/(role+'.bin')))
    def test_real_Windows_cleanup(self):
        s=load(root()/'RUN_SPEC.json');d=root()/('CPU_CLEANUP_REV'+str(len(list(root().glob('CPU_CLEANUP*')))));d.mkdir();w=Child(helper());w.run([sys.executable,'-B','-c','print("CPU")'],d/'normal',10,env(s),s['host_RAM_bytes'])
        self.assertEqual(load(d/'normal.LIFETIME.json')['exit_code'],0)
        with self.assertRaises(AssertionError):w.run([sys.executable,'-B','-c','import time;time.sleep(20)'],d/'timeout',.25,env(s),s['host_RAM_bytes'])
        self.assertIsNone(w.job);self.assertIsNone(w.active)
    def test_native_preCUDA_rejections(self):
        s=load(root()/'RUN_SPEC.json');c=load(root()/'INPUTS.json')['q2-k256-v0'];d=root()/('CPU_NEGATIVE_REV'+str(len(list(root().glob('CPU_NEGATIVE*')))));d.mkdir()
        for i,change in enumerate([dict(capture_reference=True),dict(method='H2'),dict(execution_id='wrong'),dict(graph_mode='UNKNOWN')]):
            job=dict(spec=str(root()/'RUN_SPEC.json'),execution_id=s['execution_id'],context=c,layout='PQ',lifecycle='persistent_inputs',stage='reference',warmups=0,calls=1,method='H1',capture_reference=False,graph_mode='OFF');job.update(change);p=d/f'job{i}.json';save(p,job);w=Child(helper())
            with self.assertRaises(AssertionError):w.run([str(V/'build/collector.exe'),'--cpu',str(p),str(d/f'result{i}')],d/f'host{i}',120,env(s),s['host_RAM_bytes'])
            record=load(d/f'result{i}/NATIVE_ERROR.json');self.assertFalse(any('cuda' in str(p).lower() or 'cublas' in str(p).lower() for p in record['modules']))
    def test_mode_proof_requires_real_events(self):
        from runner import trace_audit
        with tempfile.TemporaryDirectory() as name:
            p=Path(name);save(p/'GRAPH.json',{});job=dict(cupti_sha256='1'*64,cupti_path=str(p/'cupti.dll'),graph_mode='ON',warmups=2,calls=2)
            def ev(n,i):return dict(domain=2,site=1,name=n,status=0,call=i)
            events=[ev('cudaStreamBeginCapture',1),ev('cudaStreamEndCapture',1),ev('cudaGraphInstantiate',1),ev('cudaGraphLaunch',2),ev('cudaGraphLaunch',3)]
            for i,eventset in enumerate([[],events,events[:-1],events+[ev('cudaStreamBeginCapture',3)]]):
                d=p/str(i);d.mkdir();save(d/'GRAPH.json',{});save(d/'CUDA_TRACE.json',dict(module_sha256='1'*64,module_path=job['cupti_path'],overflow=False,dropped=0,flush_status=0,API_events=eventset,activities=[],activity_enable=[]))
                self.assertEqual(trace_audit(d,job)['verified'],i==1)
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Adapter));save(V/('CPU_ADAPTER_TESTS_REV'+str(len(list(V.glob('CPU_ADAPTER_TESTS*.json'))))+'.json'),dict(tests=result.testsRun,success=result.wasSuccessful(),GPU_calls=0,CUDA_loads=0));assert result.wasSuccessful()
