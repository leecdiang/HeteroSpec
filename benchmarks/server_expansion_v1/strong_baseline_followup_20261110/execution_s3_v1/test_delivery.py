"""Synthetic partial-stage archive fixture; complete accounting never refunded."""
import json
from pathlib import Path
import tempfile
import unittest
import test_ledger
from support import fresh
import deliver


class Delivery(unittest.TestCase):
    def test_partial_bytes_prefix_failure_cost_and_privacy(self):
        with tempfile.TemporaryDirectory()as directory:
            root=Path(directory);ledger,prefix=test_ledger.Prefix().fixture(root)
            ledger.event('RESERVE','s3-failed',11);ledger.event('START','s3-failed');ledger.event('FAILED','s3-failed')
            work=root/'execution';work.mkdir()
            fresh(work/'STATE.json',dict(status='S3_PARTIAL_STOPPED',reason='SYNTHETIC CPU fixture'))
            fresh(work/'CONTROLLER_CLOSED.private.json',dict(synthetic=True))
            (work/'fixture.f32').write_bytes(b'withheld synthetic bytes')
            (work/'RESOURCE_GUARD.private.jsonl').write_text('Unrelated synthetic resource data '+'.'.join(['192','168','1','2'])+'\n')
            fresh(root/'MANIFEST.json',dict(SYNTHETIC=True));fresh(root/'ROOTS.json',dict(inputs=[]))
            c=dict(execution_root=str(work),study_root=str(root),manifest=str(root/'MANIFEST.json'),roots=str(root/'ROOTS.json'),
                inheritance=ledger.inherited,budget_approval=ledger.approval,ledger=str(ledger.path))
            fresh(root/'CONFIG.json',c)
            meta=deliver.export(root/'CONFIG.json',root/'public')
            result=deliver.replay(root/'public.tar.gz',meta['archive_sha256'],root/'replay')
            self.assertEqual(result['statistical_replay'],'PARTIAL_NO_COMPLETE_PANEL_ESTIMATE')
            self.assertEqual(result['cumulative_accounting']['requests'],516)
            self.assertEqual(result['cumulative_accounting']['phase_requests'],1)
            self.assertFalse((root/'replay/data/fixture.f32').exists())
            self.assertFalse((root/'replay/data/RESOURCE_GUARD.private.jsonl').exists())
            self.assertEqual(result['unavailable_numeric_payloads'],1)
            with self.assertRaisesRegex(ValueError,'Fresh terminal export'):
                deliver.export(root/'CONFIG.json',root/'public')


if __name__=='__main__':unittest.main()
