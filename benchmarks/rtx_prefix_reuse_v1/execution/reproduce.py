"""Replay one delivered native manifest from verified archives on a supported RTX host."""
import argparse,hashlib,json,os,subprocess,zipfile
from pathlib import Path
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--runtime',type=Path,required=True);p.add_argument('--raw',type=Path,required=True);p.add_argument('--model',type=Path,required=True);p.add_argument('--slot',required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--prepare-only',action='store_true');a=p.parse_args()
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    with zipfile.ZipFile(a.raw) as raw,zipfile.ZipFile(a.runtime) as runtime:
        index=json.loads(raw.read('index.json'));ri=json.loads(runtime.read('index.json'))
        def get(name):
            record=index[name];data=raw.read('blobs/'+record['sha256']);assert hashlib.sha256(data).hexdigest()==record['sha256'];return data
        manifest=json.loads(get(a.slot+'/input.json'));launch=json.loads(get(a.slot+'/launch.json'));freeze=json.loads(get('SOURCE_POLICY_FREEZE.json'))
        assert digest(a.model)==freeze['model_sha256'],'wrong model bytes'
        role='candidate' if launch['exe']==freeze['source']['exe'] else 'oracle'
        exe=out/'worker.exe'
        for name in [role+'/worker.exe',*[n for n in ri if n.startswith('modules/')]]:
            target=out/Path(name).name;data=runtime.read(name);assert hashlib.sha256(data).hexdigest()==ri[name]['sha256'];target.write_bytes(data)
        assert digest(exe)==launch['exe'],'manifest requires a different engineering executable'
        state_dir=out/'snapshots';state_dir.mkdir()
        for unit in manifest.get('units',[]):
            if 'state' not in unit:continue
            original=unit['state'].replace('\\','/');assert original.startswith('E:/rtx172/')
            name=original[len('E:/rtx172/'):];record=index[name];target=state_dir/(record['sha256']+'.bin')
            if not target.exists():target.write_bytes(get(name))
            unit['state']=str(target)
        manifest_path=out/'input.json';manifest_path.write_text(json.dumps(manifest),encoding='utf8');native=out/'native';native.mkdir()
    (out/'replay-binding.json').write_text(json.dumps(dict(runtime_archive_sha256=digest(a.runtime),raw_archive_sha256=digest(a.raw),original_slot=a.slot,original_launch=launch,prepare_only=a.prepare_only),indent=2))
    if not a.prepare_only:
        env={k:v for k,v in os.environ.items() if not k.startswith(('HS_','GGML_','JSA_','HSC_'))}
        with (out/'native.log').open('xb') as log:subprocess.run([exe,a.model,manifest_path,native],stdout=log,stderr=subprocess.STDOUT,env=env,timeout=1800,check=True)
if __name__=='__main__':main()
