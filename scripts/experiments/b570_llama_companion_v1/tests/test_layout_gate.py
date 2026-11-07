import sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import audit,design

class LayoutGateTests(unittest.TestCase):
    def test_equal_tokens_cannot_hide_pq_qb_full_vector_difference(self):
        candidates=[];oracles=[]
        for arm in design.ARMS:
            for obs in ('off','heavy'):
                candidates.append({'record':{'input_id':'x','slot':{'arm':arm,'observer':obs},'cycles':[]},'endpoint':{'ids':[1]},'vectors':{'full':'different' if arm=='C_QB' else 'same'}})
        for obs in ('off','heavy'):
            oracles.append({'record':{'input_id':'x','slot':{'arm':'R','observer':obs},'cycles':[]},'endpoint':{'ids':[1]},'vectors':{'full':'same'}})
        with patch.object(audit,'record',side_effect=lambda x,**kw:x):
            result=audit.matrix(candidates,oracles,['x'])
        self.assertFalse(result['pure_layout_correspondence'])
        self.assertFalse(result['all_reference_equal'])
        self.assertEqual(result['status'],'REFERENCE_OR_CONTROL_FAILURE')

if __name__=='__main__':unittest.main()
