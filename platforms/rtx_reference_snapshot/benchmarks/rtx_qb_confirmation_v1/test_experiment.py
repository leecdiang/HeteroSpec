"""Synthetic scheduler/statistics/guard tests; never interpreted as GPU evidence."""
import copy
import math
from pathlib import Path
import struct
import tempfile
import unittest
from unittest import mock
import experiment as e


def panel():
    return {f:[dict(id=f't{i}', prompt_ids=[1,2,i], cap=128) for i in range(12)] for f in e.FAMILIES}


def dataset(ratio=1.04):
    p=panel(); plan=dict(panel=p, blocks=e.schedule(p), input_exposure='SYNTHETIC')
    items=[]
    for b in plan['blocks']:
        records=[]
        for task in b['tasks']:
            ms=100*ratio if b['arm'].endswith('_PQ') else 100
            records.append(dict(task=task,family=b['family'],condition=b['arm'],followup_block=b,
                                slot=b['id']+'|'+task,wall_ms=ms,contract_valid=True,workload_error=None,
                                runtime_identity_verified=True,measurement_mode='counts',warmup=False,
                                observation={k:False for k in ('phase_timers','heavy_capture','etw','added_sync')},
                                output=dict(ids=[1,99],eog_flags=[False,True],length=2,terminal_id=99,
                                            stop_reason='EOG',cached_tokens=0,truncated=False)))
        items.append(dict(status='COMPLETED',block=b,records=records))
    return plan,items


