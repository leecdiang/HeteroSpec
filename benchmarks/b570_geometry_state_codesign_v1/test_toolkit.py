"""Synthetic-only regression suite. Does not import model code or start native workers."""
import copy
from collections import Counter
import json
import math
import tempfile
import unittest
from pathlib import Path
import protocol as p
import contracts as c
import analysis as a
import policy
import architecture as ar

HASH='a'*64

def case(i,domain='math',n=90,ident=None):
    return {'id':ident or f'SYNTHETIC/{domain}/{i}', 'domain':domain,
            'prompt_ids':[1000+i]+[5]*(n-1),'tokenizer_sha256':HASH,
            'template_sha256':'b'*64,'source_sha256':'c'*64}

def panel():
    return [case(100*d+10*b+i,domain,n) for d,domain in enumerate(p.DOMAINS)
            for b,n in enumerate((90,160,300)) for i in range(4)]

def selection():
    return p.select_holdout(panel(),{'ids':[],'prompt_sha256':[],'scope_manifest_sha256':HASH,'review_complete':True})

def confirm():
    sel=selection();return p.build_plan(sel['panel'],'confirm',selection=sel)

def pilot():
    return p.build_plan([case(i,n=160+i,ident=ident) for i,ident in enumerate(p.SENTINELS)],'pilot')

def endpoint(token=31):
    return {'ids':[token]*128,'eog':[False]*128,'length':128,'terminal_id':token,'stop_reason':'CAP','cap':128}

def record(slot):
    spec=slot['request']['recipe']['draft'];hist={'2':64} if spec else {'1':127}
    return {'evidence_origin':'SYNTHETIC_TEST_ONLY','status':'COMPLETED','slot':slot['slot'],
      'request_sha256':slot['request_sha256'],'normalized_sent_request':copy.deepcopy(slot['request']),
      'runtime_manifest_sha256':HASH,'runtime_role':slot['request']['recipe']['runtime'],
      'pid':2000,'lifecycle_id':slot['process_group'],'process_group':slot['process_group'],
      'mode':slot['mode'],'warmup':slot['warmup'],
      'observation':dict(heavy_capture=slot['mode']=='diagnostic',added_sync=False,api_dump=False,gpu_queries=False),
      'external_state_imports':0,'teacher_forced_tokens':0,'phase_recipe':slot['request']['recipe'],
      'target_prefill_micrograph_widths':slot['request']['producer_plan']['expected_micrograph_widths'] if slot['mode']=='diagnostic' else None,
      'target_prefill_width_hist':{str(k):v for k,v in Counter(slot['request']['producer_plan']['expected_micrograph_widths']).items()},
      'all_target_weights_offloaded':True,'no_draft_offload_violation':True,
      'request_begin_empty_state':True,'lifecycle_closed':True,'endpoint':endpoint(),
      'work':dict(target_continuation_width_hist=hist,target_continuation_graphs=sum(hist.values()),
                  target_continuation_rows=sum(int(k)*v for k,v in hist.items()),
                  target_continuation_callers=sum(hist.values()),draft_proposed_rows=64 if spec else 0,
                  draft_catchup_rows=63 if spec else 0,accepted_proposals=63 if spec else 0,rollback_calls=0),
      'request_wall_ms':100. if slot['arm']=='R' else 90.,
      'timer_contract':'RESIDENT_RESET_PREFILL_DECODE_RECONCILE_END_SYNC','raw_artifacts':[]}

def sessions():
    return [{'session':0,'start':0,'end':1000},{'session':1,'start':5000,'end':6000},
            {'session':2,'start':86400,'end':87400},{'session':3,'start':91400,'end':92400}]

