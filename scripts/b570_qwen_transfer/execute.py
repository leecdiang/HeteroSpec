"""Supervise one bounded native unit, retaining predictions, costs and outputs."""
import argparse, hashlib, json, os, shutil, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path
from build_driver import ROOT

OLD=Path('C:/hs/b570-producer-consumer-20261028')
PANEL=OLD/'freeze/NATIVE_PANEL.json'
LOCK=Path('C:/hs/b570-llama-exclusive.lock')
SUPERVISOR=Path('I:/HeteroSpec/b570-llama-20261102/oracle-01/supervisor.py')
IDS=(4,6,2)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,data):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(data,f,indent=2);f.write('\n')
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def historical(index):return read(OLD/f'run-primary/B1-{index}.job.json')
def record_unit(unit,build,slots,panel,prediction,admit=False,probe=False):
    unit=ROOT/'units'/unit
    unit.mkdir(parents=True,exist_ok=False)
    if not prediction:raise ValueError("pre-output structural prediction required")
    write(unit/'PREDICTION.json',{'utc':now(),'expected':prediction,'slots':slots,'admit':admit})
    template=historical(2)
    job={k:v for k,v in template.items() if k not in ('slots','payload_root','runtime_sha256')}
    manifest=ROOT/build/'FILES.json'
    job.update(slots=slots,payload_root=str(unit/'payload'),runtime_sha256=sha(manifest),admit=admit,probe=probe)
    write(unit/'JOB.json',job)
    models=read(OLD/'run-primary/B1-2.receipt.json')['argv'][2:4]
    pins=read(ROOT/'MODEL_PINS.json')['files']
    for model,pin in zip(models,pins):
        stat=Path(model).stat()
        if model!=pin['path'] or stat.st_size!=pin['bytes'] or stat.st_mtime_ns!=pin['mtime_ns']:raise ValueError('model identity changed')
    if not admit and not any(read(p)['success'] for p in (ROOT/'units').glob('admit-'+build+'*/RECEIPT.json')):raise ValueError("role not admitted")
    exe=ROOT/build/'build/bin/Release/boundary.exe'
    command=[sys.executable,'-B',str(SUPERVISOR),'--manifest',str(manifest),'--receipt',str(unit/'SUPERVISOR.json'),'--limit','900','--minimum-free-bytes',str(20*1024**3),str(exe),str(unit/'native'),*models,str(panel),str(unit/'JOB.json')]
    write(unit/'COMMAND.json',command)
    write(LOCK,{'pid':os.getpid(),'unit':str(unit),'utc':now()})
    started=time.monotonic()
    try:
        with (unit/'HOST.log').open('x') as f:p=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,timeout=1000)
        sup=read(unit/'SUPERVISOR.json')
        native=read(unit/'native/result.json')
        if sup['job_accounting']['active_processes']!=0:raise RuntimeError('unsettled native process')
        expected='ZERO_FORWARD_ADMITTED' if admit else 'PROBE_COMPLETE' if probe else 'WORKER_COMPLETE'
        ok=p.returncode==0 and native['status']==expected and native.get('normal_cleanup_returned')
        observed={Path(x['path']).name.lower():x['sha256'] for x in sup.get('loaded_module_hashes',[])}
        for f in read(manifest)['files']:
            name=Path(f['path']).name.lower()
            if name.endswith('.dll') and observed.get(name)!=f['sha256']:ok=False
        receipt={'success':bool(ok),'native_status':native['status'],'requests':len(native['requests']),'owned_seconds':time.monotonic()-started,'utc':now(),'pid':sup.get('pid'),'cleanup_verified':True,'supervisor_sha256':sha(unit/'SUPERVISOR.json')}
        write(unit/'RECEIPT.json',receipt)
        LOCK.unlink()
        if not ok:raise RuntimeError(str(receipt)+' '+str(native.get('error')))
    except BaseException:
        if (unit/'SUPERVISOR.json').exists() and read(unit/'SUPERVISOR.json').get('job_accounting',{}).get('active_processes')==0 and LOCK.exists():LOCK.unlink()
        raise
    print('NATIVE_UNIT',unit.name,receipt['requests'],flush=True)
    return native
def slots_for(index, indices,**flags):
    slots=[dict(historical(index)['slots'][i],**flags) for i in indices]
    for s in slots:
        s['compare_slot_id']=s['producer_match_slot_id']=None
    return slots
def pin_models():
    out=ROOT/'MODEL_PINS.json'
    if out.exists():return
    old=read(OLD/'run-primary/B1-2.launch.json')
    files=[]
    for f in old['files']:
        p=Path(f['path'])
        if p.suffix.lower()=='.gguf':
            assert p.stat().st_size==f['bytes'] and sha(p)==f['sha256']
            files.append(dict(f,mtime_ns=p.stat().st_mtime_ns))
    target,draft=read(OLD/'run-primary/B1-2.receipt.json')['argv'][2:4]
    write(out,{'files':[next(f for f in files if f['path']==n) for n in (target,draft)],'utc':now()})
def admit(build):
    attempts=len(list((ROOT/'units').glob('admit-'+build+'*')))
    name='admit-'+build+(f'-retry-{attempts}' if attempts else '')
    record_unit(name,build,slots_for(2,[2]),PANEL,'Load both original Q8 models on Vulkan B570; construct UB4 target and UB1 draft; zero decode.',True)
def original(build):
    for i in IDS:
        s=slots_for(i,[0],observer='heavy')
        name=f'original-{i}' if build=='original-adapter-00' else f'original-{build}-{i}'
        native=record_unit(name,build,s,PANEL,'Original numerical libraries, exact scalar R; retained P1 single-row vectors expected byte-identical.')
        row=native['requests'][0];old=read(OLD/f'run-primary/B1-{i}/result.json')['requests']
        vec={k:v['sha256'] for k,v in row['vectors'].items()}
        historical_vec={k:v['sha256'] for k,v in old[2]['vectors'].items()}
        assert row['endpoint']==old[0]['endpoint'] and vec==historical_vec
        for f in row['vectors'].values():assert sha(ROOT/'units'/name/'payload'/f['path'])==f['sha256']
        write(ROOT/'units'/name/'ORIGINAL_COMPARISON.json',dict(status='EXACT_ORIGINAL_MATCH',vectors=len(vec),original_endpoint=old[0]['endpoint']))
def known(build):
    for i in IDS:
        choices=[2,8,10] if i!=2 else [2,8,10,5,12,14]
        record_unit(f'retained-{i}-{build}',build,slots_for(i,choices,trace=True),PANEL,'Exact P1 UB4 producer, width-one calls. Q8 projection action predicted in two-row verification; physical prefix stays within one padding bucket. GSM P4T also tests batched producer precision.')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['admit','original','known']);p.add_argument('build');a=p.parse_args();pin_models();{'admit':admit,'original':original,'known':known}[a.action](a.build)

