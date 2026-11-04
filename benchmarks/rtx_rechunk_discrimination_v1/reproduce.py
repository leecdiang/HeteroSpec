"""Portable delivered-manifest replay; --prepare-only never starts a model."""
import argparse,hashlib,json,os,subprocess,zipfile
from pathlib import Path
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--runtime',type=Path,required=True);p.add_argument('--raw',type=Path,required=True);p.add_argument('--model',type=Path,required=True);p.add_argument('--slot',required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--prepare-only',action='store_true');a=p.parse_args()
    assert digest(a.runtime)=='24d647dbf7bedb1003e766363d24cad04d55094290f1b06d6e17a342cb328d12'
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    with zipfile.ZipFile(a.raw) as raw,zipfile.ZipFile(a.runtime) as runtime:
        ix=json.loads(raw.read('index.json'));ri=json.loads(runtime.read('index.json'))
        def get(name):
            b=raw.read('blobs/'+ix[name]['sha256']);assert hashlib.sha256(b).hexdigest()==ix[name]['sha256'];return b
        freeze=json.loads(get('FREEZE.json'));assert digest(a.model)==freeze['model_sha256']
        manifest=json.loads(get(a.slot+'/input.json'));launch=json.loads(get(a.slot+'/launch.json'));binding=json.loads(get('candidate01/binding.json'))
        for name in [n for n in ri if n.startswith('modules/')]:
            b=runtime.read(name);assert hashlib.sha256(b).hexdigest()==ri[name]['sha256'];(out/Path(name).name).write_bytes(b)
        exe=out/'worker.exe'
        if launch['exe']==binding['exe']:exe.write_bytes(get('candidate01/worker.exe'))
        else:
            name='oracle/worker.exe' if all(u['arm']=='R' for u in manifest['units']) else 'candidate/worker.exe'
            b=runtime.read(name);assert hashlib.sha256(b).hexdigest()==ri[name]['sha256'];exe.write_bytes(b)
        assert digest(exe)==launch['exe']
        for name,h in binding['modules'].items():assert digest(out/name)==h
        states=out/'snapshots';states.mkdir()
        for u in manifest['units']:
            if 'state' not in u:continue
            old=u['state'].replace('\\','/');assert old.startswith('F:/rtx176/')
            name=old[len('F:/rtx176/'):];target=states/(ix[name]['sha256']+'.bin')
            if not target.exists():target.write_bytes(get(name))
            u['state']=str(target)
        inp=out/'input.json';inp.write_text(json.dumps(manifest));native=out/'native';native.mkdir()
    (out/'replay-binding.json').write_text(json.dumps(dict(raw_sha256=digest(a.raw),runtime_sha256=digest(a.runtime),slot=a.slot,launch=launch,prepare_only=a.prepare_only),indent=2))
    if not a.prepare_only:
        env={k:v for k,v in os.environ.items() if not k.startswith(('HS_','GGML_','JSA_','HSC_'))}
        with (out/'native.log').open('xb') as log:subprocess.run([exe,a.model,inp,native],stdout=log,stderr=subprocess.STDOUT,env=env,timeout=1800,check=True)
if __name__=='__main__':main()