class Toolkit(unittest.TestCase):
    def test_01_select_deterministic(self):
        exp={'ids':[],'prompt_sha256':[],'scope_manifest_sha256':HASH,'review_complete':True}
        self.assertEqual(p.select_holdout(panel(),exp),p.select_holdout(panel()[::-1],exp))
    def test_02_select_strata(self):
        s=selection();self.assertEqual(len(s['panel']),24)
        self.assertEqual({c['domain'] for c in s['panel']},{'code','math'})
    def test_03_exposed_id_rejected_if_shortage(self):
        e={'ids':[panel()[0]['id']],'prompt_sha256':[],'scope_manifest_sha256':HASH,'review_complete':True}
        with self.assertRaises(ValueError):p.select_holdout(panel(),e)
    def test_04_exposed_hash_rejected(self):
        e={'ids':[],'prompt_sha256':[p.prompt_hash(panel()[0]['prompt_ids'])],'scope_manifest_sha256':HASH,'review_complete':True}
        with self.assertRaises(ValueError):p.select_holdout(panel(),e)
    def test_05_exposure_must_be_reviewed(self):
        with self.assertRaises(ValueError):p.select_holdout(panel(),{'ids':[],'prompt_sha256':[],'scope_manifest_sha256':HASH,'review_complete':False})
    def test_06_no_outcome_leak(self):
        c0=case(1);c0['latency']=2
        with self.assertRaises(ValueError):p.validate_case(c0)
    def test_07_bad_bool_token(self):
        c0=case(1);c0['prompt_ids'][0]=True
        with self.assertRaises(ValueError):p.validate_case(c0)
    def test_08_duplicate_inventory(self):
        with self.assertRaises(ValueError):p.select_holdout(panel()+[panel()[0]],{'ids':[],'prompt_sha256':[],'scope_manifest_sha256':HASH,'review_complete':True})
    def test_09_pilot_80_and_precedence(self):
        x=pilot();p.validate_plan(x);self.assertEqual(len(x['slots']),80)
        self.assertTrue(all(s['arm']=='R' for s in x['slots'][:8]))
        self.assertTrue(all(s['arm']=='R_SHADOW' for s in x['slots'][8:16]))
    def test_10_reshuffled_controls_blocked(self):
        x=pilot();x['slots'][0],x['slots'][-1]=x['slots'][-1],x['slots'][0]
        with self.assertRaises(ValueError):p.validate_plan(x)
    def test_11_confirmation_counts(self):
        x=confirm();p.validate_plan(x);self.assertEqual(len(x['slots']),1728)
        self.assertEqual(len({s['process_group'] for s in x['slots']}),864)
    def test_12_all_reference_on_old_runtime(self):
        x=confirm();self.assertTrue(all(s['request']['recipe']['runtime']=='old' for s in x['slots'] if s['arm']=='R'))
    def test_13_no_selection_receipt(self):
        with self.assertRaises(ValueError):p.build_plan(panel(),'confirm')
    def test_14_mutated_wire(self):
        x=pilot();x['slots'][20]['request']['producer_plan']['ubatch']=128
        with self.assertRaises(ValueError):p.validate_plan(x)
    def test_15_duplicate_slot(self):
        x=pilot();x['slots'][-1]=x['slots'][0]
        with self.assertRaises(ValueError):p.validate_plan(x)
    def test_16_partition_boundaries(self):
        self.assertEqual(p.plan_prefill(129,'reference128')['expected_micrograph_widths'],[128,1])
        self.assertEqual(p.plan_prefill(129,'bulk512')['expected_micrograph_widths'],[129])
    def test_17_unknown_producer(self):
        with self.assertRaises(ValueError):p.plan_prefill(129,'auto')
    def test_18_json_duplicate(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'x';f.write_text('{"x":1,"x":2}')
            with self.assertRaises(ValueError):p.read_json(f)
    def test_19_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'x';p.write_new(f,{})
            with self.assertRaises(FileExistsError):p.write_new(f,{})
    def test_20_endpoint_EOG(self):
        e={'ids':[1,128009],'eog':[False,True],'length':2,'terminal_id':128009,'stop_reason':'EOG','cap':128}
        self.assertEqual(c.validate_endpoint(e),e)
    def test_21_endpoint_cropped_rejected(self):
        e=endpoint();e['ids'].pop()
        with self.assertRaises(ValueError):c.validate_endpoint(e)
    def test_22_suffix_after_EOG_rejected(self):
        e=endpoint();e['ids'][0]=128009;e['eog'][0]=True
        with self.assertRaises(ValueError):c.validate_endpoint(e)
    def test_23_micrograph_not_dispatch(self):
        r=record(pilot()['slots'][-1]);x=c.physical_work(r['work'],r['endpoint'])
        self.assertNotIn('dispatches',x);self.assertEqual(x['mean_occupied_rows_per_graph'],2.)
    def test_24_work_conservation(self):
        r=record(pilot()['slots'][-1]);r['work']['target_continuation_rows']+=1
        with self.assertRaises(ValueError):c.physical_work(r['work'],r['endpoint'])
    def test_25_paid_capture_blocked(self):
        s=pilot()['slots'][0];r=record(s);r['observation']['gpu_queries']=True
        with self.assertRaises(ValueError):c.validate_record(s,r,HASH)
    def test_26_wrong_runtime_route(self):
        s=pilot()['slots'][0];r=record(s);r['runtime_role']='new'
        with self.assertRaises(ValueError):c.validate_record(s,r,HASH)
    def test_27_wrong_hash_correct_shape(self):
        s=pilot()['slots'][0];r=record(s);r['runtime_manifest_sha256']='f'*64
        with self.assertRaises(ValueError):c.validate_record(s,r,HASH)
    def test_28_no_donor_import(self):
        s=pilot()['slots'][0];r=record(s);r['external_state_imports']=1
        with self.assertRaises(ValueError):c.validate_record(s,r,HASH)
    def test_29_premature_time_gate(self):
        self.assertFalse(a.time_gate(sessions()[:3]));s=sessions();s[2]['start']=86000;self.assertFalse(a.time_gate(s))
    def test_30_complete_synthetic_analyze(self):
        x=confirm();out=a.analyze(x,[record(s) for s in x['slots']],sessions(),HASH,allow_synthetic=True)
        self.assertTrue(out['comparisons']['R/C_R_QB']['qualified'])
        self.assertAlmostEqual(out['comparisons']['R/C_R_QB']['geomean_ratio'],100/90)
        self.assertEqual(out['evidence_origin'],'SYNTHETIC_TEST_ONLY')
    def test_31_synthetic_not_native(self):
        x=confirm();out=a.analyze(x,[record(s) for s in x['slots']],sessions(),HASH)
        self.assertEqual(len(out['invalid_records']),1728);self.assertIsNone(out['arms']['C_R_QB']['geomean_ratio'])
    def test_32_mismatch_not_fast_subset(self):
        x=confirm();rs=[record(s) for s in x['slots']]
        for s,r in zip(x['slots'],rs):
            if s['arm']=='C_R_QB' and s['task']==x['panel'][0]['id']:r['endpoint']=endpoint(55);r['request_wall_ms']=1.
        out=a.analyze(x,rs,sessions(),HASH,allow_synthetic=True)
        self.assertFalse(out['arms']['C_R_QB']['qualified']);self.assertIsNone(out['comparisons']['R/C_R_QB']['geomean_ratio'])
        self.assertTrue(out['arms']['C_B_PQ']['qualified'])
    def test_33_missing_work_withholds(self):
        x=confirm();out=a.analyze(x,[record(s) for s in x['slots']][:-1],sessions(),HASH,allow_synthetic=True)
        self.assertEqual(len(out['missing_slots']),1);self.assertIsNone(out['arms']['C_R_QB']['geomean_ratio'])
    def test_34_failure_preserved(self):
        x=confirm();rs=[record(s) for s in x['slots']];rs[0]={'slot':x['slots'][0]['slot'],'status':'LOAD_FAILED'}
        out=a.analyze(x,rs,sessions(),HASH,allow_synthetic=True);self.assertEqual(len(out['failed_slots']),1)
    def test_35_pid_pair_wrong(self):
        x=confirm();rs=[record(s) for s in x['slots']];rs[0]['pid']=100
        out=a.analyze(x,rs,sessions(),HASH,allow_synthetic=True);self.assertEqual(len(out['process_link_errors']),1)
    def test_36_policy_no_outcome(self):
        f=dict(dtype='F16',flash_attention=False,streams=1,max_q=2,prompt_tokens=160,known_graph_path=True,state_origin='fresh_request')
        self.assertEqual(policy.route(f,True,'producer_guarded'),'C_R_QB')
        f['actual_output']='unallowed'
        with self.assertRaises(ValueError):policy.route(f,True,'producer_guarded')
    def test_37_live_KV_no_fake_fallback(self):
        f=dict(dtype='F16',flash_attention=False,streams=1,max_q=2,prompt_tokens=160,known_graph_path=True,state_origin='live_KV')
        with self.assertRaises(ValueError):policy.route(f,True,'always_reference')
    def test_38_pilot_no_speed_gate(self):
        x=dict(original_reference_stable=True,rebuilt_reference_matches=True,observer_controls_match=True,all_controls_provenance_valid=True,C_R_QB_sentinel_qualification=True,C_R_PQ_sentinel_qualification=True,C_R_QB_actual_multirow_witness=True,port_repair_cycles=1)
        self.assertTrue(policy.pilot_decision(x).startswith('PILOT_FEASIBLE'))
        x['C_R_QB_actual_multirow_witness']=False;self.assertEqual(policy.pilot_decision(x),'STOP_NO_BATCHING_LEVER')
    def test_39_shared_strong_baseline(self):
        x=ar.reuse_opportunity(2,4096,2);self.assertEqual(x['candidate_vs_strong_shared_baseline_ratio'],1)
        self.assertIn('NOT_MEASURED',x['scope'])
    def test_40_amdahl_assumed(self):
        x=ar.amdahl_sensitivity(.2,2);self.assertAlmostEqual(x['whole_request_speedup_if_assumptions_hold'],1/.9)
        self.assertIn('NOT_HETEROSPEC',x['basis'])
    def test_41_arch_export_rejects_synthetic(self):
        with self.assertRaises(ValueError):ar.architecture_record(record(pilot()['slots'][-1]))
    def test_42_nonfinite_wall(self):
        s=pilot()['slots'][0];r=record(s);r['request_wall_ms']=float('nan')
        with self.assertRaises(ValueError):c.validate_record(s,r,HASH)
    def test_43_early_aggregate_withheld(self):
        x=confirm();out=a.analyze(x,[record(s) for s in x['slots']],sessions()[:3],HASH,allow_synthetic=True)
        self.assertIsNone(out['arms']['C_R_QB']['geomean_ratio'])
    def test_44_raw_escape(self):
        with tempfile.TemporaryDirectory() as d:
            arts=[{'role':r,'path':'../bad','bytes':0,'sha256':HASH} for r in ('request','result','identity','lifecycle')]
            with self.assertRaises(ValueError):c.verify_artifacts(Path(d),arts)

    def test_45_counts_histogram_is_not_ordered_trace(self):
        s=pilot()['slots'][0];r=record(s);self.assertIsNone(r['target_prefill_micrograph_widths'])
        c.validate_record(s,r,HASH)
    def test_46_diagnostic_order_required(self):
        s=next(s for s in pilot()['slots'] if s['mode']=='diagnostic');r=record(s);r['target_prefill_micrograph_widths']=None
        with self.assertRaises(ValueError):c.validate_record(s,r,HASH)

if __name__=='__main__':unittest.main(verbosity=2)
