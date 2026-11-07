"""Task-local CPU8 configuration/launcher bridge; original detectors are unchanged."""
import sys,json,os,hashlib,time,subprocess,shutil,datetime
from pathlib import Path
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,sort_keys=True,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
def sources(design):
    return {p.relative_to(design).as_posix():h(p) for p in sorted(design.rglob('*')) if p.is_file() and (p.parent==design/'host' or p.name in ['ACCEPTANCE.json','BUDGET.json','check_receipts.py'])}
def prepare(root,runid,cid,phase,freeze_sha=None):
    root=Path(root).resolve();legacy=root/'legacy';design=legacy/'repo/benchmarks/b570_supervision_fix_v2'
    allowed=['normal_single','normal_transition','terminal_pending_completion','frozen_input','late_closed_slot_write','resource_read_failure','directory_read_timeout','journal_write_failure']
    assert cid in allowed and phase in ['D0','FORMAL']
    if phase=='FORMAL':
        from guards import FrozenBaseline
        FrozenBaseline(root,freeze_sha).check()
    matrix=json.loads((design/'ACCEPTANCE.json').read_bytes());spec=next(x for x in matrix['cases'] if x['id']==cid)
    run=legacy/'runs'/runid;run.mkdir(parents=True,exist_ok=False);protected=run/'protected';external=run/'external';protected.mkdir();external.mkdir()
    for n in ['slots','inputs','sealed','history']:(protected/n).mkdir()
    (external/cid).mkdir();registry={}
    def slot(n):
        name=runid+'__'+n;p=protected/'slots'/name;p.mkdir();(p/'BASELINE.bin').write_bytes(b'CPU_BASELINE');(p/'FENCE.bin').write_bytes(b'CPU_FENCE_BASELINE');registry[name]=dict(path=str(p),state='PREPARED');return name
    slot('inactive_fixture')
    slots=[slot(cid+'_'+str(i)) for i in range(16 if cid=='normal_transition' else 2 if cid=='late_closed_slot_write' else 1)]
    target={'resource_read_failure':'resource','directory_read_timeout':'directory','journal_write_failure':'journal'}.get(cid,'positive')
    filesystem=cid in ['frozen_input','late_closed_slot_write','terminal_pending_completion']
    if filesystem:
        target=protected/'inputs/frozen_input.bin' if cid=='frozen_input' else protected/'slots'/slots[0]/'BASELINE.bin' if cid=='late_closed_slot_write' else protected/'sealed/terminal_pending_completion.bin'
        if not target.exists():target.write_bytes(b'CPU_SACRIFICIAL_FROZEN')
        target=str(target.resolve())
    chosen=dict(spec,slots=slots,target=target,filesystem=filesystem)
    hashes=sources(design);dll=root/'compiled/candidate/LauncherCapture.dll';assert dll.is_file();hashes['host/LauncherCapture.dll']=h(dll)
    caps=external/'source_caps';caps.mkdir()
    for rel,digest in hashes.items():
        p=caps/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(dll if rel=='host/LauncherCapture.dll' else design/rel,p);assert h(p)==digest
    review=design/'SOURCE_REVIEW_FREEZE.json';build=design/'results/BUILD_RECORD.json'
    cfg=dict(schema=1,id=runid,root=str(run),revision=1,round=-1,order='listed',freeze_sha256=freeze_sha,cases=[chosen],registry=registry,code_hashes=hashes,registered_ns=time.perf_counter_ns(),GPU_queries=0,GPU_initializations=0,model_file_reads=0,model_requests=0,graph_computes=0,scientific_native_starts=0,launcher_log_dir=str(external/'launcher'),launcher_seconds=180 if cid=='normal_transition' else 90,protected_roots=[str(protected),str(design)],cpu8_legacy_root=str(legacy),cpu8_compiled_dll=str(dll),phase=phase,source_review_sha256=h(review) if review.exists() else None,build_record_sha256=h(build) if build.exists() else None)
    write(run/'CONFIG.json',cfg);return run,cfg
def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--run',required=True);p.add_argument('--case',required=True);p.add_argument('--phase',choices=['D0','FORMAL'],required=True);p.add_argument('--freeze-sha256');a=p.parse_args()
    root=Path(a.root).resolve();sys.path.insert(0,str(root/'src/rev2'));run,cfg=prepare(root,a.run,a.case,a.phase,a.freeze_sha256)
    design=root/'legacy/repo/benchmarks/b570_supervision_fix_v2'
    argv=['C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe','-NoLogo','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(design/'host/launch.ps1'),'-CasePath',str(run/'CONFIG.json')]
    begin=time.perf_counter_ns()
    with (run/'external/OUTER.stdout.log').open('xb') as out,(run/'external/OUTER.stderr.log').open('xb') as err:
        proc=subprocess.Popen(argv,stdout=out,stderr=err,creationflags=0x08000000)
        try:code=proc.wait(timeout=cfg['launcher_seconds']+30)
        except subprocess.TimeoutExpired:proc.kill();proc.wait();raise
    write(run/'LAUNCH_RECEIPT.json',dict(argv=argv,begin_ns=begin,end_ns=time.perf_counter_ns(),pid=proc.pid,exit_code=code,scope='OS closure independently recorded by command observer'))
    print(json.dumps(dict(run=a.run,case=a.case,phase=a.phase,launcher_exit=code)),flush=True);return code
if __name__=='__main__':sys.exit(main())
