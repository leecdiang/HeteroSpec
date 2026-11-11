"""Seal all build/driver/model inputs before native execution."""
from pathlib import Path
import argparse,hashlib,json,subprocess,datetime
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--bin',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--model-root',type=Path,required=True);a=p.parse_args();kit=Path(__file__).resolve().parent
    if a.out.exists():raise ValueError('Fresh freeze path required')
    files=[f for f in kit.rglob('*') if f.is_file() and '__pycache__' not in f.parts and f!=a.out]
    files+=list(a.bin.glob('*.dll'))+list(a.bin.glob('*.exe'))
    for m in json.loads((kit/'MODEL_IDENTITY.json').read_text()):
        f=a.model_root/Path(m['path']).name
        if f.stat().st_size!=m['bytes'] or sha(f)!=m['sha256']:raise ValueError('Model identity changed')
        files.append(f)
    records=[{'path':str(f.resolve()),'bytes':f.stat().st_size,'sha256':sha(f)} for f in sorted(set(files))]
    r={'status':'FROZEN_BEFORE_NATIVE','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':records,'new_build':True,'historical_binary_identity_claim':False,'plan_sha256':sha(kit/'PLAN.json')}
    a.out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print('Frozen',len(records),'files')
if __name__=='__main__':main()
