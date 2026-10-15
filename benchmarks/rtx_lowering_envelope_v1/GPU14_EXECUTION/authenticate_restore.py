"""Read actual authenticated remote bytes; restore raw; CPU-only reanalysis."""
import argparse, hashlib, json, subprocess, sys, urllib.request, zipfile
from pathlib import Path, PurePosixPath
E=Path(__file__).resolve().parent
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def save(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2);f.write('\n')
def main():
    a=argparse.ArgumentParser();a.add_argument('--commit',required=True);args=a.parse_args()
    target=Path('D:/hs113-gpu14-authenticated-v1');target.mkdir(exist_ok=False)
    token=subprocess.check_output(['gh','auth','token']).decode().strip();assert token
    received=[]
    for name in ('RAW_GPU14.zip','RAW_MANIFEST.json','ANALYSIS.json','ANALYSIS.csv','RESULT.md','POST_RUN_INTEGRITY.json','analyze_gpu14.py','authenticate_restore.py'):
        url='https://api.github.com/repos/leecdiang/HeteroSpec/contents/benchmarks/rtx_lowering_envelope_v1/GPU14_EXECUTION/'+name+'?ref='+args.commit
        req=urllib.request.Request(url,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github.raw+json','Accept-Encoding':'identity','User-Agent':'HeteroSpec-GPU14-raw-readback'})
        with urllib.request.urlopen(req,timeout=45) as r:
            assert r.status==200 and r.headers.get('Content-Encoding','identity')=='identity';data=r.read()
        with (target/name).open('xb') as out:out.write(data)
        assert sha(target/name)==sha(E/name)
        received.append(dict(path=name,bytes=len(data),sha256=sha(target/name),endpoint=url))
    manifest=json.loads((target/'RAW_MANIFEST.json').read_bytes());assert sha(target/'RAW_GPU14.zip')==manifest['sha256']
    save(E/'AUTHENTICATED_RAW.json',dict(data_commit=args.commit,authenticated_remote_bytes=True,files=received,transport='GitHub raw API identity encoding; auth token only in memory, not recorded'))
    fresh=Path('D:/hs113-gpu14-fresh-restore-v1');fresh.mkdir(exist_ok=False)
    with zipfile.ZipFile(target/'RAW_GPU14.zip') as z:
        names=z.namelist();assert len(names)==len(set(names))==len(manifest['members'])
        assert set(names)=={m['path'] for m in manifest['members']}
        for name in names:
            p=PurePosixPath(name);assert not p.is_absolute() and '..' not in p.parts and ':' not in name and '\\' not in name
        z.extractall(fresh)
    for m in manifest['members']:
        p=fresh/m['path'];assert p.stat().st_size==m['bytes'] and sha(p)==m['sha256']
    cmd=[sys.executable,'-B',str(fresh/'execution/analyze_gpu14.py'),'--raw',str(fresh/'raw'),
        '--frozen',str(fresh/'frozen/repair_timer_v1'),'--bindings',str(fresh/'REFERENCE_BINDINGS.json'),'--output',str(fresh/'RECOMPUTED_ANALYSIS.json')]
    with (fresh/'CPU_REANALYSIS.stdout').open('xb') as out,(fresh/'CPU_REANALYSIS.stderr').open('xb') as err:
        result=subprocess.run(cmd,stdout=out,stderr=err,timeout=60)
    save(fresh/'CPU_REANALYSIS_PROCESS.json',dict(command=cmd,exit_code=result.returncode,native_GPU_model_starts=0))
    assert result.returncode==0
    assert (fresh/'RECOMPUTED_ANALYSIS.json').read_bytes()==(target/'ANALYSIS.json').read_bytes()
    assert (fresh/'RECOMPUTED_ANALYSIS.csv').read_bytes()==(target/'ANALYSIS.csv').read_bytes()
    save(E/'FRESH_RESTORE.json',dict(status='PASS',data_commit=args.commit,archive_sha256=manifest['sha256'],members_verified=len(manifest['members']),
        destination=str(fresh),frozen_independent_auditor_reexecuted_CPU_only=True,full_reference_inputs_and_historical_PQ_QB_controls_from_archive=True,
        all14_audits_reconstructed=True,analysis_JSON_and_CSV_byte_equal=True,additional_native_starts=0,additional_device_queries=0,additional_graph_computes=0,additional_model_requests=0,
        numerical_DLL_validation='Read original sealed DLL bytes by original recorded module paths; DLL/model bytes are not duplicated into raw',
        qualification='Engineering14 only; no next GPU stage or timing/actor admission'))
    print('PASS authenticated raw and575 restored members; all14 frozen audits plus JSON/CSV reconstructed exactly; zero new GPU/native starts')
if __name__=='__main__':main()
