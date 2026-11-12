"""Synthetic transport/strict replay fixtures; never GPU or public admission."""
import contextlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import package as transport


class Package(unittest.TestCase):
    def exercise(self,broken=False):
        implementation=Path(__file__).resolve().parent.parent/'execution_v1'
        sys.path.insert(0,str(implementation))
        from support import fresh,sha
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);phase=root/'phase';(phase/'workers').mkdir(parents=True)
            fresh(phase/'STATE.json',dict(status='S1_PASSED_WAITING_F1_PUBLIC_READBACK',synthetic=True))
            fresh(phase/'LOCK_RELEASED.private.json',dict(synthetic=True))
            fresh(root/'manifest.json',dict(synthetic=True))
            fresh(root/'configuration.json',dict(output_root=str(phase),manifest=str(root/'manifest.json')))
            tree=root/'logical';tree.mkdir();fresh(tree/'F1_INDEX.json',dict(synthetic=True))
            for name in ('QUALIFIED_BINDINGS.json','CALLER_CLASSES.json','REGISTRATION.json','S2_COMPLETE_WORKERS.json'):
                fresh(tree/'F1_DATA'/name,dict(synthetic=True,name=name))
            fresh(tree/'F1_DATA/S1/full-record.json',dict(synthetic=True,complete_vector_commitment='a'*64,negative='retained'))
            public=root/'public'
            with contextlib.redirect_stdout(io.StringIO()):
                transport.prepare(implementation,root/'configuration.json',root,tree,public,root/'archive.tar.gz')
            cache=root/'downloaded';shutil.copytree(public,cache)
            metadata=json.loads((public/'F1_INDEX.json').read_text())
            files=metadata['files']+[dict(path='F1_INDEX.json',sha256=sha(public/'F1_INDEX.json'),bytes=(public/'F1_INDEX.json').stat().st_size)]
            commit='f'*40
            proof=dict(status='COMPLETE_FILE_BYTES_MATCHED',anonymous=True,synthetic=True,commit=commit,index_name='F1_INDEX.json',
                files=[dict(public_path='fixture/'+item['path'],url='https://raw.githubusercontent.com/leecdiang/HeteroSpec/'+commit+'/fixture/'+item['path'],
                            source_file=str(public/item['path']),downloaded_file=str(cache/item['path']),sha256=item['sha256'],bytes=item['bytes'])for item in files])
            fresh(root/'proof.json',proof)
            if broken:
                part=next((cache/'F1_ARCHIVE').glob('*.b64'));part.write_bytes(part.read_bytes()+b'!')
                with self.assertRaisesRegex(ValueError,'changed/truncated'):
                    transport.verify_members(implementation,cache,root/'proof.json',root/'restored',root/'report.json')
                self.assertFalse((root/'restored').exists())
            else:
                with contextlib.redirect_stdout(io.StringIO()):
                    transport.verify_members(implementation,cache,root/'proof.json',root/'restored',root/'report.json')
                for p in tree.rglob('*'):
                    if p.is_file():self.assertEqual(p.read_bytes(),(root/'restored'/p.relative_to(tree)).read_bytes())
                self.assertIn('complete_archive_member_readback',json.loads((root/'proof.json').read_text()))

    def test_complete_member_roundtrip(self):self.exercise()
    def test_changed_fragment_has_no_restored_payload(self):self.exercise(True)


if __name__=='__main__':unittest.main()
