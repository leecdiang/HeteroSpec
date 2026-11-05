import copy,hashlib,json,math,os,sqlite3,struct,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from common import *
from design import *
from trace import reconstruct
from analyze import analyze,threshold
from active_kv import parse
from runner import Ledger,admission_for_phase
from readiness import evaluate
from stage_sources import b570_draft,observe_b570,rtx_draft

H='a'*64

def rows(count=40):
    return [{'root_id':f'root-{i}','id':f'path-{i}','tokens':64+i,'native_tokenized':True,'admitted':True} for i in range(count)]
def panel():return select(rows(),set())

def ordinary_trace():
    return {'prompt_ids':[1,2],'cap':3,'vocab':8,'eog_ids':[7],'k':0,'initial':3,
      'steps':[{'kind':'ordinary','base':2,'seed':3,'decision':4},{'kind':'ordinary','base':3,'seed':4,'decision':5}]}

def spec_trace(kind='bonus',cap=5):
    ps=[4,5,6];ds=[4,5,6,7]
    if kind=='j1':ds=[4,7,6,1]
    if kind=='j0':ds=[7,5,6,1]
    return {'prompt_ids':[1,2],'cap':cap,'vocab':8,'eog_ids':[7],'k':3,'initial':3,
            'steps':[{'kind':'verify','base':2,'seed':3,'proposals':ps,'decisions':ds}]}

def record(panel,lane):
    ss=schedule(panel,lane)
    return {'lane':lane,'panel_sha256':digest(panel),'frozen_before_test':True,
        'qualification_status':'FINITE_NATIVE_CAPTURE_MATCH','source_freeze_sha256':H,'numeric_profile_sha256':H,
        'records':[{**j,'service_s':1+ss['arms'].index(j['arm'])*.1+(int(j['root_id'].split('-')[1])%3)*.02,
          'source_freeze_sha256':H,'numeric_profile_sha256':H,'status':'COMPLETE','endpoint_equal':True,
          'endpoint_sha256':digest(j['root_id']),'fallback_count':0} for j in ss['slots']]}

class DesignTests(unittest.TestCase):
    def test_root_leakage(self):
        p=panel();self.assertFalse(set(x['root_id'] for x in p['development'])&set(x['root_id'] for x in p['test']))
    def test_deterministic(self):self.assertEqual(panel(),select(list(reversed(rows())),set()))
    def test_exclusions(self):self.assertNotIn('root-1',[r['root_id'] for r in select(rows(),{'root-1'})['test']])
    def test_outcomes_forbidden(self):
        r=rows();r[0]['seconds']=1
        with self.assertRaises(Invalid):select(r,set())
    def test_insufficient(self):
        with self.assertRaises(Invalid):select(rows(10),set())
    def test_duplicate_id(self):
        r=rows();r.append(r[0])
        with self.assertRaises(Invalid):select(r,set())
    def test_three_schedules(self):
        p=panel()
        for lane,count in [('rtx-operator',216),('rtx-draft',192),('b570-draft',300)]:
            s=schedule(p,lane);self.assertEqual(s['measurement_count'],count)
            self.assertEqual(len({x['slot'] for x in s['slots']}),2*count)
    def test_position_balance(self):
        from collections import Counter
        p=panel()
        for lane in ARMS:
            s=schedule(p,lane);c=Counter((r['root_id'],r['arm'],r['period']) for r in s['slots'] if r['kind']=='measure')
            self.assertEqual(len(set(c.values())),1)
    def test_odd_roots_refused(self):
        p=panel();p['test']=p['test'][:-1]
        with self.assertRaises(Invalid):schedule(p,'b570-draft')
    def test_roster_exclusion(self):
        p=panel();p['arms_by_lane']={'b570-draft':['M','C1U1','C4U1','C4U2']}
        p.update(eligibility_decision_pretest=True,excluded_arm_reasons={'C4U4':'CAPACITY'})
        self.assertEqual(schedule(p,'b570-draft')['sessions'],4)
    def test_no_slow_exclusion(self):
        p=panel();p['arms_by_lane']={'b570-draft':['M','C1U1','C4U1','C4U2']}
        p.update(eligibility_decision_pretest=True,excluded_arm_reasons={'C4U4':'SLOW'})
        with self.assertRaises(Invalid):schedule(p,'b570-draft')
    def test_chunks(self):
        for n in range(1,1025):
            for width in (1,2,4):self.assertEqual(sum(caller_chunks(n,width)),n)

class TraceTests(unittest.TestCase):
    def test_ordinary(self):
        r=reconstruct(ordinary_trace());self.assertEqual(r['tokens'],[3,4,5]);self.assertEqual(r['states'][-1]['unmaterialized_suffix'],[5])
    def test_initial_cap(self):
        t=ordinary_trace();t['cap']=1;t['steps']=[]
        r=reconstruct(t);self.assertEqual(r['states'][0]['prefix'],[1,2]);self.assertIsNone(r['states'][0]['next_pending'])
    def test_bonus(self):self.assertEqual(reconstruct(spec_trace())['tokens'],[3,4,5,6,7])
    def test_j1(self):
        r=reconstruct(spec_trace('j1'));self.assertEqual(r['tokens'],[3,4,7]);self.assertEqual(r['states'][-1]['prefix'],[1,2,3,4]);self.assertEqual(r['states'][-1]['branch'],'correction')
    def test_j0(self):self.assertEqual(reconstruct(spec_trace('j0'))['tokens'],[3,7])
    def test_accepted_cap(self):
        r=reconstruct(spec_trace(cap=2));self.assertEqual(r['states'][-1]['prefix'],[1,2,3,4]);self.assertEqual(r['states'][-1]['unmaterialized_suffix'],[])
    def test_extra_step(self):
        t=spec_trace();t['steps']*=2
        with self.assertRaises(Invalid):reconstruct(t)
    def test_stop_too_soon(self):
        t=ordinary_trace();t['steps']=[]
        with self.assertRaises(Invalid):reconstruct(t)
    def test_wrong_seed(self):
        t=ordinary_trace();t['steps'][0]['seed']=5
        with self.assertRaises(Invalid):reconstruct(t)
    def test_false_accepted(self):
        t=spec_trace();t['steps'][0]['accepted']=0
        with self.assertRaises(Invalid):reconstruct(t)

