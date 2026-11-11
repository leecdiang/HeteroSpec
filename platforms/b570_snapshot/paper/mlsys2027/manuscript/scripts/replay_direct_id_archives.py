"""Replay frozen direct-ID archives offline; never execute model runners."""
from pathlib import Path
import hashlib,json,subprocess,sys,tarfile,tempfile
HERE=Path(__file__).resolve().parents[1];REPO=HERE.parents[2];E=HERE.parent/'evidence'
def main():
    archives=[('rtx_direct_id_v2','archive_manifest.json','sha256','fc3676adae93c4f21bf6e29d9787d95d1e60d08c2d7223de30fc58c46c3e0822'),
              ('b570_direct_id_v1','ARCHIVE.json','archive_sha256','58daa4159de12042c73194bbd99abc5e5e23c171578ea873675f07901582db20')]
    for study,filename,key,expected in archives:
        folder=REPO/'artifacts'/study;meta=json.loads((folder/filename).read_text())
        archive=folder/meta['archive']
        assert hashlib.sha256(archive.read_bytes()).hexdigest()==meta[key]==expected
        if study.startswith('rtx'):
            command=[sys.executable,str(REPO/'scripts/verify_rtx_direct_id_v2.py'),str(archive),'--output',str(E/'DIRECT_ID_RTX_OFFLINE_V07.json')]
            subprocess.run(command,cwd=REPO,check=True)
        else:
            with tempfile.TemporaryDirectory(prefix='heterospec-b570-offline-') as temporary:
                root=Path(temporary)
                with tarfile.open(archive) as bundle:bundle.extractall(root,filter='data')
                base=root/'b570_direct_id_v1'
                command=[sys.executable,str(REPO/'scripts/platform/b570_direct_id_v1/verify.py'),
                         '--root',str(base/'formal'),'--protocol',str(base/'protocol/protocol_v1.json'),
                         '--analysis',str(base/'protocol/FORMAL_ANALYSIS.json'),'--manifest',str(base/'SHA256_MANIFEST.json'),
                         '--output',str(E/'DIRECT_ID_B570_OFFLINE_V07.json')]
                subprocess.run(command,cwd=REPO,check=True)
    print('Both content-addressed direct-ID archives independently replayed offline.')
if __name__=='__main__':main()
