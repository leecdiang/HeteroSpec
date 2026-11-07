"""Synthetic CPU fixtures only; no GPU observations or execution."""
import copy
import math
import unittest
from collections import Counter
from plan import make_plan, validate
from analyze import run


def receipts(p, stages=('confirm',)):
    rows=[]
    for t in p['tasks']:
        if t['stage'] not in stages:continue
        value={'PQ':180,'QB_A':100,'QB_B':100,'QH_C':120,
               'QB_permuted':150,'QH_permuted':170,'QB_compact':155,'QH_compact':155}[t['arm']]
        if t['graph_mode']=='ON':value*=.8
        rows.append(dict(task_id=t['task_id'],attempt_id='synthetic-'+t['task_id'],plan_sha256=p['plan_sha256'],
                         layout=t['layout'],graph_mode=t['graph_mode'],cost_view=t['cost_view'],
                         numerical_qualified=True,environment_qualified=True,mode_verified=True,
                         status='QUALIFIED',session_id=t['session'],measured_us=[value]*30,
                         host_sha256='1'*64,runtime_sha256='2'*64,policy_sha256='3'*64,
                         logical_input_sha256='4'*64,physical_input_sha256='5'*64,
                         reference_sha256='6'*64,mode_evidence_sha256='7'*64,audit_sha256='8'*64))
    return rows


