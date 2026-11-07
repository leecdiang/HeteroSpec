"""Bounded deterministic CPU fixtures, retained first attempt and actual modules."""
import argparse, datetime, os, pathlib, subprocess, time
from common import ROOT, load, save, sha, modules
from fixtures import fixtures, write_input

def main():
    p=argparse.ArgumentParser();p.add_argument('group',choices=['dev','holdout']);a=p.parse_args()
    before=modules();host=ROOT/'_host'/a.group;host.mkdir(parents=True,exist_ok=False)
    git=[os.environ.get('HETEROSPEC_GIT','git'),'-C',str(ROOT),'rev-parse','HEAD']
    commit=subprocess.check_output(git,text=True).strip()
    if a.group=='holdout':assert (ROOT/'RULE_LOCK.json').exists(), 'Holdout needs committed rule lock'
    inputs=[]
    for f in fixtures(a.group):
        target=host/(f['id']+'.bin');digest=write_input(target,f)
        inputs.append(dict(**f,path=str(target),sha256=digest,bytes=target.stat().st_size))
    save(host/'inputs.json',inputs)
    exe=ROOT/'_host/build/Release/representation-cpu.exe';output=ROOT/(a.group.upper()+'_RAW.jsonl')
    assert not output.exists()
    start=datetime.datetime.now(datetime.timezone.utc).isoformat();t=time.monotonic()
    r=subprocess.run([str(exe),str(host/'inputs.json'),str(output)],capture_output=True,text=True)
    end=datetime.datetime.now(datetime.timezone.utc).isoformat()
    loaded=[]
    if output.exists():
        import json
        events=[json.loads(x) for x in output.read_text().splitlines()]
        loaded=next(x['loaded'] for x in events if x['event']=='MODULES')
        complete=[x for x in events if x['event']=='FIXTURE']
    else:complete=[]
    receipt=dict(group=a.group,commit=commit,begin_utc=start,end_utc=end,elapsed_s=time.monotonic()-t,
       returncode=r.returncode,stdout=r.stdout,stderr=r.stderr,executable_sha256=sha(exe),
       sources={str(f.relative_to(ROOT)):sha(f) for f in [ROOT/'fixtures.py',ROOT/'native/cpu.cpp',ROOT/'native/oracle.hpp']},
       inputs=[{k:v for k,v in x.items() if k!='path'} for x in inputs],
       planned=len(inputs),completed=len(complete),raw_sha256=sha(output) if output.exists() else None,
       actual_loaded_modules=[dict(path=x,sha256=sha(x)) for x in loaded],
       python_modules_before=before,python_modules_after=modules(),
       model_processes=0,model_requests=0,gpu_forwards=0,gpu_operator_starts=0,probes=0,warmups=0,
       cpu_harness_processes=1,automatic_retries=0)
    save(ROOT/(a.group.upper()+'_RECEIPT.json'),receipt)
    print({k:receipt[k] for k in ['group','returncode','planned','completed','elapsed_s','stderr']})
    raise SystemExit(r.returncode)

if __name__=='__main__':main()
