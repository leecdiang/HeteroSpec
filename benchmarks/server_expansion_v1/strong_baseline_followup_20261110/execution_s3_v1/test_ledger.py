"""Synthetic predecessor-prefix and failure-accounting checks, zero GPU."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from ledger import Ledger,canonical,sha


class Prefix(unittest.TestCase):
    def fixture(self,root):
        inherited=root/'old.jsonl';inherited.write_text('old historical accounting\n')
        anchor=dict(ledger_path=str(inherited),ledger_sha256=sha(inherited),requests=514,reserved_rows=1000)
        previous=dict(scope='S1+S2',status='EXPLICITLY_APPROVED',request_ceiling=516,row_ceiling=2000000,incremental_request_ceiling=2)
        journal=root/'same-global.jsonl';parent='0'*64;events=[]
        for kind in ('RESERVE','START','FAILED'):
            e=dict(kind=kind,operation_id='old-failed',parent_sha256=parent,inheritance_sha256=anchor['ledger_sha256'],approval_sha256=hashlib.sha256(canonical(previous)).hexdigest())
            if kind=='RESERVE':e['reserved_rows']=10
            e['event_sha256']=hashlib.sha256(canonical(e)).hexdigest();parent=e['event_sha256'];events.append(e)
        journal.write_bytes(b''.join(canonical(x)+b'\n'for x in events));prefix=root/'prefix.jsonl';prefix.write_bytes(journal.read_bytes())
        anchor['approval_prefix_path']=str(prefix)
        approval=dict(scope='S3',status='EXPLICITLY_APPROVED',request_ceiling=517,row_ceiling=2000000,incremental_request_ceiling=3,
             phase_request_ceiling=2,predecessor_prefix_bytes=prefix.stat().st_size,
             predecessor_prefix_sha256=sha(prefix),predecessor_approval=previous,predecessor_requests=515,operation_prefix='s3-')
        return Ledger(journal,anchor,approval),prefix

    def test_same_chain_keeps_failed_cost(self):
        with tempfile.TemporaryDirectory()as directory:
            ledger,prefix=self.fixture(Path(directory));before=prefix.read_bytes()
            for op in ('s3-one','s3-two'):
                ledger.event('RESERVE',op,11);ledger.event('START',op);ledger.event('COMPLETE',op)
            s=ledger.snapshot();self.assertEqual((s['requests'],s['phase_requests'],s['reserved_rows']),(517,2,1032))
            self.assertEqual(s['operations']['old-failed'],'FAILED')
            self.assertTrue(ledger.path.read_bytes().startswith(before))
            with self.assertRaisesRegex(ValueError,'Insufficient'):ledger.event('RESERVE','s3-three',1)

    def test_new_directory_cannot_reset(self):
        with tempfile.TemporaryDirectory()as directory:
            ledger,prefix=self.fixture(Path(directory));ledger.path=Path(directory)/'new-ledger.jsonl'
            with self.assertRaisesRegex(ValueError,'prefix'):ledger.snapshot()

    def test_changed_prefix_or_authority_rejected(self):
        for change in ('bytes','approval'):
            with tempfile.TemporaryDirectory()as directory:
                ledger,prefix=self.fixture(Path(directory))
                if change=='bytes':prefix.write_bytes(prefix.read_bytes()+b'\n')
                else:ledger.approval['predecessor_approval']['request_ceiling']+=1
                with self.assertRaises(ValueError):ledger.snapshot()

    def test_duplicate_and_historical_transition_rejected(self):
        with tempfile.TemporaryDirectory()as directory:
            ledger,prefix=self.fixture(Path(directory))
            with self.assertRaises(ValueError):ledger.event('COMPLETE','old-failed')
            ledger.event('RESERVE','s3-once',1)
            with self.assertRaisesRegex(ValueError,'Duplicate'):ledger.event('RESERVE','s3-once',1)


if __name__=='__main__':unittest.main()
