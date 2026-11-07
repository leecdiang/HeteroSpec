import copy,os,sys,tempfile,unittest,struct
from pathlib import Path
from common import V,load,save,sha
from prepare_rtx import root
from runner import Child,helper,env,trace_audit
from inputs_rtx import materialize,verify,span
from analysis_rtx import analyze
from plan import build
class Adapter(unittest.TestCase):
    def test_arithmetic_unchanged(self):
        for n in ['graph_base.h','hs113_graph.h','core_gate.h','cupti_observer.h']:
            self.assertEqual(sha(V/n),sha(Path('D:/hs122/benchmarks/rtx_mechanism_baselines_v1')/n))
    def test_strided_padding_and_negative(self):
        a=dict(ne=[2,3,2,1],nb=[2,8,4,24],type=1);b=dict(ne=[2,5,2,1],nb=[2,8,4,40],type=1);raw=bytes(range(24));out=materialize(raw,a,b,'K');self.assertEqual(verify(raw,a,out,b,'K'),(12,8))
        bad=bytearray(out);bad[-1]=1
        with self.assertRaises(AssertionError):verify(raw,a,bad,b,'K')
        with self.assertRaises(AssertionError):verify(raw,a,out[:-1],b,'K')
    def test_all_actual_logical_and_padding_words(self):
        rows=load(root()/'INPUTS.json');count=0
        for c in rows.values():
            old=Path(c['logical_root']);m=load(old/'snapshot.json')
            for role in ['Q','K','V','mask']:
                verify((old/(role+'.bin')).read_bytes(),m[role],(Path(c['root'])/(role+'.bin')).read_bytes(),c['metadata'][role],role);count+=1
        self.assertEqual(count,96)
    def test_actual_Windows_cleanup_and_timeout(self):
        d=root()/('CPU_CLEANUP_'+str(len(list(root().glob('CPU_CLEANUP*')))));d.mkdir();s=load(root()/'RUN_SPEC.json');w=Child(helper());w.run([sys.executable,'-B','-c','print("CPU")'],d/'normal',10,env(s),s['host_RAM_bytes']);self.assertEqual(load(d/'normal.LIFETIME.json')['exit_code'],0)
        with self.assertRaises(AssertionError):w.run([sys.executable,'-B','-c','import time;time.sleep(20)'],d/'timeout',.25,env(s),s['host_RAM_bytes'])
        self.assertIsNone(w.job);self.assertIsNone(w.active)
    def test_native_preCUDA_identity_rejection(self):
        d=root()/('CPU_NEGATIVE_'+str(len(list(root().glob('CPU_NEGATIVE*')))));d.mkdir();s=load(root()/'RUN_SPEC.json');c=next(iter(load(root()/'INPUTS.json').values()))
        for i,change in enumerate([dict(execution_id='wrong'),dict(graph_mode='unknown'),dict(method='H2'),dict(capture_reference=True)]):
            j=dict(spec=str(root()/'RUN_SPEC.json'),execution_id=s['execution_id'],context=c,layout='QB',lifecycle='persistent_inputs',stage='reference',warmups=0,calls=1,method='H1',capture_reference=False,graph_mode='OFF');j.update(change);save(d/f'{i}.json',j);w=Child(helper())
            with self.assertRaises(AssertionError):w.run([str(V/'build/collector.exe'),'--cpu',str(d/f'{i}.json'),str(d/f'result{i}')],d/f'host{i}',120,env(s),s['host_RAM_bytes'])
            self.assertFalse(any('cuda' in p.lower() or 'cublas' in p.lower() for p in load(d/f'result{i}/NATIVE_ERROR.json')['modules']))
    def test_mode_proof_missing_replay(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);save(p/'GRAPH.json',{});j=dict(cupti_sha256='1'*64,cupti_path=str(p/'observer'),graph_mode='ON',warmups=2,calls=2)
            save(p/'CUDA_TRACE.json',dict(overflow=False,dropped=0,flush_status=0,module_sha256=j['cupti_sha256'],module_path=j['cupti_path'],API_events=[],activities=[],activity_enable=[]));self.assertFalse(trace_audit(p,j)['verified'])
    def test_practical_rule_both_controls_values_and_sessions(self):
        p=build();rows=[]
        for t in p['timed_jobs']:
            arm=t['arm'];value=100 if arm in ['native_A','native_B','QB_A','QB_B'] else 80
            rows.append(dict(t,planned_session=t['session'],values_us=[value]*30,actual_session='s'+str(t['session']),eligible=True))
        a=analyze(p,rows,100);self.assertEqual(a['geometries']['B0-1023']['candidates']['pad_1'],'PRACTICAL_CANDIDATE')
        bad=copy.deepcopy(rows)
        for h in bad:
            if h['arm']=='native_B':h['values_us']=[70]*30
        a=analyze(p,bad,100);self.assertEqual(a['geometries']['B0-1023']['candidates']['pad_1'],'NOT_ESTABLISHED')
        bad=copy.deepcopy(rows)
        for h in bad:
            if h['arm']=='pad_1' and h['cell'].endswith('v1'):h['values_us']=[101]*30
        a=analyze(p,bad,100);self.assertEqual(a['geometries']['B0-1023']['candidates']['pad_1'],'NOT_ESTABLISHED')
    def test_analysis_no_fake_missing_or_duplicate(self):
        p=build();a=analyze(p,[],100);self.assertEqual(sum(x['started'] for x in a['coverage']),0);self.assertEqual(a['geometries']['B0-1023']['candidates']['pad_1'],'NOT_ESTABLISHED')
        t=p['timed_jobs'][0];h=dict(t,planned_session=t['session'],values_us=[1]*30,actual_session='s',eligible=True)
        with self.assertRaises(AssertionError):analyze(p,[h,h],100)
if __name__=='__main__':unittest.main()
