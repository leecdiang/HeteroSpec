import subprocess
import base64
import hashlib
import tempfile
import unittest
from pathlib import Path
import history_inputs

class ReachableTreesTest(unittest.TestCase):
    def test_aggregate_population_keeps_reservations_and_operational_hits(self):
        coord=dict(schema='heterospec.jsa.b570.coordination.v1',remaining_ranked_candidates=['MBPP/11','MBPP/12','MBPP/13'],provisional_b570_reservation=['MBPP/12'],rtx_reserved_ids=[])
        obj=dict(status='PASS_ACCESSIBLE_ID_AUDIT',confirmation_selection='NOT_PERFORMED',hits={'MBPP/11':['C:\\hs\\TOKENIZATION.stdout.jsonl','C:\\hs\\COORDINATION_SNAPSHOT.json'],'MBPP/12':['C:\\hs\\COORDINATION_SNAPSHOT.json'],'MBPP/13':['C:\\hs\\ACTUAL_REQUEST.json']})
        self.assertEqual(history_inputs.aggregate_availability_ids(obj,coord),{'MBPP/11'})
        obj['confirmation_selection']='PERFORMED'
        self.assertEqual(history_inputs.aggregate_availability_ids(obj,coord),set())

    def test_parallel_host_reader_keeps_bytes_and_hash_based_reuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);old=root/'old.txt';old.write_bytes(b'old')
            (root/'new.json').write_bytes(b'{"historical":"text"}')
            (root/'models').mkdir();(root/'models'/'excluded.txt').write_bytes(b'ignored directory')
            known=frozenset({hashlib.sha256(b'old').hexdigest()})
            rows=list(history_inputs.host_objects([root],known))
            names={p.name:(kind,value) for p,(kind,value) in rows}
            self.assertEqual(set(names),{'old.txt','new.json'})
            self.assertEqual(names['old.txt'],('reused_text',hashlib.sha256(b'old').hexdigest()))
            self.assertEqual(names['new.json'],('text',b'{"historical":"text"}'))
            old.write_bytes(b'new') # same size must still be freshly hashed
            names={p.name:(kind,value) for p,(kind,value) in history_inputs.host_objects([root],known)}
            self.assertEqual(names['old.txt'],('text',b'new'))

    def test_missing_blob_authenticated_bytes_are_verified_and_cached(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo=Path(tmp)/'repo';repo.mkdir();local=Path(tmp)/'audit';local.mkdir()
            subprocess.run(['git','init',str(repo)],check=True,capture_output=True)
            body=b'complete historical exposure text'
            oid=hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()
            saved=(history_inputs.REPO,history_inputs.LOCAL,history_inputs.api)
            try:
                history_inputs.REPO=repo;history_inputs.LOCAL=local
                history_inputs.api=lambda route:dict(encoding='base64',sha=oid,size=len(body),content=base64.b64encode(body).decode())
                self.assertEqual(history_inputs.load_git_blob(oid,'history.md'),body)
                history_inputs.api=lambda route: self.fail('cached blob must not request the remote again')
                self.assertEqual(history_inputs.load_git_blob(oid,'history.md'),body)
                self.assertTrue((local/'authenticated-text-blobs'/(oid+'.json')).exists())
            finally:
                history_inputs.REPO,history_inputs.LOCAL,history_inputs.api=saved

    def test_all_historical_text_blobs_and_quoted_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo=Path(tmp)/'repo';repo.mkdir();local=Path(tmp)/'audit';local.mkdir()
            def git(*args):
                return subprocess.check_output(['git',*args],cwd=repo,stderr=subprocess.DEVNULL).decode().strip()
            git('init');git('config','user.email','fixture@example.test');git('config','user.name','Fixture')
            (repo/'old text.json').write_text('{"exposed":"first"}')
            (repo/'weights.bin').write_bytes(b'irrelevant binary')
            git('add','.');git('commit','-m','first');old=git('rev-parse','HEAD:old text.json')
            (repo/'old text.json').unlink();(repo/'new.md').write_text('second exposure')
            git('add','-A');git('commit','-m','second');new=git('rev-parse','HEAD:new.md')
            saved=(history_inputs.REPO,history_inputs.LOCAL,history_inputs.git)
            try:
                history_inputs.REPO=repo;history_inputs.LOCAL=local;history_inputs.git=git
                objects=history_inputs.reachable_text_objects(set())
                self.assertEqual(objects,{old:'old text.json',new:'new.md'})
                (local/'REACHABLE_TEXT_TREES.json').unlink()
                self.assertEqual(history_inputs.reachable_text_objects({old}),{new:'new.md'})
            finally:
                history_inputs.REPO,history_inputs.LOCAL,history_inputs.git=saved

if __name__=='__main__':unittest.main()
