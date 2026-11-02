from pathlib import Path
import tempfile,unittest,json
from object_archive import pack,verify,restore,read
from independent_qualification import transactions,endpoint

class ReconstructionTests(unittest.TestCase):
    def test_deduplicated_byte_exact_reconstruction_and_tamper(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);raw=p/'raw';raw.mkdir();(raw/'a.state').write_bytes(bytes(range(256)));(raw/'b.state').write_bytes(bytes(range(256)));(raw/'failed.log').write_text('preserved failure');(raw/'runtime.dll').write_bytes(b'native binary')
            pack(raw,p/'archive',limit=260);result=verify(p/'archive');self.assertEqual(result['files'],4);self.assertEqual(result['objects'],3)
            restore(p/'archive',p/'restored')
            for f in raw.iterdir():self.assertEqual(f.read_bytes(),(p/'restored'/f.name).read_bytes())
            first=read(p/'archive/INDEX.json')['parts'][0]['name'];f=p/'archive'/first;f.write_bytes(f.read_bytes()+b'tampered')
            with self.assertRaises(ValueError):verify(p/'archive')
    def test_independent_acceptance_and_rejection(self):
        r={'ids':[1,2,9],'eog':[False,False,True],'length':3,'terminal_id':9,'stop_reason':'EOG','slot':{'arm':'C_QB'},'prompt_ids':[100,101],'cycles':[{'cycle':0,'base':2,'output_begin':1,'proposals':[2,3,4],'decisions':[2,9,7,5],'verify_ids':[1,2,3,4],'accepted':1,'bonus':False,'emitted':[2,9],'keep':4,'target_kv_max':3,'draft_kv_max':3}]}
        endpoint(r);mapping,vectors=transactions(r);self.assertEqual(mapping,{0:'initial',1:'verify-0-0',2:'verify-0-1'});self.assertEqual(len(vectors),8)
        r['cycles'][0]['accepted']=2
        with self.assertRaises(ValueError):transactions(r)

if __name__=='__main__':unittest.main()
