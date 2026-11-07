"""Clean reconstruction, extraction, manifest and independent evidence checks."""
import argparse, hashlib, json, shutil, subprocess, sys, tarfile, tempfile
from pathlib import Path

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,required=True);a=p.parse_args();record=json.loads(a.archive.read_text(encoding='utf-8'))
    with tempfile.TemporaryDirectory(prefix='b570-partition-offline-') as directory:
        directory=Path(directory);archive=directory/'evidence.tar.gz';dest=directory/'extracted';dest.mkdir()
        with archive.open('wb') as out:
            for part in record['parts']:
                path=a.archive.parent/part['path'];assert sha(path)==part['sha256'] and path.stat().st_size==part['bytes']
                with path.open('rb') as src:shutil.copyfileobj(src,out)
        assert sha(archive)==record['archive_sha256']
        with tarfile.open(archive,'r:gz') as ar:ar.extractall(dest,filter='data')
        manifest=dest/'MANIFEST.json';assert sha(manifest)==record['manifest_sha256']
        files=json.loads(manifest.read_text(encoding='utf-8'))['files']
        for name,h in files.items():assert sha(dest/name)==h['sha256'] and (dest/name).stat().st_size==h['bytes'],name
        subprocess.run([sys.executable,str(dest/'scripts/platform/b570_partition_intervention_v1/verify_complete.py'),'--root',str(dest)],check=True)
        print('Clean-extraction manifest PASS:',len(files),'files')

if __name__=='__main__':main()
