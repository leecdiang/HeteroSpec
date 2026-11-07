import sys,tempfile,unittest,zipfile,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'source'),str(ROOT/'src/rev2')]
from evidence_pack import write_manifest,archive
from evidence_contract import manifest_check
class Pack(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'tmp');self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name);self.root=self.base/'sealed';self.root.mkdir();(self.root/'failed.log').write_bytes(b'actual failure preserved');self.out=self.base/'external';(self.root/'ACQUISITION.json').write_text(json.dumps(dict(first_preparation_utc='2026-10-18T15:00:00Z')));(self.root/'CAMPAIGN.json').write_text(json.dumps(dict(schema=1,first_preparation_utc='2026-10-18T15:00:00Z',external_root=str(self.out),original_root=str(self.root),previous=[])))
 def test_exact_tree_with_old_post_directory(self):
  (self.root/'delivery/post_manifest').mkdir(parents=True);(self.root/'delivery/post_manifest/must-retain.log').write_bytes(b'failure')
  x=write_manifest(self.root);self.assertEqual(x['members'],4);manifest_check(self.root,'delivery/EVIDENCE_MANIFEST.json')
  a=archive(self.root,self.out);self.assertEqual(a['members'],5)
  with zipfile.ZipFile(self.out/'RAW_EVIDENCE.zip') as z:self.assertEqual(z.read('delivery/post_manifest/must-retain.log'),b'failure')
 def test_archive_cannot_write_inside_root(self):
  write_manifest(self.root)
  with self.assertRaisesRegex(ValueError,'outside'):archive(self.root,self.root/'hidden-tail')
 def test_postseal_new_failure_rejected(self):
  write_manifest(self.root);(self.root/'late-failure.log').write_bytes(b'late')
  with self.assertRaisesRegex(ValueError,'exact sealed tree'):archive(self.root,self.out)
  self.assertFalse((self.out/'RAW_EVIDENCE.zip').exists())
 def test_postseal_changed_failure_rejected(self):
  write_manifest(self.root);(self.root/'failed.log').write_bytes(b'changed')
  with self.assertRaisesRegex(ValueError,'manifest member'):archive(self.root,self.out)
if __name__=='__main__':unittest.main()
