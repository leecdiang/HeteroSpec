"""Synthetic rejection checks, not experimental evidence."""
import copy
import itertools
import unittest
from rtx_pr91_crossaudit import ARMS,FAMILIES,paired_analysis,signature,count_check

def records():
    rows=[]
    for f,d,t,s,j,a in itertools.product(FAMILIES,['MBPP','GSM8K'],range(12),range(2),range(5),ARMS):
        rows.append(dict(family=f,task=f'{d}/{t}',session=s,round=j,condition=a,
            phase='formal',status='COMPLETED',warmup=False,measurement_mode='counts',
            observation=dict(phase_timers=False,heavy_capture=False,etw=False,added_sync=False),
            wall_ms=2 if a=='C3' else 1,input_sha256=f'{f}/{d}/{t}',
            output=dict(ids=[3]*128,eog_flags=[False]*128,length=128,terminal_id=3,
                        stop_reason='CAP',cached_tokens=0,truncated=False)))
    return rows

class AuditTests(unittest.TestCase):
    def test_complete_and_cost_direction(self):
        r=paired_analysis(records(),{f:{9} for f in FAMILIES})
        p=next(p for p in r['Qwen']['pairs'] if p['pair']=='M3/C3')
        self.assertTrue(p['complete_pairwise_equal']);self.assertEqual(p['cost_ratio'],.5)
        self.assertEqual(len(p['regressions']),24)
    def test_suffix_not_just_first_difference(self):
        rr=records()
        for r in rr:
            if r['family']=='Qwen' and r['task']=='MBPP/0' and r['condition'] in ['M3','C3']:
                r['output']['ids'][40]=4
                if r['condition']=='C3':r['output']['ids'][90]=5
        q=paired_analysis(rr,{f:{9} for f in FAMILIES})
        p=next(p for p in q['Qwen']['pairs'] if p['pair']=='M3/C3')
        self.assertEqual(p['matched_requests'],230)
        self.assertEqual(p['mismatches'][0]['differences'][0]['first_difference']['index'],90)
    def test_missing_duplicate(self):
        rr=records()
        for bad in [rr[:-1],rr[:-1]+[copy.deepcopy(rr[0])]]:
            with self.assertRaises(AssertionError):paired_analysis(bad,{f:{9} for f in FAMILIES})
    def test_eog_cannot_be_cropped_or_misflagged(self):
        r=records()[0];r['output']['ids'][30]=9
        with self.assertRaises(AssertionError):signature(r,{9})
        r['output']['eog_flags'][30]=True
        with self.assertRaises(AssertionError):signature(r,{9})
    def test_input_or_observer_drift(self):
        rr=records();rr[0]['input_sha256']='different'
        with self.assertRaises(AssertionError):paired_analysis(rr,{f:{9} for f in FAMILIES})
        rr=records();rr[0]['observation']['added_sync']=True
        with self.assertRaises(AssertionError):paired_analysis(rr,{f:{9} for f in FAMILIES})

if __name__=='__main__':unittest.main()