class ScheduleTests(unittest.TestCase):
    def test_budget_and_unique_blocks(self):
        rows=e.schedule(panel())
        self.assertEqual(len(rows),324)
        self.assertEqual(len({b['id'] for b in rows}),324)
        self.assertEqual(sum(len(b['tasks'])+1 for b in rows),1620)
        self.assertEqual(sum(len(b['tasks']) for b in rows if b['arm']!='R'),864)
        self.assertEqual(sum(len(b['tasks']) for b in rows if b['arm']=='R'),432)

    def test_every_task_has_paired_arms_and_two_references(self):
        rows=e.schedule(panel())
        for session in range(6):
            for family in e.FAMILIES:
                selected=[b for b in rows if b['session']==session and b['family']==family]
                self.assertEqual(selected[0]['arm'],'R');self.assertEqual(selected[-1]['arm'],'R')
                for task in (f't{i}' for i in range(12)):
                    arms=[b['arm'] for b in selected if task in b['tasks']]
                    self.assertEqual(sorted(arms),sorted(['R','R','M_PQ','M_QB','C_PQ','C_QB']))

    def test_order_balanced_within_each_session(self):
        rows=e.schedule(panel())
        for session in range(6):
            for family in e.FAMILIES:
                for path in e.PATHS:
                    a=[b for b in rows if b['session']==session and b['family']==family and b['arm'].startswith(path+'_')]
                    self.assertEqual(sum(a[i]['arm'].endswith('PQ') for i in range(0,8,2)),2)
                    for i in range(0,8,2):self.assertEqual(a[i]['tasks'],a[i+1]['tasks'])

    def test_deterministic_seed_and_no_panel_mutation(self):
        p=panel();before=copy.deepcopy(p)
        self.assertEqual(e.schedule(p),e.schedule(p))
        self.assertNotEqual(e.schedule(p),e.schedule(p,17))
        self.assertEqual(p,before)

    def test_invalid_panels_rejected(self):
        bad=[]
        p=panel();p.pop('Qwen');bad.append(p)
        p=panel();p['Qwen'].append(p['Qwen'][0]);bad.append(p)
        p=panel();p['Qwen'][0]['cap']=127;bad.append(p)
        p=panel();p['Qwen'][0]['prompt_ids']=[True];bad.append(p)
        for p in bad:
            with self.assertRaises(ValueError):e.schedule(p)

    def test_conditions(self):
        self.assertFalse(e.condition('R')['spec'])
        self.assertEqual(e.condition('C_QB')['maximum_k'],3)
        self.assertFalse(e.condition('M_PQ')['spec'])
        with self.assertRaises(ValueError):e.condition('M_GS')


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan,cls.items=dataset()

    def test_known_synthetic_effect(self):
        result=e.analyze_blocks(self.plan,self.items)
        self.assertEqual(len(result['comparisons']),6)
        for r in result['comparisons']:
            self.assertEqual(r['status'],'QUALIFIED_FINITE_PANEL')
            self.assertAlmostEqual(r['estimate']['speed_ratio_PQ_over_QB'],1.04)
            self.assertEqual(len(r['task_ratios']),72)
            self.assertEqual(r['task_regressions'],0)

    def test_negative_effect_retained(self):
        plan,items=dataset(.97)
        for r in e.analyze_blocks(plan,items)['comparisons']:
            self.assertAlmostEqual(r['estimate']['speed_ratio_PQ_over_QB'],.97)
            self.assertEqual(r['task_regressions'],72)

    def test_failure_not_silently_dropped(self):
        rows=copy.deepcopy(self.items);b=next(x for x in rows if x['block']['arm']=='M_PQ')
        family=b['block']['family'];b['status']='FAILED'
        r=next(r for r in e.analyze_blocks(self.plan,rows)['comparisons'] if r['family']==family and r['path']=='M')
        self.assertIsNone(r['estimate']);self.assertTrue(r['failed'])

    def test_missing_data_yields_no_interval(self):
        rows=self.items[:-1]
        result=e.analyze_blocks(self.plan,rows)
        self.assertTrue(any(r['estimate'] is None for r in result['comparisons']))

    def test_output_mismatch_disqualifies_not_speed_selected(self):
        rows=copy.deepcopy(self.items);b=next(x for x in rows if x['block']['arm']=='C_QB')
        family=b['block']['family'];b['records'][0]['output']['ids']=[2,99]
        r=next(r for r in e.analyze_blocks(self.plan,rows)['comparisons'] if r['family']==family and r['path']=='C')
        self.assertIsNone(r['estimate']);self.assertTrue(r['mismatches'])

    def test_duplicate_and_changed_blocks_rejected(self):
        with self.assertRaises(ValueError):e.analyze_blocks(self.plan,self.items+[self.items[0]])
        rows=copy.deepcopy(self.items);rows[0]['block']['tasks'].reverse()
        with self.assertRaises(ValueError):e.analyze_blocks(self.plan,rows)

    def test_observer_timing_not_admitted(self):
        rows=copy.deepcopy(self.items);b=next(x for x in rows if x['block']['arm']=='C_PQ')
        b['records'][0]['observation']['added_sync']=True
        result=e.analyze_blocks(self.plan,rows)
        self.assertTrue(any(r['estimate'] is None for r in result['comparisons']))

    def test_session_reversal_not_hidden(self):
        values=[math.log(x) for x in (.97,1.08,.98,1.07,.99,1.06)]
        r=e.contrast(values)
        self.assertLess(r['session_ratios'][0],1)
        self.assertGreater(r['session_ratios'][1],1)
        self.assertEqual(len(r['session_ratios']),6)

    def test_wrong_independent_sample_count(self):
        for xs in ([0]*5,[0]*7,[float('nan')]*6):
            with self.assertRaises(ValueError):e.contrast(xs)


class UtilityTests(unittest.TestCase):
    def test_quantile(self):
        self.assertEqual(e.quantile([0,10],.25),2.5)
        self.assertEqual(e.quantile([3],.975),3)

    def test_source_anchor_fail_closed(self):
        self.assertEqual(e.replace_once('hello a','a','b'),'hello b')
        for s in ('hello','a a'):
            with self.assertRaises(ValueError):e.replace_once(s,'a','b')

    def test_immutable_receipt(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'receipt.json';e.save(p,{'a':1})
            with self.assertRaises(FileExistsError):e.save(p,{'a':2})

    def test_strided_canonical_and_crop_rejection(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);(p/'x').write_bytes(struct.pack('<6f',1,2,0,3,4,0))
            m=dict(file='x',type=0,ne=[2,2,1,1],nb=[4,12,24,24])
            self.assertEqual(e.canonical(p,m),struct.pack('<4f',1,2,3,4))
            (p/'x').write_bytes(b'\0')
            with self.assertRaises(ValueError):e.canonical(p,m)

    def test_remote_freeze_rejection(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);e.save(p/'FREEZE.json',{'files':[]})
            with mock.patch.object(e.subprocess,'check_output',side_effect=[(p/'FREEZE.json').read_bytes(),b'wrong']):
                with self.assertRaises(ValueError):e.verify_freeze(p,p,'a'*40,'F0.json')


if __name__=='__main__':unittest.main(verbosity=2)