class AnalysisTests(unittest.TestCase):
    def test_complete(self):
        p=panel();r=analyze(p,'rtx-operator',record(p,'rtx-operator'),100)
        self.assertEqual(r['independent_roots'],12);self.assertEqual(len(r['contrasts']),3)
    def test_primary(self):
        p=panel();r=analyze(p,'rtx-draft',record(p,'rtx-draft'),100);self.assertEqual(r['primary'],'total_service_ratio')
    def test_missing(self):
        p=panel();r=record(p,'rtx-draft');r['records'].pop()
        with self.assertRaises(Invalid):analyze(p,'rtx-draft',r,100)
    def test_duplicate(self):
        p=panel();r=record(p,'rtx-draft');r['records'][-1]=r['records'][0]
        with self.assertRaises(Invalid):analyze(p,'rtx-draft',r,100)
    def test_output_disagreement(self):
        p=panel();r=record(p,'rtx-draft');r['records'][0]['endpoint_sha256']='b'*64
        with self.assertRaises(Invalid):analyze(p,'rtx-draft',r,100)
    def test_failure_not_dropped(self):
        p=panel();r=record(p,'rtx-draft');r['records'][2]['status']='FAILED'
        with self.assertRaises(Invalid):analyze(p,'rtx-draft',r,100)
    def test_nonfinite(self):
        p=panel();r=record(p,'rtx-draft');r['records'][0]['service_s']=float('nan')
        with self.assertRaises(Invalid):analyze(p,'rtx-draft',r,100)
    def test_threshold(self):self.assertAlmostEqual(threshold(10,2,9),2)
    def test_no_headroom(self):self.assertIsNone(threshold(10,1,8))

class BridgeEntryTests(unittest.TestCase):
    def test_bridge_not_circular(self):
        admission_for_phase('bridge',{'status':'HOST_READY_BRIDGE','original_assets_verified':True,'bounded_native_entry_reviewed':True})
    def test_bridge_cannot_time_main(self):
        with self.assertRaises(Invalid):admission_for_phase('main',{'status':'HOST_READY_BRIDGE','original_assets_verified':True,'bounded_native_entry_reviewed':True})
    def test_bridge_requires_assets(self):
        with self.assertRaises(Invalid):admission_for_phase('bridge',{'status':'HOST_READY_BRIDGE','original_assets_verified':False,'bounded_native_entry_reviewed':True})
    def test_development_requires_bridge(self):
        with self.assertRaises(Invalid):admission_for_phase('development',{'status':'HOST_READY_FINITE_STUDY','reference_bridge_passed':False})
    def test_main_requires_freeze(self):
        with self.assertRaises(Invalid):admission_for_phase('main',{'status':'HOST_READY_FINITE_STUDY','reference_bridge_passed':True,'frozen_before_test':False})

class LedgerTests(unittest.TestCase):
    def test_reservations_not_refunded(self):
        with tempfile.TemporaryDirectory() as d:
            q=Ledger(Path(d)/'ledger',dict(requests=2,token_rows=20,operators=0))
            try:
                q.reserve('a',dict(requests=2,token_rows=10,operators=0));q.finish('a','FAILED',1)
                with self.assertRaises(Invalid):q.reserve('b',dict(requests=1,token_rows=1,operators=0))
            finally:q.close()
    def test_duplicate_attempt(self):
        with tempfile.TemporaryDirectory() as d:
            q=Ledger(Path(d)/'ledger',dict(requests=10,token_rows=20,operators=0))
            try:
                q.reserve('a',dict(requests=1,token_rows=1,operators=0))
                with self.assertRaises(Invalid):q.reserve('a',dict(requests=1,token_rows=1,operators=0))
            finally:q.close()
    def test_budget_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'ledger';q=Ledger(p,dict(requests=2,token_rows=20,operators=0));q.close()
            with self.assertRaises(Invalid):Ledger(p,dict(requests=3,token_rows=20,operators=0))

class ReadinessTests(unittest.TestCase):
    def test_blocked_lane_independent(self):
        good={x:True for x in ('old_reference_available','old_reference_stable','observer_bridge_passed','actual_native_build_passed','resource_admission_passed','module_inventory_recorded','numerical_qualification_passed','backend_loop4_executed')}
        good.update({x:H for x in ('reference_identity_sha256','source_freeze_sha256','implementation_sha256')})
        r=evaluate({'platform':'rtx','lanes':{'operator':good,'draft':{}}})
        self.assertEqual(r['lanes']['operator']['status'],'READY_FOR_FROZEN_CONFIRMATION');self.assertEqual(r['lanes']['draft']['status'],'DEVELOPMENT_ONLY')

if __name__=='__main__':unittest.main()
