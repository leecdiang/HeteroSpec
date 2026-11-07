import hashlib,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from design import caller_chunks
class OriginalInterfaceTests(unittest.TestCase):
    def test_verbatim_fixture_identity(self):
        folder=Path(__file__).parent/'fixtures'
        pin=json.loads((folder/'ORIGINAL_INTERFACE.json').read_text())
        self.assertEqual(hashlib.sha256((folder/'original_prefill.inc').read_bytes()).hexdigest(),pin['method_sha256'])
    def test_original_width_domain_and_tail(self):
        for n in range(1,4097):
            for width in (1,2,4):
                schedule=caller_chunks(n,width)
                self.assertEqual(sum(schedule),n)
                self.assertTrue(all(x in (1,2,4) and x<=width for x in schedule))
            if n%4==3:self.assertEqual(caller_chunks(n,4)[-2:],[2,1])
if __name__=='__main__':unittest.main()
