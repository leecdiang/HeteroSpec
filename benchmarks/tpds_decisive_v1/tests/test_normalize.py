import copy,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from common import *
from normalize import trace_from_row,reference_jobs
from merge_references import merge
from test_capture import fixture

class NormalizeTests(unittest.TestCase):
    def test_rtx_endpoint_reconstructed(self):
        r={'ids':[3,4,7],'stop_reason':'EOG','study_cap':128,'draft_enabled':True,'k':3,
           'cycles':[{'base':2,'seed':3,'proposals':[4,5,6],'decisions':[4,7,6,0],'accepted':1}]}
        t,d=trace_from_row(r,[1,2],8,[7],'rtx');self.assertEqual(d['states'][-1]['prefix'],[1,2,3,4])
    def test_b570_correction(self):
        r={'endpoint':{'ids':[3,7],'stop_reason':'EOG'},'study_cap':128,'study_draft_enabled':True,
           'cycles':[{'base':2,'seed_id':3,'proposal':4,'decisions':[7,6],'accepted':0}]}
        t,d=trace_from_row(r,[1,2],8,[7],'b570');self.assertEqual(d['states'][-1]['unmaterialized_suffix'],[7])
    def test_endpoint_not_trusted(self):
        r={'ids':[3,4],'stop_reason':'CAP','study_cap':128,'draft_enabled':False,'k':0,'cycles':[]}
        with self.assertRaises(Invalid):trace_from_row(r,[1,2],8,[7],'rtx')
    def test_reference_maximal_no_values_in_job(self):
        with tempfile.TemporaryDirectory() as d:
            ps=fixture(Path(d));j=reference_jobs([ps[0]],{'caller_lengths':[2],'last_output_flags':[True]})
            self.assertEqual(j['request_reservation'],1)
            self.assertEqual(j['jobs'][0]['forced_suffix'],[3,4])
            self.assertNotIn('tokens',j['free_reference_job']);self.assertNotIn('forced_suffix',j['free_reference_job'])
    def test_reference_producer_mask_required(self):
        with tempfile.TemporaryDirectory() as d:
            ps=fixture(Path(d))
            with self.assertRaises(Invalid):reference_jobs([ps[0]],{'caller_lengths':[2],'last_output_flags':[]})
    def test_merge_single_path(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);ps=fixture(root);obj=read(ps[2]);obj['role']='forced_reference_path';ps[2].unlink();write_new(ps[2],obj)
            out=merge([ps[2]],root/'bank');self.assertEqual(len(out['prefixes']),3)
    def test_merge_duplicate_invocation(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);ps=fixture(root);obj=read(ps[2]);obj['role']='forced_reference_path';ps[2].unlink();write_new(ps[2],obj)
            with self.assertRaises(Invalid):merge([ps[2],ps[2]],root/'bank')

if __name__=='__main__':unittest.main()
