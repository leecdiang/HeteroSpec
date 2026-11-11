"""Gated new live partition intervention; never consumes old output arrays."""
import argparse, gzip, hashlib, json, os, re, shutil, subprocess, sys, tarfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LOCAL = Path('C:/Users/DIANG/Documents/ChatGPT/HeteroSpec')
PLAN = ROOT/'benchmarks/b570_partition_intervention_v1'
RAW = ROOT/'artifacts/b570_partition_intervention_v1/raw'
BUILD = Path('C:/hs/b570-partition-intervention-v1-build')
EXE = BUILD/'Release/heterospec-partition.exe'
RUNTIME = Path('C:/hs/b570-direct-id-v1-build/bin/Release')
SRC = Path(__file__).resolve().parent
V1 = json.loads((ROOT/'benchmarks/b570_direct_id_v1/protocol_v1.json').read_text(encoding='utf-8'))
DATA = LOCAL/'datasets/humaneval/HumanEval.jsonl.gz'
TARGET = LOCAL/'models/gguf/Qwen3-8B-Q8_0.gguf'
DRAFT = LOCAL/'models/gguf/Qwen3-0.6B-Q8_0.gguf'
TASKS = ['HumanEval/'+str(i) for i in (134,42,145,138,19,20)]
PREFIX = 'Complete the following Python function. Return only the completed Python code, without Markdown fences.\n\n'
SALT = 'B570_LIVE_PARTITION_INTERVENTION_V1|2026-09-30|'

def utc(): return datetime.now(timezone.utc).isoformat()
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');t.replace(p)
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT,text=True,encoding='utf-8').strip()
def env_identity():
    cmd="[Console]::OutputEncoding=[Text.UTF8Encoding]::new(); [ordered]@{os=(Get-CimInstance Win32_OperatingSystem|Select-Object Caption,Version,BuildNumber);gpu=@(Get-CimInstance Win32_VideoController|Select-Object Name,DriverVersion,PNPDeviceID);vulkan_runtime=(Get-Item C:\\Windows\\System32\\vulkan-1.dll).VersionInfo.FileVersion}|ConvertTo-Json -Depth 6"
    return json.loads(subprocess.check_output(['powershell.exe','-NoProfile','-Command',cmd],encoding='utf-8-sig'))
def semantic(ids,flags):
    assert len(ids)==len(flags) and ids and all(type(x)==int and x>=0 for x in ids)
    assert all(type(x)==bool for x in flags)
    end=min(128,next((i+1 for i,x in enumerate(flags) if x),len(ids)))
    assert end==128 or flags[end-1]
    return ids[:end]
def checkpoint_pushed(file):
    rel=Path(file).relative_to(ROOT).as_posix();commit=git('log','-1','--format=%H','--',rel)
    assert subprocess.check_output(['git','show',commit+':'+rel],cwd=ROOT)==Path(file).read_bytes()
    branch=git('branch','--show-current');subprocess.run(['git','fetch','origin',branch],cwd=ROOT,check=True)
    subprocess.run(['git','merge-base','--is-ancestor',commit,'origin/'+branch],cwd=ROOT,check=True)
    return commit

