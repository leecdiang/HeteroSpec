"""Actual shared-core graph/address checks and Windows cleanup tests; CPU only."""
import copy,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from common import V,load,save,sha
from prepare_rtx import root,scalar,values
from collect import Child,helper,env

class AdapterTests(unittest.TestCase):
    def test_recipe_edges(self):
        import numpy as np
        counters=np.array([0,1,31,8191,8192,2**32,2**63-1],dtype=np.uint64)
        for role,salt,mod in [('Q',0x51,17),('K',0x4b,17),('V',0x56,33)]:
            for realization in range(2):
                got=values(counters,20261018+realization,salt,realization,mod,'<f4')
                self.assertEqual(got.tolist(),[scalar(int(i),20261018+realization,salt,realization,mod) for i in counters])
    def test_factor_logical_overlap(self):
        import numpy as np
        rows=load(root()/'INPUTS.json')
        for q in [2,4]:
            for real in [0,1]:
                a=rows[f'q{q}-k256-v{real}'];b=rows[f'q{q}-compact-v{real}'];d=a['d'];H=a['Hq']
                x=np.fromfile(Path(a['root'])/'Q.bin',dtype='<f4').reshape(q,H,d);y=np.fromfile(Path(b['root'])/'Q.bin',dtype='<f4').reshape(H,q,d).transpose(1,0,2)
                self.assertTrue(np.array_equal(x,y));self.assertEqual((Path(a['root'])/'K.bin').read_bytes(),(Path(b['root'])/'K.bin').read_bytes())
    def test_real_windows_lifecycle(self):
        s=load(root()/'RUN_SPEC.json');folder=root()/'CPU_CLEANUP';folder.mkdir();w=Child(helper())
        w.run([sys.executable,'-B','-c','print("cpu-only lifecycle")'],folder/'normal',10,env(s),s['host_RAM_bytes'])
        self.assertEqual(load(folder/'normal.LIFETIME.json')['exit_code'],0)
        with self.assertRaises(AssertionError):w.run([sys.executable,'-B','-c','import time;time.sleep(20)'],folder/'timeout',.25,env(s),s['host_RAM_bytes'])
        self.assertIsNone(w.active);self.assertIsNone(w.job)
        self.assertTrue(load(folder/'timeout.LIFETIME.json')['error'])

def graphs():
    r=root();s=load(r/'RUN_SPEC.json');cases=load(r/'INPUTS.json');count=words=0
    for cid,c in cases.items():
        folder=r/'CPU'/cid;folder.mkdir(parents=True)
        for l in ['PQ','QB','QH_C']:
            job=folder/(l+'_JOB.json');save(job,dict(spec=str(r/'RUN_SPEC.json'),context=c,layout=l));w=Child(helper());w.run([str(V/'build/address_cpu.exe'),str(job),str(folder/(l+'.json'))],folder/(l+'_host'),120,env(s),s['host_RAM_bytes']);res=load(folder/(l+'.json'));assert res['status']=='PASS' and res['CUDA_loads']==0;words+=res['whole_Q_mask_output_words'];count+=1
    negative=r/'CPU_NEGATIVE';negative.mkdir();c=next(c for c in cases.values() if c['q']==2)
    for i,change in enumerate([dict(capture_reference=True),dict(method='H2'),dict(execution_id='wrong-UUID')]):
        job=dict(spec=str(r/'RUN_SPEC.json'),execution_id=s['execution_id'],context=c,layout='PQ',lifecycle='persistent_inputs',stage='reference',warmups=0,calls=1,method='H1',capture_reference=False);job.update(change);path=negative/f'job{i}.json';save(path,job);w=Child(helper())
        try:w.run([str(V/'build/collector.exe'),'--cpu',str(path),str(negative/f'result{i}')],negative/f'host{i}',120,env(s),s['host_RAM_bytes'])
        except AssertionError:pass
        else:raise AssertionError('negative native admission accepted')
        err=load(negative/f'result{i}/NATIVE_ERROR.json');assert not any('cuda' in str(p).lower() or 'cublas' in str(p).lower() for p in err['modules'])
    return count,words
if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(AdapterTests);res=unittest.TextTestRunner(verbosity=2).run(suite);assert res.wasSuccessful();count,words=graphs();save(V/'CPU_RTX_TESTS.json',dict(status='PASS',tests=res.testsRun,full_native_graphs=count,complete_Q_mask_output_words=words,native_admission_rejections=3,real_Windows_cleanup_and_timeout=True,GPU_calls=0,CUDA_loads=0));print('CPU actual graphs PASS',count,words)
