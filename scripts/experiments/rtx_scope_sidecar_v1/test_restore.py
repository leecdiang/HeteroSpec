import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from restore_objects import restore,sha,safe

class RestoreTests(unittest.TestCase):
    def fixture(self,root):
        data=b'exact retained bytes\x00\xff';h=hashlib.sha256(data).hexdigest();part=root/'p.zip'
        with zipfile.ZipFile(part,'w') as z:z.writestr('objects/'+h,data)
        manifest={'objects':[{'sha256':h,'bytes':len(data)}],'members':[{'snapshot':'a','path':name,'sha256':h,'bytes':len(data)} for name in ('one.bin','nested/two.bin')]}
        m=root/'completed-through-day0.OBJECT_MEMBERS.json';m.write_text(json.dumps(manifest),encoding='utf-8')
        index=root/'index.json';index.write_text(json.dumps({'members_manifest':{'sha256':sha(m)},'parts':[{'path':'parts/p.zip','sha256':sha(part),'bytes':part.stat().st_size,'objects':[h]}]}),encoding='utf-8')
        return index,part,data

    def test_duplicate_paths_restore_exact_bytes_and_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);index,part,data=self.fixture(root);out=root/'restored'
            self.assertEqual(restore(root,index,sha(index),out)['members'],2)
            self.assertEqual((out/'a/nested/two.bin').read_bytes(),data)
            with self.assertRaisesRegex(ValueError,'fresh output'):restore(root,index,sha(index),out)

    def test_corrupt_download_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);index,part,data=self.fixture(root);part.write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError,'part hash'):restore(root,index,sha(index),root/'out')

    def test_paths_cannot_escape(self):
        for name in ('../escape','a/../../escape','C:/escape','/escape','a\\escape'):
            with self.assertRaises(ValueError):safe(Path.cwd(),name)

if __name__=='__main__':unittest.main()