def prepare():
    PLAN.mkdir(parents=True,exist_ok=True)
    identities={}
    for p,h in [(DATA,V1['dataset']['sha256']),(TARGET,V1['target']['sha256']),(DRAFT,V1['draft']['sha256'])]:
        actual=sha(p);assert actual==h,(str(p),'asset mismatch');identities[p.name]=actual
    binaries={}
    for p in RUNTIME.glob('*.dll'):
        h=sha(p);assert h==V1['binary_hashes'][p.name],p.name
        shutil.copy2(p,EXE.parent/p.name);binaries[p.name]=h
    binaries[EXE.name]=sha(EXE)
    pinned=Path('C:/hs/b570-direct-id-v1-src')
    original=LOCAL/'work/b570_direct_id_v1/upstream/llama.cpp-0cae43063cf15170e91a2ff4d034da0ecef4a1b2'
    source_identity={};changes=[]
    for base in ('common','include','src','ggml/include','ggml/src','vendor/nlohmann'):
        for p in (pinned/base).rglob('*'):
            if p.is_file() and p.suffix in ('.cpp','.c','.h','.hpp'):
                rel=p.relative_to(pinned).as_posix();h=sha(p);source_identity[rel]=h
                if not (original/rel).exists() or sha(original/rel)!=h:changes.append(rel)
    # Historical instrumentation alters completion and speculative, not the core libraries.
    assert changes==['common/heterospec-direct-id.h'],changes
    source_identity['examples/speculative/speculative.cpp']=sha(pinned/'examples/speculative/speculative.cpp')
    manifest={'study':'B570_LIVE_PARTITION_INTERVENTION_V1','created_utc':utc(),
        'starting_main':git('rev-parse','origin/main'),'worktree':str(ROOT),'branch':git('branch','--show-current'),
        'upstream_commit':V1['upstream_commit'],'build_number':10839,'environment':env_identity(),
        'assets':identities,'binaries':binaries,'pinned_source_files':source_identity,
        'source_deviations':changes,'static_libraries':{str(p):sha(p) for p in Path('C:/hs/b570-direct-id-v1-build').rglob('*.lib')},
        'new_frontend_files':{p.name:sha(p) for p in SRC.iterdir() if p.is_file()},
        'historical_environment_inherited':False,'new_qualification_required':True,
        'offload_required':{'target':'37/37 Vulkan0 B570','draft':'29/29 Vulkan0 B570'}}
    save(PLAN/'BUILD_IDENTITY.json',manifest)
    print('New runtime/source/model/environment identity archived; no inference.',flush=True)

def check():
    m=read(PLAN/'BUILD_IDENTITY.json')
    assert env_identity()==m['environment'],'environment drift requires new qualification and freeze'
    for n,h in m['binaries'].items(): assert sha(EXE.parent/n)==h,n
    for n,h in m['new_frontend_files'].items(): assert sha(SRC/n)==h,n
    for p,h in [(DATA,m['assets'][DATA.name]),(TARGET,m['assets'][TARGET.name]),(DRAFT,m['assets'][DRAFT.name])]:assert sha(p)==h
    return m

def command(exe,prompt):
    return [str(exe),'--model',str(TARGET),'--device','Vulkan0','--n-gpu-layers','all','--fit','off',
        '--ctx-size','1024','--batch-size','512','--ubatch-size','1','--flash-attn','off',
        '--file',str(prompt),'--n-predict','127','--temp','0','--top-k','0','--top-p','1','--min-p','0',
        '--seed','123','--verbose','--spec-type','draft-simple','--spec-draft-model',str(DRAFT),
        '--spec-draft-device','Vulkan0','--spec-draft-ngl','all','--spec-draft-n-max','2','--spec-draft-n-min','0']

