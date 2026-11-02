"""Compact matrix auditing must preserve raw geometry validation and decisions."""
from pathlib import Path
import json,struct,tempfile,unittest
from test_companion import ordinary
import audit,common

class CompactAuditTests(unittest.TestCase):
    def test_compact_preserves_checks_and_original_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'record.json';root=p.with_suffix('');(root/'target').mkdir(parents=True)
            r=ordinary();r.update(ids=[4],eog=[True],length=1,terminal_id=4,stop_reason='EOG',geometry=[{'scheduler_backend':'Vulkan0','caller_ids':[1,2,3]}]);r['slot']['observer']='heavy'
            values=[0.]*common.VOCAB;values[4]=1.
            (root/'target/initial.f32').write_bytes(struct.pack('<'+'f'*common.VOCAB,*values));(root/'target_final.state').write_bytes(b'fixture')
            p.write_text(json.dumps(r),encoding='utf-8');before=p.read_bytes()
            full=audit.record(p);compact=audit.record(p,retain_geometry=False)
            self.assertIn('geometry',full['record']);self.assertNotIn('geometry',compact['record'])
            for key in ('endpoint','vectors','record_sha256'):self.assertEqual(full[key],compact[key])
            self.assertEqual(before,p.read_bytes())
            r['geometry'][0]['scheduler_backend']=None;p.write_text(json.dumps(r),encoding='utf-8')
            with self.assertRaises(ValueError):audit.record(p,retain_geometry=False)

if __name__=='__main__':unittest.main()
