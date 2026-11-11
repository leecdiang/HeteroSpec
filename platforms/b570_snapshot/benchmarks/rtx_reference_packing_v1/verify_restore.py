"""Verify authenticated archive bytes and every restored member; independent CPU reread."""
import argparse
import json
from pathlib import Path
import zipfile
from prepare import ROOT,sha,save

def main():
    p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--manifest',required=True);p.add_argument('--destination',required=True);p.add_argument('--remote-commit',required=True);a=p.parse_args()
    archive=Path(a.archive);manifest=Path(a.manifest);m=json.loads(manifest.read_bytes())
    assert archive.stat().st_size==m['bytes'] and sha(archive)==m['sha256']
    assert manifest.read_bytes()==(ROOT/'RAW_ARCHIVE_MANIFEST.json').read_bytes()
    target=Path(a.destination);target.mkdir(exist_ok=False)
    with zipfile.ZipFile(archive) as z:
        assert len(z.infolist())==len(m['members']) and len(set(z.namelist()))==len(m['members'])
        for item in z.infolist():assert not Path(item.filename).is_absolute() and '..' not in Path(item.filename).parts
        z.extractall(target)
    for item in m['members']:
        path=target/item['path'];assert path.stat().st_size==item['bytes'] and sha(path)==item['sha256']
    save(ROOT/'AUTHENTICATED_ARCHIVE_BYTES_RESTORE.json',dict(status='BYTES_PASS_CPU_RECHECK_PENDING',remote_commit=a.remote_commit,archive_sha256=m['sha256'],
        archive_bytes=m['bytes'],members_verified=len(m['members']),fresh_restore=str(target),new_schedules=0,
        external_audit=False,note='Execute restored recheck.py in a new interpreter; do not treat extraction as numerical recheck'))
    print(json.dumps(dict(members_verified=len(m['members']),new_schedules=0,status='BYTES_PASS_CPU_RECHECK_PENDING')))
if __name__=='__main__':main()