def execute(stage,task,rep,mode):
    directory=RAW/stage/(task.replace('/','_')+f'-r{rep}-{mode}')
    assert not directory.exists(),'No selective restart/replacement'
    directory.mkdir(parents=True)
    with gzip.open(DATA,'rt',encoding='utf-8') as f: ds={r['task_id']:r for r in map(json.loads,f)}
    prompt=directory/'prompt.txt';prompt.write_text(PREFIX+ds[task]['prompt'],encoding='utf-8',newline='\n')
    exe=RUNTIME/'llama-speculative.exe' if mode=='original' else EXE
    cmd=command(exe,prompt);en=os.environ.copy()
    en['HETEROSPEC_DIRECT_ID_PATH']=str(directory/'ids.json')
    en['HS_PARTITION_MODE']=mode;en['HS_PARTITION_OUTPUT']=str(directory/'capture.json')
    start={'task_id':task,'repetition':rep,'mode':mode,'stage':stage,'start_utc':utc(),'study_head':git('rev-parse','HEAD'),
        'command':cmd,'prompt_sha256':sha(prompt),'identity_sha256':sha(PLAN/'BUILD_IDENTITY.json')}
    save(directory/'start.json',start)
    try:
        with (directory/'stdout.txt').open('wb') as out,(directory/'stderr.txt').open('wb') as err:
            proc=subprocess.run(cmd,env=en,stdout=out,stderr=err,timeout=1800)
        rc=proc.returncode
    except Exception as ex:
        rc=-1;start['exception']=repr(ex)
    start.update(end_utc=utc(),exit_code=rc)
    text=(directory/'stderr.txt').read_text(encoding='utf-8',errors='replace')
    placements=[s for s in text.splitlines() if 'using device ' in s]
    offloads=re.findall(r'offloaded\s+(\d+)/(\d+) layers to GPU',text)
    valid=rc==0 and offloads==[('37','37'),('29','29')] and len(placements)==2 and all('using device Vulkan0 (Intel(R) Arc(TM) B570 Graphics)' in s for s in placements)
    start['placements']=placements;start['offloads']=offloads
    if (directory/'ids.json').exists():
        d=read(directory/'ids.json')
        try: start['generated_ids']=semantic(d['ids'],d['eog'])
        except Exception as ex:valid=False;start['endpoint_error']=repr(ex)
    else:valid=False
    capture=directory/'capture.json'
    if mode!='original':
        if capture.exists():
            d=read(capture)
            valid &= not d['failure'] and d['exit_code']==0 and d['primary_ids']==read(directory/'ids.json')['ids'] if (directory/'ids.json').exists() else False
            start['forked']=d['forked']
            if mode!='baseline' and d['forked']:
                try: semantic(d['alternate_ids'],d['alternate_eog'])
                except Exception:valid=False
            elif mode!='baseline' and len(start.get('generated_ids',[]))>=64:valid=False
        else:valid=False
    # Deduplicate identical serialized KV bytes by SHA256, while retaining logical identities.
    states={}
    for p in directory.glob('capture.json.*.kv'):
        digest=sha(p);dest=directory/(digest+'.kv.gz')
        if not dest.exists():
            with p.open('rb') as src,gzip.open(dest,'wb',compresslevel=1) as out:shutil.copyfileobj(src,out)
        states[p.name]={'sha256':digest,'bytes':p.stat().st_size,'compressed':dest.name};p.unlink()
    start['state_objects']=states;start['execution_valid']=bool(valid)
    start['files']={p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in directory.iterdir() if p.is_file() and p.name!='record.json'}
    save(directory/'record.json',start)
    print(stage,task,'r'+str(rep),mode,'valid='+str(valid),flush=True)
    return start,directory

