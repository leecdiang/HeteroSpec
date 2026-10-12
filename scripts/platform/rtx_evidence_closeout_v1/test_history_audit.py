import subprocess
import base64
import hashlib
import tempfile
import unittest
from pathlib import Path
import history_inputs

class ReachableTreesTest(unittest.TestCase):
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
