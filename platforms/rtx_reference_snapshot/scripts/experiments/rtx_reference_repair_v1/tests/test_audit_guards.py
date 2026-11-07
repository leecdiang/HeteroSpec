"""Additional state, raw-evidence and resource-failure controls. All inputs are synthetic."""
from __future__ import annotations
import copy,json,struct,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(HERE))
import common as c
import audit,plan,probes,run,archive
from test_repair import panel,endpoint,policy

def ordinary():
    e=endpoint([1,2,3]);return dict(e,endpoint=e,prompt_tokens=3,draft_enabled=False,cycles=[],
          vocabulary_eog=[3],target_final_kv={'min':0,'max':4},draft_final_kv=None)

def speculative(reject=False):
    if reject:
        ids=[1,5];proposals=[2,3,4];decisions=[5,9,9,9];accepted=0;kind='correction';eog=5
    else:
        ids=[1,2,3,4,5];proposals=[2,3,4];decisions=[2,3,4,5];accepted=3;kind='bonus';eog=5
    e=endpoint(ids);keep=3+1+accepted
    cy={'cycle':0,'base':3,'seed':1,'proposals':proposals,'decisions':decisions,'accepted':accepted,
        'rejected':reject,'commit_kind':kind,'keep':keep,'output_length':len(ids),'done':True,
        'pending_after':None,'target_after':{'min':0,'max':keep-1},'draft_after':{'min':0,'max':keep-1}}
    return dict(e,endpoint=e,prompt_tokens=3,draft_enabled=True,k=3,cycles=[cy],vocabulary_eog=[eog],
       target_final_kv={'min':0,'max':keep-1},draft_final_kv={'min':0,'max':keep-1})

def matrix_fixture():
    p=panel(4);slots=plan.development(p);refs={x['id']:endpoint() for x in p['inputs']}
    rows=[{'slot':s,'endpoint':endpoint(),'cycles':[],'target_final_kv':{'max':4},'draft_final_kv':None} for s in slots]
    return p,slots,refs,rows

class TransactionTests(unittest.TestCase):
    def test_ordinary_pending_once(self):audit.transaction_check(ordinary())
    def test_ordinary_incorrect_state_rejected(self):
        r=ordinary();r['target_final_kv']['max']+=1
        with self.assertRaises(ValueError):audit.transaction_check(r)
    def test_speculative_all_accepted_bonus(self):audit.transaction_check(speculative())
    def test_speculative_rejection(self):audit.transaction_check(speculative(True))
    def test_accepted_count_corruption(self):
        r=speculative();r['cycles'][0]['accepted']=2
        with self.assertRaises(ValueError):audit.transaction_check(r)
    def test_final_pending_corruption(self):
        r=speculative(True);r['cycles'][0]['pending_after']=5
        with self.assertRaises(ValueError):audit.transaction_check(r)
    def test_wrong_trim(self):
        r=speculative();r['cycles'][0]['target_after']['max']-=1
        with self.assertRaises(ValueError):audit.transaction_check(r)
    def test_vocab_eog(self):
        r=ordinary();r['vocabulary_eog']=[]
        with self.assertRaises(ValueError):audit.transaction_check(r)

class MatrixTests(unittest.TestCase):
    def test_complete_dev_matrix(self):
        p,s,refs,rows=matrix_fixture();r=audit.matrix(rows,p,s,refs)
        self.assertEqual(len(r['cells']),48);self.assertTrue(r['all_reference_equal'])
    def test_reference_failure_is_retained_not_crash(self):
        p,s,refs,rows=matrix_fixture()
        for r in rows:
            if r['slot']['source_index']==0 and r['slot']['arm']=='M_QB':r['endpoint']=endpoint([4,5,3])
        x=audit.matrix(rows,p,s,refs);self.assertFalse(x['all_reference_equal']);self.assertEqual(len(x['cells']),48)
    def test_observer_contamination(self):
        p,s,refs,rows=matrix_fixture();rows[1]['endpoint']=endpoint([4,5,3])
        self.assertTrue(audit.matrix(rows,p,s,refs)['observer_errors'])
    def test_missing_matrix_record(self):
        p,s,refs,rows=matrix_fixture()
        with self.assertRaises(ValueError):audit.matrix(rows[:-1],p,s,refs)
    def test_duplicate_matrix(self):
        p,s,refs,rows=matrix_fixture();rows[-1]=rows[0]
        with self.assertRaises(ValueError):audit.matrix(rows,p,s,refs)
    def test_state_artifact_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);f=p/'target_final.state';f.write_bytes(b'abc')
            r={'draft_enabled':False,'target_state':{'bytes':3,'sha256':c.file_hash(f)}}
            audit.verify_states(r,p);f.write_bytes(b'abd')
            with self.assertRaises(ValueError):audit.verify_states(r,p)