def qualify():
    check();commit=checkpoint_pushed(PLAN/'ENGINEERING_PLAN.md')
    assert not (RAW/'r0').exists(),'R0 already started'
    results=[];passed=True
    for task in TASKS:
        rows={}
        for mode in ('original','baseline','control','intervention'):
            row,directory=execute('r0',task,1,mode);rows[mode]=(row,directory)
            if not row['execution_valid']:
                results.append({'task_id':task,'pass':False,'reason':'operational/endpoint/fork failure','mode':mode});passed=False;break
        if not passed:break
        original=rows['original'][0]['generated_ids'];baseline=read(rows['baseline'][1]/'capture.json')
        control=read(rows['control'][1]/'capture.json');pair=read(rows['intervention'][1]/'capture.json')
        checks={'new_original_baseline_ids_equal':original==rows['baseline'][0]['generated_ids'],
            'new_original_control_ids_equal':original==rows['control'][0]['generated_ids'],
            'new_original_intervention_primary_ids_equal':original==rows['intervention'][0]['generated_ids'],
            'all_native_proposal_tapes_equal':baseline['proposal_events']==control['proposal_events']==pair['proposal_events'],
            'control_full_continuation_ids_equal':control['primary_ids']==control['alternate_ids'],
            'control_full_raw_checkpoint_scores_equal':control['primary_scores']==control['alternate_scores'],
            'control_fork_exists':control['forked'],'intervention_fork_exists':pair['forked'],
            'control_state_equal':control['checkpoint']['serialized_kv_equal'] and control['checkpoint']['source_unchanged'],
            'intervention_state_equal':pair['checkpoint']['serialized_kv_equal'] and pair['checkpoint']['source_unchanged'],
            'native_physical_ub1': [r['output_tokens'] for r in pair['primary_physical_graphs']]==[1,1,1],
            'alternate_physical_ub128': [r['output_tokens'] for r in pair['alternate_physical_graphs']]==[3]}
        results.append({'task_id':task,'checks':checks,'pass':all(checks.values())})
        if not all(checks.values()):passed=False;break
    status='PASS' if passed else 'INTERVENTION_NOT_FEASIBLE'
    report={'status':status,'engineering_freeze_commit':commit,'created_utc':utc(),'results':results,
        'planned_tasks':TASKS,'attempted_executions':len(list((RAW/'r0').glob('*/start.json'))),'reserved_executions':0,
        'failure_policy':'First R0 failure terminates study; no repair/requalification to rescue V1.'}
    save(PLAN/'TECHNICAL_QUALIFICATION.json',report)
    (PLAN/'TECHNICAL_QUALIFICATION.md').write_text('# Same-state technical qualification\n\n**'+status+'**.\n\n'+json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(status,flush=True)

def freeze():
    assert read(PLAN/'TECHNICAL_QUALIFICATION.json')['status']=='PASS'
    check();audit=read(PLAN/'EXPOSURE_AUDIT.json');assert not audit['errors']
    reserved=read(PLAN/'RESERVED_SET.json');assert len(reserved['task_ids'])==24
    frozen={'created_utc':utc(),'study':'B570_LIVE_PARTITION_INTERVENTION_V1',
        'starting_main':git('rev-parse','origin/main'),'task_ids':reserved['task_ids'],'repetitions':3,
        'schedule':[{'task_id':t,'repetition':r} for r in (1,2,3) for t in reserved['task_ids']],
        'checkpoint_rule':'One sampled checkpoint: first native verification batch whose starting committed-ID count is >=64. If inclusive EOG ends earlier, no eligible checkpoint. No other checkpoint selection.',
        'primary_endpoint':'All target decisions reachable within the sampled fixed-proposal verification block until first rejection/bonus or endpoint; first different decision at a still-common proposal-conditioned prefix. Count both prompt and execution units.',
        'secondary_endpoint':'Entire primary and alternate native live-loop committed-ID trajectories up to 128 IDs/inclusive EOG; alternate drafting after intervention is a downstream consequence.',
        'identity_sha256':sha(PLAN/'BUILD_IDENTITY.json'),'qualification_sha256':sha(PLAN/'TECHNICAL_QUALIFICATION.json'),
        'exposure_sha256':sha(PLAN/'EXPOSURE_AUDIT.json'),'reserved_set_sha256':sha(PLAN/'RESERVED_SET.json'),
        'source_files':{p.name:sha(p) for p in SRC.iterdir() if p.is_file()},
        'failure_policy':'Any operation/state/offload/provenance failure immediately stops formal interpretation and retains all attempts; no replacements.',
        'proposal_rule':'Live draft UB1 k2 tape already complete and recorded before either target decode; cloned target samplers. No future branch proposals enter paired block.',
        'no_performance_or_energy':True,'no_parameter_search':True}
    save(PLAN/'FORMAL_FREEZE.json',frozen)
    print('Formal freeze ready; commit and push before reserved inference.',flush=True)

def formal():
    assert read(PLAN/'TECHNICAL_QUALIFICATION.json')['status']=='PASS'
    check();f=read(PLAN/'FORMAL_FREEZE.json');commit=checkpoint_pushed(PLAN/'FORMAL_FREEZE.json')
    assert sha(PLAN/'BUILD_IDENTITY.json')==f['identity_sha256']
    assert not (RAW/'reserved').exists()
    save(PLAN/'FORMAL_EXECUTION.json',{'status':'RUNNING','freeze_commit':commit,'start_utc':utc(),'executions':[]})
    rows=[]
    for item in f['schedule']:
        row,_=execute('reserved',item['task_id'],item['repetition'],'intervention');rows.append(row)
        status='RUNNING' if row['execution_valid'] else 'FORMAL_OPERATIONAL_FAILURE'
        save(PLAN/'FORMAL_EXECUTION.json',{'status':status,'freeze_commit':commit,'executions':rows,'updated_utc':utc()})
        if not row['execution_valid']:return
    save(PLAN/'FORMAL_EXECUTION.json',{'status':'EXECUTION_COMPLETE','freeze_commit':commit,'executions':rows,'finished_utc':utc()})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['prepare','qualify','freeze','formal']);a=p.parse_args()
    globals()[a.stage]()
