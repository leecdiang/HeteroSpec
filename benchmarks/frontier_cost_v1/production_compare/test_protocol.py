"""Host-only rejection/accounting checks. No native binary or model is run."""
from copy import deepcopy
from array import array
import json
from pathlib import Path
import tempfile
import unittest
from protocol import VOCAB, actual_work, identity, make_plan, storage_ceiling, validate_inputs, write_new
from verify_production import logical_walk, safe, verify_directory, verify_job

HERE = Path(__file__).resolve().parent


class ProtocolChecks(unittest.TestCase):
    def setUp(self):
        self.inputs = json.loads((HERE/'INPUTS.json').read_text())

    def test_fixed_budget_api_and_physical_are_distinct(self):
        plan = make_plan(self.inputs)
        self.assertEqual(plan['work_ceiling'], {'requests':12,'cycles':180,
            'target_decode_calls':234,'draft_decode_calls':1452,
            'target_physical_microbatches':234,'draft_physical_microbatches':1848,
            'target_rows':3048,'draft_rows':3048})
        self.assertEqual(plan['context_creation_ceiling'],12)
        self.assertFalse(plan['performance_admitted'])

    def test_document_mutations_are_rejected(self):
        for modify in [lambda x:x['inputs'][0]['prompt_ids'].__setitem__(0,0),
                       lambda x:x['inputs'][0].__setitem__('cap',96),
                       lambda x:x['inputs'].reverse(),
                       lambda x:x.__setitem__('draft_sha256','0'*64)]:
            candidate=deepcopy(self.inputs);modify(candidate)
            with self.assertRaises(ValueError):validate_inputs(candidate)

    def test_literal_draft_prefill_accounting(self):
        # Arithmetic fixture only: P151, one rejected k7 cycle.
        receipt={'cycles':[{'accepted':0}],'target_calls':6,'draft_calls':9,
                 'draft_tail_skipped':0,'draft_tail_recovered':0,
                 'target_physical_width_hist':{'32':4,'23':1,'8':1},
                 'draft_physical_width_hist':{'4':37,'3':1,'1':8}}
        eager=actual_work(receipt,self.inputs['inputs'][0],0)
        self.assertEqual(eager['draft_decode_calls'],9)
        self.assertEqual(eager['draft_physical_microbatches'],46)
        receipt['draft_calls']=8;receipt['draft_tail_skipped']=1
        receipt['draft_physical_width_hist']['1']=7
        deferred=actual_work(receipt,self.inputs['inputs'][0],1)
        self.assertEqual(deferred['draft_physical_microbatches'],45)
        receipt['draft_calls']=45
        with self.assertRaises(ValueError):actual_work(receipt,self.inputs['inputs'][0],1)

    def test_bool_counter_is_not_an_integer_receipt(self):
        receipt={'cycles':[{'accepted':True}]}
        with self.assertRaises(ValueError):actual_work(receipt,self.inputs['inputs'][0],0)

    def test_storage_uses_real_model_structures(self):
        storage=storage_ceiling(self.inputs['inputs'])
        self.assertEqual(storage['requests'][0]['target_state_bytes_ceiling'],175*36*2048*2+1024**2)
        self.assertGreater(storage['all_capture_bytes_per_process'],storage['sidecar_bytes_per_process'])
        self.assertGreater(storage['minimum_free_disk_bytes'],2*storage['all_capture_bytes_per_process'])

    def test_unsafe_raw_paths(self):
        for name in ('../receipt.json','/tmp/receipt.json','a/../receipt.json'):
            with self.assertRaises(ValueError):safe(name)

    def test_error_and_timeout_cannot_become_a_capture_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);write_new(root/'JOB.json',{})
            for code,timed_out,reaped in [(2,False,True),(0,True,True),(0,False,False)]:
                record={'job_file':'JOB.json','job_identity':identity(root/'JOB.json'),
                        'process':{'returncode':code,'timed_out':timed_out,'child_reaped':reaped}}
                with self.assertRaises(ValueError):verify_job(root,record,{},self.inputs['inputs'])

    def test_arbitrary_pass_and_partial_plan_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);write_new(root/'INPUTS.json',self.inputs);write_new(root/'PLAN.json',make_plan(self.inputs))
            for status,completed in [('PASS',[]),('COMPLETE_PREPARATION_NOT_PERFORMANCE_ADMITTED',[{}]),
                                     ('COMPLETE_PREPARATION_NOT_PERFORMANCE_ADMITTED',[{},{}]),
                                     ('CAPTURE_COMPLETE_PENDING_COMPARISON',[{}]*6)]:
                path=root/'RUN.json'
                if path.exists():path.unlink()
                write_new(path,{'status':status,'completed':completed,'attempted_processes':len(completed),
                                'plan_identity':identity(root/'PLAN.json'),'inputs_identity':identity(root/'INPUTS.json')})
                with self.assertRaises(ValueError):verify_directory(root)

    def test_foreign_plan_and_extra_jobs_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);write_new(root/'INPUTS.json',self.inputs)
            plan=make_plan(self.inputs);plan['jobs'].append(deepcopy(plan['jobs'][0]))
            write_new(root/'PLAN.json',plan);write_new(root/'RUN.json',{})
            with self.assertRaises(ValueError):verify_directory(root)

    def test_original_terminal_has_two_files_not_worker_metadata(self):
        # Explicit host-only format fixture, not native model evidence.
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'target/state/initial').mkdir(parents=True);(root/'target/state/terminal').mkdir()
            values=array('f',[0.0])*VOCAB;values[151645]=1.0;data=values.tobytes()
            (root/'target/initial.f32').write_bytes(data)
            for name in ('initial','terminal'):
                (root/'target/state'/name/'frontier.f32').write_bytes(data)
                (root/'target/state'/name/'sequence.bin').write_bytes(b'host-format-fixture')
            (root/'target/state/initial/capture.txt').write_text('vocab=151936\nsequence_bytes=19\nposition_min=0\nposition_max=150\n')
            receipt={'ids':[151645],'eog':[True],'cycles':[],'length':1,'terminal_id':151645,'stop_reason':'EOG'}
            self.assertEqual(logical_walk(receipt,root,self.inputs['inputs'][0]),1)
            (root/'target/state/terminal/capture.txt').write_text('not an original terminal member')
            with self.assertRaises(ValueError):logical_walk(receipt,root,self.inputs['inputs'][0])


if __name__=='__main__':
    unittest.main(verbosity=2)
