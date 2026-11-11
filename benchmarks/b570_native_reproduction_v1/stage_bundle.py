"""Stage explicit source/runtime/real fixtures and references, then verify a fresh copy."""
from pathlib import Path
import argparse,importlib.util,json,shutil
def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--run',type=Path,required=True);p.add_argument('--reference',type=Path,required=True);p.add_argument('--dest',type=Path,required=True);p.add_argument('--fresh',type=Path,required=True);a=p.parse_args()
    if a.dest.exists() or a.fresh.exists():raise ValueError('Fresh package and copy directories required')
    kit=Path(__file__).resolve().parent
    a.dest.mkdir(parents=True)
    shutil.copytree(kit,a.dest/'kit',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    shutil.copytree(a.run/'build/bin/Release',a.dest/'runtime')
    shutil.copytree(a.run/'fixture-a2',a.dest/'fixture')
    for i in range(4):shutil.copytree(a.reference/f'qual-{i}',a.dest/'references'/f'qual-{i}')
    shutil.copyfile(a.run/'upstream.tar.gz',a.dest/'upstream.tar.gz')
    util=a.repo/'scripts/native_reproduction/bundle_manifest.py'
    shutil.copyfile(util,a.dest/'bundle_manifest.py')
    spec=importlib.util.spec_from_file_location('bundle_manifest',util);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    includes=[x.relative_to(a.dest).as_posix() for x in sorted(a.dest.rglob('*')) if x.is_file()]
    identity={'source_commit':'0cae43063cf15170e91a2ff4d034da0ecef4a1b2','build_identity':'new build; per-file runtime hashes in this manifest','model_identity':json.loads((kit/'MODEL_IDENTITY.json').read_text()),'device_identity':'Arc B570; numerical replay reported separately'}
    created=m.create(a.dest,includes,'b570',a.dest/'manifest.json',identity)
    shutil.copytree(a.dest,a.fresh)
    checked=m.verify(a.fresh,m.read_json(a.fresh/'manifest.json'))
    receipt={'created':created,'fresh_copy':str(a.fresh),'verification':checked,'scope':'Integrity only. Native fresh-copy receipts are separate.'}
    (a.run/'FRESH_COPY_INTEGRITY.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    if checked['status']!='PASS':raise ValueError('Copy mismatch')
    print(json.dumps({'status':'PASS','files':len(includes),'fresh':str(a.fresh)}))
if __name__=='__main__':main()
