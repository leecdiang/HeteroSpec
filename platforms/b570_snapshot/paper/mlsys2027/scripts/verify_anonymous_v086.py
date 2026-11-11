#!/usr/bin/env python3
"""Stdlib reviewer verifier: preserved primary assertions + post-study replay."""
import hashlib,json
from pathlib import Path
from verify_original import validate
from analysis import compute
ROOT=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def main():
    manifest=read(ROOT/'SHA256SUMS.json')
    assert {p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file()}==set(manifest)|{'SHA256SUMS.json'}
    for name,digest in manifest.items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    studies={p.stem:read(p) for p in (ROOT/'evidence').glob('*.json')}
    original=validate(studies)
    derived,_=compute(read(ROOT/'derived/inputs.json'))
    assert json.loads(json.dumps(derived))==read(ROOT/'derived/results.json')
    print(json.dumps({'status':'PASS','original_studies':original,'post_study_replay':'PASS','limits':'retained arrays/times/logits and conditional arithmetic only; no original absolute-time or omitted-asset authentication; no models'}))
if __name__=='__main__':main()
