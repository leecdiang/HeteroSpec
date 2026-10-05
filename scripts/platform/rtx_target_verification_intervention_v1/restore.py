"""Restore all logical evidence files from the CAS archive into an empty directory."""
import argparse, hashlib, json, os, pathlib, tarfile
def sha(p):
    with pathlib.Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def restore(archive,dest):
    archive=pathlib.Path(archive);dest=pathlib.Path(dest)
    if dest.exists() and any(dest.iterdir()):raise RuntimeError('restore destination must be empty')
    dest.mkdir(parents=True,exist_ok=True);cas=dest/'cas';cas.mkdir()
    with tarfile.open(archive,'r:gz') as t:
        for m in t:
            if m.name=='MANIFEST.json':manifest=json.load(t.extractfile(m));continue
            if not m.name.startswith('cas/') or not m.isfile():raise RuntimeError('unsafe archive member')
            h=m.name.split('/')[1];assert len(h)==64 and all(c in '0123456789abcdef' for c in h)
            with (cas/h).open('wb') as f:
                source=t.extractfile(m)
                for b in iter(lambda:source.read(8*1024*1024),b''):f.write(b)
            assert sha(cas/h)==h
    for name,row in manifest['files'].items():
        relative=pathlib.PurePosixPath(name)
        if relative.is_absolute() or '..' in relative.parts:raise RuntimeError('unsafe logical path')
        p=dest/pathlib.Path(name);p.parent.mkdir(parents=True,exist_ok=True);os.link(cas/row['sha256'],p)
        assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
    (dest/'RESTORE_RECEIPT.json').write_text(json.dumps({'status':'PASS','logical_files':len(manifest['files']),'archive_sha256':sha(archive)},indent=2)+'\n',encoding='utf-8')
    return manifest
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--archive',type=pathlib.Path,required=True);p.add_argument('--dest',type=pathlib.Path,required=True);a=p.parse_args();x=restore(a.archive,a.dest);print(json.dumps({'status':'PASS','files':len(x['files'])}))
