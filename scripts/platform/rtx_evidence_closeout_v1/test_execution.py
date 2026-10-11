"""Real adapter contract guards; no GPU requests."""
import copy, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import resident, run_common, stages
import deliver, closeout
from test_closeout import fixture,D

class ExecutionGuards(unittest.TestCase):
    def test_raw_eog_suffix_is_retained_and_invalid(self):
        c=stages.ordinary(1,'R');task={'cap':3,'prompt_ids':[1,2]}
        obs=dict(adapter='hsc89-v1',mode='counts',scope_mask=0,context=1024,effective_batch=1024,target_ub=1,phase_timers=False,heavy_capture=False,etw=False,added_sync=False)
        response=dict(tokens=[7,9,7],tokens_predicted=3,stop_type='eos',truncated=False,timings=dict(cache_n=0,prompt_n=2),hs_closeout=obs)
        out,valid,_=resident.normalize(response,task,'Qwen',c,'counts',{9})
        self.assertFalse(valid);self.assertEqual(out['ids'],[7,9,7])
        response.update(tokens=[7,9],tokens_predicted=2)
        out,valid,_=resident.normalize(response,task,'Qwen',c,'counts',{9});self.assertTrue(valid)
        response['timings']['cache_n']=1
        self.assertFalse(resident.normalize(response,task,'Qwen',c,'counts',{9})[1])
    def test_actual_observer_and_ub_identity_required(self):
        c=stages.ordinary(1,'R');task={'cap':1,'prompt_ids':[1]}
        obs=dict(adapter='hsc89-v1',mode='counts',scope_mask=0,context=1024,effective_batch=1024,target_ub=1,phase_timers=False,heavy_capture=False,etw=False,added_sync=False)
        response=dict(tokens=[7],tokens_predicted=1,stop_type='limit',truncated=False,timings=dict(cache_n=0,prompt_n=1),hs_closeout=obs)
        for key,val in [('mode','heavy'),('added_sync',True),('target_ub',4),('phase_timers',True)]:
            r=copy.deepcopy(response);r['hs_closeout'][key]=val
            with self.assertRaises(AssertionError):resident.normalize(r,task,'Qwen',c,'counts',set())
    def test_immutable_writer_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/'a.json';run_common.save(p,{'slot':'one'})
            with self.assertRaises(FileExistsError):run_common.save(p,{'slot':'two'})
            self.assertEqual(run_common.read(p),{'slot':'one'})
    def test_core_and_profile_cannot_borrow_budgets(self):
        with tempfile.TemporaryDirectory() as root,patch.object(resident,'LOCAL',Path(root)):
            l=resident.Ledger();l.events=[dict(family='Qwen',phase='core',kind='request',slot=str(i)) for i in range(360)]
            with self.assertRaises(AssertionError):l.charge('Qwen','core','request','overflow')
            l.events=[dict(family='Qwen',phase='profile',kind='request',slot=str(i)) for i in range(128)]
            with self.assertRaises(AssertionError):l.charge('Qwen','profile','request','overflow')
            with self.assertRaises(AssertionError):l.charge('Qwen','profile','request','0')
    def test_delivery_report_uses_actual_analyser_interface(self):
        inputs,plan,freeze,rows=fixture();result=closeout.analyse(D,plan,inputs,rows,freeze)
        with tempfile.TemporaryDirectory() as root:
            pub=Path(root)/'pub';design=Path(root)/'design';pub.mkdir();design.mkdir()
            for name,value in [('RESULTS.json',result),('FORMAL_RECORDS.json',rows),('SELECTED_ORDINARY.json',plan['ordinary_selection'])]:run_common.save(pub/name,value)
            run_common.save(design/'DESIGN.json',D)
            with patch.object(deliver,'PUB',pub),patch.object(deliver,'DESIGN',design),patch.object(deliver,'figures'):
                deliver.reports()
            self.assertTrue((pub/'RESULTS.md').exists());self.assertTrue((pub/'LENGTH_DOMAIN_STOP_RECORDS.json').exists())
    def test_actual_load_log_restores_request_verbosity_and_offload(self):
        # Real zero-forward repair probe, if present; no GPU is launched by this test.
        path=run_common.PUB/'LOAD_METADATA_REPAIR_PROOF.json'
        if not path.exists():self.skipTest('execution host load proof not present')
        proof=run_common.read(path)
        self.assertEqual(proof['status'],'PASS');self.assertEqual(proof['requested_forwards'],0)
        layers=proof['actual_loaded_identity']['layers'];self.assertEqual(len(layers),1)
        self.assertTrue(all(a==b for a,b in layers))
        self.assertEqual(int(proof['actual_loaded_identity']['ubs'][0]),1)

if __name__=='__main__':unittest.main()
