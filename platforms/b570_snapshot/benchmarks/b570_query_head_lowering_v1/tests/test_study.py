"""Synthetic tests of this package, not Windows/GGML/Vulkan experiment results."""
import copy
import itertools
import math
import struct
import tempfile
import unittest
from pathlib import Path
import core
import oracle
import plan
import evidence
from ledger import Ledger

H='a'*64

def inventory():
    return [dict(id=f'SYNTHETIC/{d}/{b}/{i}',domain=d,prompt_ids=[100+100*di+10*b+i]+[7]*(n-1),
                 source_sha256=H,tokenizer_sha256='b'*64,template_sha256='c'*64)
            for di,d in enumerate(('code','math')) for b,n in enumerate((90,180,300)) for i in range(4)]

def selected():
    return plan.select_panel(inventory(),dict(ids=[],prompt_sha256=[],scope_sha256=H,review_complete=True))

def confirmation():
    return plan.make_plan('confirm',selected()['panel'])

def census():
    return dict(binding_sha256=H,observations=[dict(cell_sha256=core.sha(c),mode=m,
        compute_nodes=[dict(id='qk',op='MUL_MAT',supports_op=True),dict(id='sm',op='SOFT_MAX',supports_op=True),
                       dict(id='av',op='MUL_MAT',supports_op=True)],raw_sha256='b'*64)
        for c in plan.operator_cells() for m in plan.GPU_MODES])

def endpoint(token=31):
    return dict(ids=[token]*128,eog=[False]*128,cap=128,stop='CAP')

def records(p):
    return [dict(slot=s['id'],status='COMPLETED',origin='SYNTHETIC_TEST_ONLY',request_sha256=core.sha(s),
          raw_audit_sha256=H,channel='counts',warmup=s['warmup'],process_group=s['process_group'],
          lifecycle_id=s['process_group'],runtime_role='original' if s['arm']=='R' else 'candidate',
          fresh_state=True,wall_ms=100. if s['arm']=='R' else 95.,endpoint=endpoint()) for s in p['slots']]

def sessions():
    return [dict(id=0,start=0,end=100),dict(id=1,start=3700,end=3900),dict(id=2,start=86400,end=86600)]

