import subprocess
import tempfile
import unittest
from pathlib import Path
import history_inputs

class ReachableTreesTest(unittest.TestCase):
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