class BudgetAndProbeTests(unittest.TestCase):
    def test_unsettled_attempt_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'ledger';c.append(p,{'event':'START','epoch':'x','unit':'a','reserved_requests':8})
            with self.assertRaises(ValueError):run.resource_totals(p)
    def test_unmatched_end_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'ledger';c.append(p,{'event':'END','epoch':'x','unit':'a','seconds':1})
            with self.assertRaises(ValueError):run.resource_totals(p)
    def test_cumulative_budget_across_epochs(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'ledger'
            for e in ('e1','e2'):
                c.append(p,{'event':'START','epoch':e,'unit':'a','reserved_requests':8})
                c.append(p,{'event':'END','epoch':e,'unit':'a','seconds':2})
            self.assertEqual(run.resource_totals(p),(16,4))
    def test_probe_first_prefill_and_controls(self):
        with tempfile.TemporaryDirectory() as d:
            b=Path(d);c.save(b/'DEV.json',panel(4));c.save(b/'DEV_REFERENCES.json',{'x/0':endpoint([5,6,3])})
            ss=probes.make_probes(b,'x/0',0,b/'probe.json')
            self.assertEqual(len(ss),8);self.assertEqual(ss[1]['repair']['trace']['phases'],['PREFILL'])
            self.assertTrue(all(s['category']=='diagnostic' and s['repair']['probe'] for s in ss))
    def test_first_divergence_length(self):self.assertEqual(probes.first_difference([1,2],[1,2,3]),2)
    def test_first_divergence_none(self):self.assertIsNone(probes.first_difference([1,2],[1,2]))


class GeometryTests(unittest.TestCase):
    def nodes(self):
        return [{'name':f'kq-{i}','op':'MUL_MAT','layer':i,'scheduler_backend':'CPU' if i<17 else 'CUDA0',
          'buffer_owner_device':'NVIDIA (not execution evidence)'} for i in range(40)]
    def test_scheduler_coverage_without_weight_inference(self):
        r=audit.geometry_check(self.nodes());self.assertEqual(r['layers'],40);self.assertEqual(r['backend_names'],['CPU','CUDA0'])
    def test_empty_geometry_rejected(self):
        with self.assertRaises(ValueError):audit.geometry_check([])
    def test_missing_layer_rejected(self):
        with self.assertRaises(ValueError):audit.geometry_check(self.nodes()[:-1])
    def test_buffer_label_alone_rejected(self):
        a=self.nodes();a[0]['scheduler_backend']=None
        with self.assertRaises(ValueError):audit.geometry_check(a)
    def test_view_is_not_qk_compute(self):
        a=self.nodes();a[0]['op']='VIEW'
        with self.assertRaises(ValueError):audit.geometry_check(a)
    def test_nested_endpoint_mutation(self):
        r=ordinary();r['endpoint']=endpoint([5,6,3])
        with self.assertRaises(ValueError):audit.transaction_check(r)


class ObserverModeTests(unittest.TestCase):
    def test_timing_skips_metadata_inventory(self):
        text=(HERE/'repair_observer.inc').read_text()
        self.assertIn('if(!o.observe_target||!o.metadata_enabled)return false;',text)
    def test_peak_producer_allocation_admitted(self):
        import native
        raw=(HERE/'tests/fixtures/pr151_worker.cpp').read_text()
        adapter=(HERE/'tests/fixtures/pr156_adapter.py.txt').read_bytes()
        text=native.adapt(native.inherited_adapt(raw,adapter),(HERE/'repair_observer.inc').read_text())
        self.assertIn('producer_allocation_probes',text)
        self.assertIn('producer context violates VRAM reserve',text)

if __name__=='__main__':unittest.main(verbosity=2)
