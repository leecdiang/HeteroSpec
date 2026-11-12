"""Synthetic state-machine integration; mocked native execution, ZERO GPU.

Numerical comparators have their own strict tests and real qualification. This
fixture exercises complete210-worker order, oracle/qualification gates and
failure stopping, including actual complete-panel normalization/statistics.
"""
import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
import run
from plan import construct


def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value))


class Controller(unittest.TestCase):
    def simulate(self,temporary,fail_R=False):
        base=Path(temporary);root=base/'execution';root.mkdir();roots=dict(generated_outputs_seen=False,inputs=[
            dict(id=f'SYNTHETIC/{i}',slot=i,domain='code'if i<6 else'math',cap=128,prompt_ids=[1]*20)for i in range(12)])
        old=dict(services=[dict(id=f'old{i}',input=dict(id=f'SYNTHETIC-OLD/{i}',prompt_ids=[1],cap=2))for i in range(6)])
        plan,jobs=construct(roots,old,Path('/SYNTHETIC/model.gguf'))
        for relative,value in jobs.items():put(base/relative,value)
        for name,value in [('ROOTS.json',roots),('MANIFEST.json',plan),('OLD.json',old),('PROFILE.json',{}),
            ('B2.json',dict(statistical_replay='PASSED_COMPLETE_128_OPERATIONS'))]:put(base/name,value)
        (base/'global.jsonl').write_text('SYNTHETIC ledger; real hash-chain tested separately\n')
        put(root/'RESOURCE_GUARD_LATEST.private.json',dict(epoch=time.time(),events=[]))
        config=dict(execution_root=str(root),execution_phase='S3_QUAL',manifest=str(base/'MANIFEST.json'),
            state_profile=str(base/'PROFILE.json'),roots=str(base/'ROOTS.json'),B2_public_delivery_proof=str(base/'B2.json'),
            B2_public_delivery_proof_sha256=run.sha(base/'B2.json'),manifest_sha256=run.sha(base/'MANIFEST.json'),
            predecessor_manifest=str(base/'OLD.json'),old_R_native0=str(base/'old-native'),
            executables=dict(R=dict(path='SYNTHETIC_R',sha256='1'*64),guard=dict(path='SYNTHETIC_GUARD')),
            guard_script='SYNTHETIC_NO_EXEC',budget_approval=dict(request_ceiling=1812),
            phase_output_roots=dict(S3_QUAL=str(root/'S3_QUAL'),S3=str(root/'S3')),ledger=str(base/'global.jsonl'),
            allocation_end_utc='2099-01-01T00:00:00+00:00',fixed_worker_gap_s=3,archive_bound_s=3600,worker_timeout_s=900)
        put(root/'ADMISSION.private.json',config);calls=[];count=[0];native_ns=[1000000000000]
        class FakeLedger:
            def snapshot(self):return dict(requests=1373+count[0],reserved_rows=677712,events=[],operations={})
        class FakeHost:
            def __init__(self,path):
                self.c=run.read(path);self.root=Path(self.c['phase_output_roots'][self.c['execution_phase']]);self.root.mkdir(parents=True,exist_ok=True);self.ledger=FakeLedger()
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def run(self,worker,job,executable,phase):
                if executable=='model':
                    if phase=='S3_QUAL':
                        if count[0]<24:raise AssertionError('Candidate preceded all24R')
                        if not Path(self.c['new_root_oracles']).exists():raise AssertionError('No oracle freeze')
                    elif count[0]<135:raise AssertionError('Formal preceded complete qualification')
                calls.append(worker['worker_id']);count[0]+=len(worker['operations'])
                out=self.root/'workers'/worker['worker_id'];native=out/'native';native.mkdir(parents=True)
                put(out/'HOST.json',dict(caller_s=10))
                for item in job['inputs']:
                    native_ns[0]+=1000000
                    put(native/item['name']/'receipt.json',dict(semantic_tape_sha256='2'*64,S3_service=dict(elapsed_s=.01),
                        synthetic=True,absolute_fixture_ns=native_ns[0]))
                return out
        class FakeGuard:
            def poll(self):return None
            def wait(self,timeout):return 0
        def reference(*args):
            if fail_R:raise ValueError('SYNTHETIC independent R mismatch')
            return dict(SYNTHETIC_NUMERIC_STUB=True)
        def synthetic_row(worker,ordinal,directory,job,host):
            begin=run.read(directory/'receipt.json')['absolute_fixture_ns'];ids=[1,151645]
            return dict(operation_id=worker['operations'][ordinal]['operation_id'],worker_id=worker['worker_id'],arm=worker['arm'],
              slot=worker['slot'],block=worker['block'],ordinal=ordinal,role=job['inputs'][ordinal]['name'],phase='S3',unit='s',
              elapsed_s=.0001,start_ns=begin,end_ns=begin+100000,fence_ns=begin+100000,owned_ready_ns=begin+100000,
              q=2,output_rows=2,all_outputs_owned=True,callback_continues=True,input_sha256=hashlib.sha256(json.dumps(job['inputs'][ordinal]['input'],sort_keys=True).encode()).hexdigest(),
              config_sha256='3'*64,output_sha256='4'*64,tokens=ids,generated_tokens=2,stop_reason='eog')
        with patch.object(run,'Host',FakeHost),patch.object(run.subprocess,'Popen',return_value=FakeGuard()),\
             patch.object(run,'resource',return_value={}),patch.object(run,'repeated_R',side_effect=reference),\
             patch.object(run,'complete_bridge',return_value=dict(SYNTHETIC_NUMERIC_STUB=True)),\
             patch.object(run,'clean',return_value=dict(SYNTHETIC_NUMERIC_STUB=True)),\
             patch.object(run,'clock',side_effect=lambda r:r['S3_service']),patch.object(run,'row',side_effect=synthetic_row):
            if fail_R:
                with self.assertRaisesRegex(ValueError,'independent R mismatch'):run.execute(root/'ADMISSION.private.json')
            else:run.execute(root/'ADMISSION.private.json')
        return root,calls,count[0],plan

    def test_complete_order_and_automatic_gates(self):
        with tempfile.TemporaryDirectory()as temporary:
            root,calls,count,plan=self.simulate(temporary)
            self.assertEqual(calls,[x['worker_id']for x in plan['workers']]);self.assertEqual(count,423)
            self.assertEqual(run.read(root/'STATE.json')['status'],'S3_COMPLETE_REQUIRES_PUBLIC_ARCHIVE_REPLAY')
            self.assertEqual(len(run.read(root/'S3_ROWS.json')),288)
            self.assertEqual(run.read(root/'S3_ANALYSIS.json')['contrasts'][0]['ratio'],1)

    def test_reference_failure_never_reaches_candidate_or_formal(self):
        with tempfile.TemporaryDirectory()as temporary:
            root,calls,count,plan=self.simulate(temporary,True)
            self.assertEqual(count,2);self.assertEqual(len(calls),2)
            self.assertEqual(run.read(root/'STATE.json')['status'],'S3_PARTIAL_STOPPED')
            self.assertFalse((root/'S3_ROWS.json').exists());self.assertFalse((root/'ADMISSION_FORMAL_DERIVED.private.json').exists())


if __name__=='__main__':unittest.main()