class StudyTests(unittest.TestCase):
    def test_geometric_map_72_descriptors(self):
        gs={core.sha(c['geometry']):c['geometry'] for c in plan.cpu_cells()}
        self.assertEqual(len(gs),72)
        for g in gs.values():self.assertGreater(oracle.address_audit(core.Geometry(**g)),0)
    def test_scalar_candidates_two_masks_and_strides(self):
        for q,heads,mask,storage in itertools.product((1,2,3,4),((4,1),(4,2)),('causal','single','holes'),('compact','permuted')):
            g=core.Geometry(8,4,q,7,*heads,storage);f=oracle.fixture(g,mask)
            expected=oracle.logical(g,f)
            self.assertEqual(expected,oracle.packed(g,f));self.assertEqual(expected,oracle.packed(g,f,True))
    def test_four_injected_faults_detected(self):
        g=core.Geometry(8,4,3,7,6,2);f=oracle.fixture(g,'causal');expected=oracle.logical(g,f)
        for fault in ('gqa_modulo','wrong_mask','wrong_output','wrong_pack'):
            self.assertNotEqual(expected,oracle.packed(g,f,fault=fault))
    def test_nondivisible_head_reject(self):
        with self.assertRaises(ValueError):core.Geometry(8,8,2,7,7,2).check()
    def test_boolean_descriptor_reject(self):
        with self.assertRaises(ValueError):core.Geometry(8,8,True,7,4,2).check()
    def test_oversized_extent_reject(self):
        with self.assertRaises(ValueError):core.Geometry(8,8,4,99999999,4,2).check()
    def test_bad_storage_reject(self):
        with self.assertRaises(ValueError):core.Geometry(8,8,2,7,4,2,'arbitrary').check()
    def test_no_all_masked_softmax(self):
        g=core.Geometry(8,4,2,7,4,2);f=oracle.fixture(g);f['mask'][0]=[-math.inf]*7
        with self.assertRaises(ValueError):oracle.logical(g,f)
        with self.assertRaises(ValueError):oracle.packed(g,f)
    def test_known_rejection_not_full_admission(self):
        g=core.Geometry(128,128,2,128,8,2)
        self.assertIs(core.lower(g,'QB4')['full_backend_support'],False)
        self.assertIsNone(core.lower(g,'QH_C')['full_backend_support'])
        self.assertIs(core.lower(g,'QH_C')['batch3_necessary_condition'],True)
    def test_unknown_backend_stays_unknown(self):
        self.assertIsNone(core.lower(core.Geometry(8,8,2,7,4,2),'QB4','unknown')['full_backend_support'])
    def test_q1_uses_common(self):
        for m in core.MODES:self.assertTrue(core.lower(core.Geometry(8,8,1,7,4,2),m)['common_original_path'])
    def test_qh_no_kv_repeat(self):
        g=core.Geometry(128,128,4,257,16,4)
        self.assertEqual(core.allocation_model(g,'QH_C')['repeated_kv_destination_bytes'],0)
        self.assertGreater(core.allocation_model(g,'REPEAT4')['repeated_kv_destination_bytes'],0)
    def test_compact_vs_permuted_copy_cost(self):
        self.assertEqual(core.allocation_model(core.Geometry(128,128,4,257,16,4,'compact'),'QH_C')['q_pack_destination_bytes'],0)
        self.assertGreater(core.allocation_model(core.Geometry(128,128,4,257,16,4),'QH_C')['q_pack_destination_bytes'],0)
    def test_all_plan_budgets(self):
        for phase,n in (('cpu',2592),('operator',161),('pilot',64),('confirm',1008)):
            p=plan.make_plan(phase,selected()['panel'] if phase=='confirm' else None)
            plan.validate_plan(p);self.assertEqual(len(p['slots']),n)
            self.assertEqual(len({s['id'] for s in p['slots']}),n)
    def test_dev_holdout_counts(self):
        rows=plan.cpu_cells();self.assertEqual(len(rows),432)
        self.assertEqual(sum(c['group']=='development' for c in rows),216)
    def test_pilot_control_precedence(self):
        p=plan.make_plan('pilot');self.assertTrue(all(s['arm']=='R' for s in p['slots'][:8]))
        self.assertTrue(all(s['arm']=='R_SHADOW' for s in p['slots'][8:16]))
        p['slots'].reverse()
        with self.assertRaises(ValueError):plan.validate_plan(p)
    def test_plan_budget_mutation_rejected(self):
        p=copy.deepcopy(plan.make_plan('pilot'));p['limits']['model_requests']=65
        with self.assertRaises(ValueError):plan.validate_plan(p)
    def test_capability_fixed_choice(self):
        self.assertEqual(evidence.choose_from_capabilities(census(),H),'QH_C')
    def test_capability_dense_only_by_support(self):
        x=census();x['observations'][2]['compute_nodes'][1]['supports_op']=False
        self.assertEqual(evidence.choose_from_capabilities(x,H),'QH_D')
    def test_capability_unknown_not_true(self):
        x=census();x['observations'][2]['compute_nodes'][0]['supports_op']=None
        with self.assertRaises(ValueError):evidence.choose_from_capabilities(x,H)
    def test_capability_refused_wrong_backend(self):
        with self.assertRaises(ValueError):evidence.choose_from_capabilities(census(),'b'*64)
    def test_capability_output_leak_rejected(self):
        x=census();x['latency']=1.
        with self.assertRaises(ValueError):evidence.choose_from_capabilities(x,H)
    def test_capability_missing_or_duplicate_rejected(self):
        x=census();x['observations'][-1]=x['observations'][0]
        with self.assertRaises(ValueError):evidence.choose_from_capabilities(x,H)
    def test_holdout_deterministic(self):
        e=dict(ids=[],prompt_sha256=[],scope_sha256=H,review_complete=True)
        self.assertEqual(plan.select_panel(inventory(),e),plan.select_panel(inventory()[::-1],e))
    def test_exposed_input_not_replaced_by_outcome(self):
        e=dict(ids=[inventory()[0]['id']],prompt_sha256=[],scope_sha256=H,review_complete=True)
        with self.assertRaises(ValueError):plan.select_panel(inventory(),e)
    def test_exposure_review_required(self):
        with self.assertRaises(ValueError):plan.select_panel(inventory(),dict(review_complete=False))
    def test_no_latency_in_input_selection(self):
        x=inventory();x[0]['latency']=0
        with self.assertRaises(ValueError):plan.select_panel(x,dict(ids=[],prompt_sha256=[],scope_sha256=H,review_complete=True))
    def test_full_endpoint_required(self):
        e=endpoint();e['ids'].pop()
        with self.assertRaises(ValueError):evidence.endpoint(e)
    def test_eog_suffix_rejected(self):
        e=endpoint();e['ids'][0]=128009;e['eog'][0]=True
        with self.assertRaises(ValueError):evidence.endpoint(e)
    def test_synthetic_cannot_become_native(self):
        p=confirmation();out=evidence.summarize(p,records(p),sessions())
        self.assertEqual(len(out['invalid']),1008);self.assertIsNone(out['arms']['C_R_QH']['ratio'])
    def test_full_panel_calculation(self):
        p=confirmation();out=evidence.summarize(p,records(p),sessions(),True)
        self.assertTrue(out['complete']);self.assertAlmostEqual(out['arms']['C_R_QH']['ratio'],100/95)
        self.assertEqual(len(out['arms']['C_R_QH']['strata']),6)
        self.assertTrue(all(v['matching_pairs']==12 for v in out['arms']['C_R_QH']['strata'].values()))
    def test_mismatch_not_fast_subset(self):
        p=confirmation();rs=records(p)
        for s,r in zip(p['slots'],rs):
            if s['task']==p['slots'][0]['task'] and s['arm']=='C_R_QH':r['endpoint']=endpoint(32);r['wall_ms']=1.
        out=evidence.summarize(p,rs,sessions(),True)
        self.assertIsNone(out['arms']['C_R_QH']['ratio']);self.assertTrue(out['arms']['C_R_PQ']['qualified'])
    def test_missing_slot_withholds_aggregate(self):
        p=confirmation();out=evidence.summarize(p,records(p)[:-1],sessions(),True)
        self.assertIsNone(out['arms']['C_R_QH']['ratio']);self.assertEqual(len(out['missing']),1)
    def test_time_gate_and_failed_slot(self):
        p=confirmation();rs=records(p);rs[0]['status']='FAILED'
        out=evidence.summarize(p,rs,sessions(),True);self.assertFalse(out['complete']);self.assertEqual(len(out['failed']),1)
        self.assertFalse(evidence.time_gate(sessions()[:2]))
    def test_process_link_and_runtime_role(self):
        p=confirmation();rs=records(p);rs[0]['lifecycle_id']='different'
        self.assertTrue(evidence.summarize(p,rs,sessions(),True)['process_link_errors'])
        rs=records(p);i=next(i for i,s in enumerate(p['slots']) if s['arm']=='R');rs[i]['runtime_role']='candidate'
        self.assertTrue(evidence.summarize(p,rs,sessions(),True)['invalid'])
    def test_float_files_signed_zero(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a';b=Path(d)/'b';a.write_bytes(struct.pack('<ff',0.,1.));b.write_bytes(struct.pack('<ff',-0.,1.))
            out=evidence.compare_f32(a,b);self.assertFalse(out['bitwise_equal']);self.assertEqual(out['max_ulp_finite'],0)
    def test_cross_zero_ulp(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a';b=Path(d)/'b'
            a.write_bytes(struct.pack('<I',0x80000001));b.write_bytes(struct.pack('<I',1))
            self.assertEqual(evidence.compare_f32(a,b)['max_ulp_finite'],2)
    def test_float_files_truncated_reject(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a';b=Path(d)/'b';a.write_bytes(b'1');b.write_bytes(b'1')
            with self.assertRaises(ValueError):evidence.compare_f32(a,b)
    def test_ledger_no_restart_or_retry(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'log';l=Ledger(p,['a'],100);l.begin('a');l.finish('FAILED')
            with self.assertRaises(ValueError):l.begin('a')
            l.close()
            with self.assertRaises(FileExistsError):Ledger(p,['a'],100)
    def test_json_no_duplicates_or_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x';p.write_text('{"a":1,"a":2}')
            with self.assertRaises(ValueError):core.read(p)
            with self.assertRaises(FileExistsError):core.write_new(p,{})

if __name__=='__main__':unittest.main(verbosity=2)
