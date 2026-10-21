"""Real isolated child launches; import-only checks, never native gate acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parent))
from entry_bootstrap import expected_modules
ENTRIES=('observe.py','outer_watchdog.py','stall_supervisor.py','stall_harness.py')

def authenticate(root,manifest,expected):
    raw=Path(manifest).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('preflight manifest digest')
    files=json.loads(raw)['files']
    actual={p.relative_to(root).as_posix() for directory in ('source','src/rev2')
            for p in (root/directory).rglob('*') if p.is_file()}
    if actual!=set(files):raise ValueError('preflight exact source inventory')
    for rel,h in files.items():
        p=root/rel
        if root not in p.resolve().parents or p.is_symlink() or '__pycache__' in p.parts:
            raise ValueError('preflight source alias/bytecode')
        if hashlib.sha256(p.read_bytes()).hexdigest()!=h:raise ValueError('preflight source digest')
    return files

def probe_entries(root,python,cwd):
    results=[]
    for name in ENTRIES:
        entry=(root/'source'/name).resolve()
        argv=[str(python),'-I','-B',str(entry),'--startup-check']
        cp=subprocess.run(argv,cwd=cwd,capture_output=True,text=True,timeout=30)
        record=dict(entry=name,argv=argv,cwd=str(cwd),exit_code=cp.returncode,
                    stdout=cp.stdout,stderr=cp.stderr)
        results.append(record)
        if cp.returncode!=0:break
        try:
            d=json.loads(cp.stdout)
            valid=(d['status']=='ENTRY_IMPORT_READY' and d['entry']==str(entry)
                   and Path(d['python']).resolve()==Path(python).resolve()
                   and d['root']==str(root)
                   and d['modules']=={n:str(path) for n,path in expected_modules(root,entry).items()})
        except (ValueError,KeyError,TypeError):valid=False
        record['identity_checked']=valid
        if not valid:break
    return results

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--manifest',required=True)
    p.add_argument('--manifest-sha256',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    root=Path(a.root).resolve();output=Path(a.output).resolve()
    if sys.platform!='win32':raise RuntimeError('native startup preflight requires Windows')
    if root!=Path(__file__).resolve().parents[1]:raise ValueError('preflight deployed root')
    if root not in output.parents or output.exists():raise ValueError('fresh confined preflight output required')
    authenticate(root,a.manifest,a.manifest_sha256)
    output.parent.mkdir(parents=True,exist_ok=True)
    result=dict(status='STARTUP_PREFLIGHT_FAILED',manifest_sha256=a.manifest_sha256,
                native_gate_acceptance=False,records=[],error=None)
    try:
        with tempfile.TemporaryDirectory(prefix='startup-cwd-',dir=output.parent) as cwd:
            result['records']=probe_entries(root,Path(sys.executable).resolve(),cwd)
        if len(result['records'])==len(ENTRIES) and all(r.get('identity_checked') for r in result['records']):
            authenticate(root,a.manifest,a.manifest_sha256)
            result['status']='STARTUP_PREFLIGHT_PASS'
    except Exception as e:result['error']=repr(e)
    with output.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result))
    return 0 if result['status']=='STARTUP_PREFLIGHT_PASS' else 1
if __name__=='__main__':sys.exit(main())
