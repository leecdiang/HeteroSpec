"""Synthetic mutation checks; not scientific results."""
import copy
import unittest
from b570_pr92_pairwise import ARMS, pairwise

def fixture():
    rows=[]
    for d in ('MBPP','GSM8K'):
        for t in range(12):
            for s in range(2):
                for j in range(5):
                    for a in ARMS:
                        rows.append({'task':f'{d}/{t}','session':s,'round':j,'condition':a,
                            'phase':'formal','status':'COMPLETED','warmup':False,'family':'Llama',
                            'wall_ms':2 if a=='C_k1' else 1,'input_sha256':str(t),
                            'measurement_mode':'counts','observation':{'phase_timers':False,
                                'heavy_capture':False,'etw':False,'added_sync':False},
                            'output':{'ids':[3]*128,'eog_flags':[False]*128,'length':128,
                                'terminal_id':3,'stop_reason':'CAP','cached_tokens':0,'truncated':False}})
    return rows

class Tests(unittest.TestCase):
    def test_complete_pairwise_equality_and_negative_cost(self):
        r=pairwise(fixture());p=next(x for x in r['pairs'] if x['pair']=='M_match/C_k1')
        self.assertEqual(p['matched_requests'],240);self.assertEqual(p['diagnostic_cost_ratio'],0.5)
        self.assertEqual(p['negative_tasks'],24)
    def test_same_first_difference_does_not_imply_equal_suffix(self):
        rr=fixture()
        for r in rr:
            if r['task']=='GSM8K/0' and r['condition'] in ('R_prod','M_match','C_k1'):
                r['output']['ids'][47]=4
                if r['condition']=='C_k1':r['output']['ids'][90]=5
        a=pairwise(rr);p=next(x for x in a['pairs'] if x['pair']=='M_match/C_k1')
        self.assertFalse(p['complete_pairwise_equal']);self.assertEqual(p['matched_requests'],230)
        self.assertEqual(p['mismatches'][0]['differences'][0]['first_difference']['index'],90)
    def test_missing_or_duplicate_coordinate_is_rejected(self):
        rr=fixture()
        for bad in [rr[:-1],rr[:-1]+[copy.deepcopy(rr[0])]]:
            with self.assertRaises(AssertionError):pairwise(bad)
    def test_terminal_suffix_cannot_be_cropped(self):
        rr=fixture();rr[0]['output']['ids'][40]=128009;rr[0]['output']['eog_flags'][40]=True
        with self.assertRaises(AssertionError):pairwise(rr)
    def test_observer_drift_is_rejected(self):
        rr=fixture();rr[0]['observation']['phase_timers']=True
        with self.assertRaises(AssertionError):pairwise(rr)
    def test_input_identity_drift_is_rejected(self):
        rr=fixture();rr[0]['input_sha256']='other'
        with self.assertRaises(AssertionError):pairwise(rr)

if __name__=='__main__':unittest.main()
