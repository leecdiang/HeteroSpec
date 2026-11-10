"""Full128-operation artificial replay fixture; no native/GPU execution."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
import deliver
from execute import analyze,save


class Delivery(unittest.TestCase):
    def test_complete_text_roundtrip_and_tamper(self):
        with tempfile.TemporaryDirectory()as temporary:
            root=Path(temporary);work=root/'work';work.mkdir();source=root/'source';source.mkdir()
            save(work/'STATE.json',dict(status='B2_COMPLETE_REQUIRES_PUBLIC_ARCHIVE_REPLAY'))
            save(work/'LOCK_RELEASED.private.json',dict(closed=True))
            cells=[['loop4',248],['loop4',252],['packed',248],['packed',252]];workers=[];records=[];ledger=[]
            for core,pos in cells:
                for round_ in range(4):
                    worker=dict(id=f'{core}-{pos}-{round_}',core=core,boundary=pos,round=round_,job=f'jobs/{core}-{pos}-{round_}.json')
                    workers.append(worker);items=[];operations=[]
                    for i in range(8):
                        role='warm'if i<4 else'measured';execution='q4pair'if i%2==0 else'q8'
                        item=dict(name=f'{role}-{i}',execution=execution);items.append(item)
                        receipt=dict(operation_s=1 if execution=='q4pair'else.8,capture=False)
                        save(work/'runs'/worker['id']/'native'/item['name']/'receipt.json',receipt)
                        operations.append(dict(role=role,item=item,receipt=receipt))
                    save(work/worker['job'],dict(diagnostics=items))
                    record=dict(worker=worker,operations=operations,caller_s=10);records.append(record)
                    save(work/'checked'/(worker['id']+'.json'),record)
                    ledger.extend([dict(event='RESERVE',requests=8,rows=2064),dict(event='COMPLETE')])
            plan=dict(cells=cells,workers=workers);save(work/'PLAN.json',plan)
            save(work/'RESULTS.json',analyze(records,plan))
            (work/'ledger.jsonl').write_text(''.join(json.dumps(x)+'\n'for x in ledger))
            (work/'numeric.f32').write_bytes(b'not published')
            (work/'RESOURCE_GUARD.private.jsonl').write_text('private foreign info\n')
            archive_source=Path(os.environ.get('B2_ARCHIVE_SOURCE',str(Path(__file__).resolve().parents[1]/'execution_v1')))
            out=root/'public';meta=deliver.export(work,root,source,out,archive_source)
            result=deliver.replay(root/'public.tar.gz',meta['archive_sha256'],root/'replay',archive_source)
            self.assertEqual(result['statistical_replay'],'PASSED_COMPLETE_128_OPERATIONS')
            self.assertEqual(result['unavailable_numeric_payloads'],1)
            self.assertFalse((root/'replay/data/numeric.f32').exists())
            self.assertFalse((root/'replay/data/RESOURCE_GUARD.private.jsonl').exists())
            # Actual native receipt and checked record must agree; changed
            # archive payloads are rejected before restoring any destination.
            package=(root/'public.tar.gz').read_bytes();broken=root/'broken.tar.gz';broken.write_bytes(package[:-10])
            with self.assertRaisesRegex(ValueError,'Archive transport hash mismatch'):
                deliver.replay(broken,meta['archive_sha256'],root/'bad',archive_source)
            self.assertFalse((root/'bad').exists())


if __name__=='__main__':unittest.main()
