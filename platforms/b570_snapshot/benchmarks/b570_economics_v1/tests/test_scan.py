"""Tiny synthetic saved-metadata population; not original GPU evidence."""
import hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import costs
class ScanTests(unittest.TestCase):
 def fixture(self,p):
  panel=p/'PANEL.json';panel.write_text(json.dumps({'test':[{'id':'i','root_id':'r'}]}))
  records=[]
  for s in range(6):
   for arm in ('M','H1','C1U1','C4U1','C4U2','C4U4'):
    folder=p/'runs'/f'main-s{s}-r0-{arm}';folder.mkdir(parents=True)
    for j,kind in enumerate(('warmup','measure')):
     data=json.dumps({'service_ms':1000,'generation_ms':700,'whole_request_ms':999}).encode()
     (folder/f'{j}.json.metrics.json').write_bytes(data)
     records.append(dict(slot=f'{s}-{arm}-{kind}',input_id='i',root_id='r',arm=arm,kind=kind,session=s,
       status='COMPLETE',endpoint_equal=True,service_s=1,metrics_sha256=hashlib.sha256(data).hexdigest()))
  (p/'RECORDS.json').write_text(json.dumps({'records':records}));return panel,records
 def test_exact_metadata(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);panel,_=self.fixture(p);a=costs.scan_saved(p,panel)
   self.assertEqual(a['slots'],72);self.assertEqual(a['summary']['M']['service_s'],6)
   self.assertIsNone(a['records'][0]['draft_s']);self.assertIsNone(a['records'][0]['legacy_windows_s']['prefill_ms'])
 def test_partial_not_complete(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);panel,rs=self.fixture(p);(p/'RECORDS.json').write_text(json.dumps({'records':rs[:-1]}))
   with self.assertRaises(ValueError):costs.scan_saved(p,panel)
 def test_metric_mutation(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);panel,_=self.fixture(p);(p/'runs/main-s0-r0-M/0.json.metrics.json').write_text('{}')
   with self.assertRaises(ValueError):costs.scan_saved(p,panel)
if __name__=='__main__':unittest.main()
