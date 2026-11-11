"""Recover byte-pinned historical sources; build without any old object/library."""
from pathlib import Path
import argparse, hashlib, json, shutil, tarfile, difflib

UPSTREAM = '0cae43063cf15170e91a2ff4d034da0ecef4a1b2'
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def write(p, obj):
    Path(p).write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8')
def main():
    p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,required=True);p.add_argument('--dest',type=Path,required=True);a=p.parse_args()
    kit=Path(__file__).resolve().parent
    if a.dest.exists():raise ValueError('Fresh destination required')
    a.dest.mkdir(parents=True)
    with tarfile.open(a.archive) as t:t.extractall(a.dest,filter='data')
    src=a.dest/('llama.cpp-'+UPSTREAM)
    if not src.is_dir():raise ValueError('Wrong upstream archive')
    inventory=json.loads((kit/'SOURCE_INPUTS.json').read_text())
    for row in inventory['upstream']:
        f=src/row['path']
        if f.stat().st_size!=row['bytes'] or sha(f)!=row['sha256']:raise ValueError('Upstream mismatch '+row['path'])
    for row in inventory['overlays']:
        f=kit/row['source']
        if sha(f)!=row['sha256']:raise ValueError('Overlay mismatch '+row['source'])
        shutil.copyfile(f,src/row['destination'])
    write(a.dest/'PREPARED_SOURCE.json',{'upstream_commit':UPSTREAM,'upstream_files':len(inventory['upstream']),'archive_sha256':sha(a.archive),'source':str(src),'overlay_files':inventory['overlays'],'old_build_inputs':[]})
    print(src)
if __name__=='__main__':main()