class PlanTests(unittest.TestCase):
    def test_counts_and_determinism(self):
        p=make_plan();self.assertEqual(p,make_plan());self.assertTrue(validate(p))
        self.assertEqual(p['scientific_state'],'NOT_RUN')
        self.assertEqual(p['counts'],{'reference/core':{'hosts':44,'calls':44},
             'qualification/core':{'hosts':144,'calls':4896},'confirm/core':{'hosts':768,'calls':29184},
             'reference/optional':{'hosts':16,'calls':16},'producer_qualification/optional':{'hosts':32,'calls':1088},
             'producer/optional':{'hosts':128,'calls':4864}})
    def test_mode_order_balanced_in_each_cycle(self):
        p=make_plan()
        for c in p['cases']:
            for cycle in (0,1):
                rows=[t for t in p['tasks'] if t['stage']=='confirm' and t['case_id']==c['case_id'] and t['block']//4==cycle and t['position']==0]
                self.assertEqual(Counter((t['graph_mode'],t['mode_position']) for t in rows),
                                 Counter({('OFF',0):2,('OFF',1):2,('ON',0):2,('ON',1):2}))
    def test_fallback_and_optional_gates(self):
        p=make_plan('off-only');self.assertNotEqual(p['plan_sha256'],make_plan()['plan_sha256'])
        self.assertTrue(all(t['graph_mode']=='OFF' for t in p['tasks']))
        self.assertTrue(all('producer_decision' in t['requires'] for t in p['tasks'] if t['optional']))
        self.assertEqual(sum(v['hosts'] for k,v in p['counts'].items() if k.endswith('/core')),500)
    def test_identity_corruption(self):
        p=make_plan();p['cases'][0]['keys']=1
        with self.assertRaises(ValueError):validate(p)


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.p=make_plan();cls.rows=receipts(cls.p,('confirm','producer'))
    def result(self,rows=None):return run(self.p,self.rows if rows is None else rows,100)
    def geom(self,r,comparison='QB_A',mode='ON/OFF'):
        return next(x['summary'] for x in r['geometry_contrasts'] if x['stage']=='confirm' and x['geometry_id']=='q2-k256' and x['mode']==mode and x['comparison']==comparison)
    def test_full_panel_known_ratios(self):
        r=self.result();self.assertEqual(r['observed_hosts'],896)
        s=self.geom(r);self.assertAlmostEqual(s['ratio'],.8);self.assertEqual(s['blocks'],8);self.assertEqual(s['sessions'],2)
        self.assertAlmostEqual(self.geom(r,'AA','ON')['ratio'],1)
        self.assertAlmostEqual(self.geom(r,'QB_QH','OFF')['ratio'],100/120)
        self.assertTrue(all(abs(x['ratio_of_ratios']['ratio']-1)<1e-12 for x in r['factor_contrasts']))
        z=next(x['summary'] for x in r['geometry_contrasts'] if x['stage']=='producer' and x['comparison']=='QH_conversion')
        self.assertAlmostEqual(z['ratio'],155/170)
    def test_unverified_on_never_becomes_speedup(self):
        rows=copy.deepcopy(self.rows)
        for r in rows:
            if r['graph_mode']=='ON':r.update(status='MODE_UNVERIFIED',mode_verified=False)
        result=self.result(rows)
        self.assertFalse(any(x['mode']=='ON/OFF' for x in result['case_contrasts']))
    def test_qualified_unverified_rejected(self):
        rows=copy.deepcopy(self.rows);rows[0]['mode_verified']=False
        with self.assertRaises(ValueError):self.result(rows)
    def test_missing_value_not_complete_geometry(self):
        ids={t['task_id'] for t in self.p['tasks'] if t['case_id']=='q2-k256-v1'}
        r=self.result([x for x in self.rows if x['task_id'] not in ids])
        self.assertEqual(self.geom(r)['blocks'],0)
        self.assertTrue(any(x['status']=='UNSTARTED' for x in r['coverage']))
    def test_one_missing_arm_removes_pair_block(self):
        tids={t['task_id'] for t in self.p['tasks'] if t['stage']=='confirm' and t['case_id']=='q2-k256-v0' and t['graph_mode']=='ON' and t['block']==0 and t['arm']=='QB_B'}
        r=self.result([x for x in self.rows if x['task_id'] not in tids])
        self.assertEqual(self.geom(r)['blocks'],7)
    def test_duplicate_unknown_plan_layout(self):
        with self.assertRaises(ValueError):self.result(self.rows+[self.rows[0]])
        for key,value in [('task_id','fake'),('plan_sha256','0'*64),('layout','MQ'),('cost_view','kernel_time')]:
            rows=copy.deepcopy(self.rows);rows[0][key]=value
            with self.assertRaises(ValueError):self.result(rows)
    def test_invalid_samples(self):
        for value in (True,0,-1,float('nan'),float('inf')):
            rows=copy.deepcopy(self.rows);rows[0]['measured_us'][0]=value
            with self.assertRaises(ValueError):self.result(rows)
        rows=copy.deepcopy(self.rows);rows[0]['measured_us'].pop()
        with self.assertRaises(ValueError):self.result(rows)
    def test_mixed_identities(self):
        for key in ('runtime_sha256','host_sha256','policy_sha256','logical_input_sha256','reference_sha256','physical_input_sha256'):
            rows=copy.deepcopy(self.rows);rows[0][key]='a'*64
            with self.assertRaises(ValueError):self.result(rows)
    def test_session_scope(self):
        rows=copy.deepcopy(self.rows)
        for r in rows:r['session_id']='single'
        self.assertEqual(self.geom(self.result(rows))['sessions'],1)
        self.assertIn('single-session',self.geom(self.result(rows))['scope'])
    def test_same_qb_label_bias_retained(self):
        rows=copy.deepcopy(self.rows);tasks={t['task_id']:t for t in self.p['tasks']}
        for r in rows:
            if tasks[r['task_id']]['arm']=='QB_B':r['measured_us']=[x*1.2 for x in r['measured_us']]
        self.assertAlmostEqual(self.geom(self.result(rows),'AA','ON')['ratio'],1/1.2)
    def test_failed_attempt_without_final_hash(self):
        rows=copy.deepcopy(self.rows);rows[0].update(status='EXECUTION_FAILED',numerical_qualified=False,
                       mode_verified=False,measured_us=[],audit_sha256=None,failure_reason='synthetic crash')
        self.assertEqual(self.result(rows)['coverage'][0]['status'],'EXECUTION_FAILED')


if __name__=='__main__':unittest.main()
