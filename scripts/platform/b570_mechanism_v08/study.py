"""Stage-gated execution for the frozen B570 mechanism protocol."""
import argparse, gzip, hashlib, json, os, re, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

REPO=Path(__file__).resolve().parents[3]
PROTOCOL=REPO/'benchmarks/b570_mechanism_v08'
RAW=REPO/'artifacts/b570_mechanism_v08/raw'
EXE=Path('C:/hs/b570-mechanism-v08-build/Release/heterospec-mechanism.exe')
OLD=REPO/'work/b570_direct_id_v1/formal-v1-20260929-local/executions.json'
PREFIX='Complete the following Python function. Return only the completed Python code, without Markdown fences.\n\n'
TARGET=REPO/'models/gguf/Qwen3-8B-Q8_0.gguf'
DRAFT=REPO/'models/gguf/Qwen3-0.6B-Q8_0.gguf'
DATA=REPO/'datasets/humaneval/HumanEval.jsonl.gz'
V1=json.loads((REPO/'benchmarks/b570_direct_id_v1/protocol_v1.json').read_text(encoding='utf-8'))
DISC=json.loads((PROTOCOL/'discovery_protocol.json').read_text(encoding='utf-8'))

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
def array_sha(ids):return hashlib.sha256(json.dumps(ids,separators=(',',':')).encode()).hexdigest()
def utc():return datetime.now(timezone.utc).isoformat()
def save(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8');tmp.replace(path)
def head():return subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def compare(a,b):
    i=next((i for i,(x,y) in enumerate(zip(a,b)) if x!=y),None)
    if i is None and len(a)!=len(b):i=min(len(a),len(b))
    return {'exact':i is None,'first_divergence_index':i,'reference_token':a[i] if i is not None and i<len(a) else None,'candidate_token':b[i] if i is not None and i<len(b) else None,'reference_length':len(a),'candidate_length':len(b)}
def assets():
    expected={TARGET:V1['target']['sha256'],DRAFT:V1['draft']['sha256'],DATA:V1['dataset']['sha256']}
    for p,h in expected.items():
        if sha(p)!=h:raise RuntimeError('Asset SHA mismatch: '+str(p))
    return {str(p.relative_to(REPO)):h for p,h in expected.items()}
def prepare_build():
    identity=assets()
    binaries={}
    for p in Path('C:/hs/b570-direct-id-v1-build/bin/Release').glob('*.dll'):
        if sha(p)!=V1['binary_hashes'][p.name]:raise RuntimeError('Frozen runtime DLL mismatch')
        shutil.copy2(p,EXE.parent/p.name);binaries[p.name]=sha(p)
    binaries[EXE.name]=sha(EXE)
    pinned=Path('C:/hs/b570-direct-id-v1-src')
    original=REPO/'work/b570_direct_id_v1/upstream/llama.cpp-0cae43063cf15170e91a2ff4d034da0ecef4a1b2'
    headers={}
    for base in ('common','include','ggml/include','vendor/nlohmann','vendor/sheredom'):
        for p in (pinned/base).rglob('*'):
            if p.is_file() and p.suffix in ('.h','.hpp','.cpp') and p.name!='heterospec-direct-id.h':
                rel=p.relative_to(pinned)
                if not (original/rel).exists() or sha(p)!=sha(original/rel):raise RuntimeError('Pinned source mismatch '+str(rel))
                headers[str(rel).replace('\\','/')]=sha(p)
    libs={str(p):sha(p) for p in Path('C:/hs/b570-direct-id-v1-build').rglob('*.lib')}
    env=json.loads(subprocess.check_output(['powershell.exe','-NoProfile','-Command',"[Console]::OutputEncoding=[Text.UTF8Encoding]::new(); [ordered]@{os=(Get-CimInstance Win32_OperatingSystem|Select-Object Caption,Version,BuildNumber);gpu=@(Get-CimInstance Win32_VideoController|Select-Object Name,DriverVersion,PNPDeviceID);vulkan_runtime=(Get-Item C:\\Windows\\System32\\vulkan-1.dll).VersionInfo.FileVersion}|ConvertTo-Json -Depth 6"],encoding='utf-8-sig'))
    manifest={'schema':'heterospec.b570.mechanism.build.v08','created_utc':utc(),'upstream_commit':V1['upstream_commit'],'build_number':10839,'linked_source_verified_against_upstream_archive':True,'source_file_hashes':headers,'static_import_library_hashes':libs,'binary_hashes':binaries,'assets':identity,'environment':env,'harness_source_sha256':sha(Path(__file__).parent/'harness.cpp'),'cmake_source_sha256':sha(Path(__file__).parent/'CMakeLists.txt'),'historical_executions_sha256':sha(OLD),'historical_reference_count':90}
    save(PROTOCOL/'build_manifest.json',manifest)
    print('Build provenance PASS; no inference executed.',flush=True)
def check_build():
    m=read(PROTOCOL/'build_manifest.json')
    for name,h in m['binary_hashes'].items():
        if sha(EXE.parent/name)!=h:raise RuntimeError('Runtime changed: '+name)
    if sha(Path(__file__).parent/'harness.cpp')!=m['harness_source_sha256']:raise RuntimeError('Harness source changed')
    if sha(OLD)!=m['historical_executions_sha256']:raise RuntimeError('Historical evidence changed')
    return m
def command(prompt,ubatch):
    return [str(EXE),'--model',str(TARGET),'--device','Vulkan0','--n-gpu-layers','all','--fit','off','--ctx-size','1024','--batch-size','512','--ubatch-size',str(ubatch),'--flash-attn','off','--file',str(prompt),'--n-predict','128','--temp','0','--top-k','0','--top-p','1','--min-p','0','--seed','123','--reasoning','off','--simple-io','--no-warmup','--log-verbosity','4','--no-conversation']
def execute(stage,task,rep,ubatch,rows):
    directory=RAW/stage;directory.mkdir(parents=True,exist_ok=True)
    stem=task.replace('/','_')+f'-r{rep}-ub{ubatch}'
    capture=directory/(stem+'.capture.json')
    if capture.exists() or (directory/(stem+'.start.json')).exists():raise RuntimeError('No selective rerun: '+stem)
    with gzip.open(DATA,'rt',encoding='utf-8') as f:dataset={r['task_id']:r for r in map(json.loads,f)}
    prompt=directory/(task.replace('/','_')+'.prompt.txt')
    prompt.write_text(PREFIX+dataset[task]['prompt'],encoding='utf-8',newline='\n')
    input_ids=directory/(task.replace('/','_')+'.prompt_ids.json')
    env=os.environ.copy();env['HS_MECHANISM_OUTPUT']=str(capture);env.pop('HS_MECHANISM_INPUT_IDS',None);env.pop('HETEROSPEC_DIRECT_ID_PATH',None)
    if input_ids.exists():env['HS_MECHANISM_INPUT_IDS']=str(input_ids)
    cmd=command(prompt,ubatch)
    row={'stage':stage,'task_id':task,'repetition':rep,'n_ubatch':ubatch,'study_head':head(),'start_utc':utc(),'command':cmd,'env_overrides':{k:env[k] for k in ('HS_MECHANISM_OUTPUT','HS_MECHANISM_INPUT_IDS') if k in env},'prompt_sha256':sha(prompt)}
    save(directory/(stem+'.start.json'),row)
    stdout=directory/(stem+'.stdout.txt');stderr=directory/(stem+'.stderr.txt')
    with stdout.open('wb') as out,stderr.open('wb') as err:
        proc=subprocess.run(cmd,env=env,stdout=out,stderr=err,timeout=900)
    row.update(end_utc=utc(),exit_code=proc.returncode,stdout=str(stdout.relative_to(REPO)).replace('\\','/'),stderr=str(stderr.relative_to(REPO)).replace('\\','/'),stdout_sha256=sha(stdout),stderr_sha256=sha(stderr))
    text=stderr.read_text(encoding='utf-8',errors='replace')
    off=re.findall(r'offloaded\s+(\d+)/(\d+) layers to GPU',text)
    place=[line for line in text.splitlines() if 'using device ' in line]
    row['placement_evidence']=[line for line in text.splitlines() if 'using device ' in line or 'offloaded ' in line]
    row['execution_valid']=proc.returncode==0 and off==[('37','37')] and len(place)==1 and 'using device Vulkan0 (Intel(R) Arc(TM) B570 Graphics)' in place[0]
    if capture.exists():
        data=read(capture);ids=data['generated_ids'];flags=data['eog']
        valid=0<len(ids)<=128 and len(ids)==len(flags) and all(type(i)==int and i>=0 for i in ids) and (len(ids)==128 or flags[-1]) and not any(flags[:-1])
        row.update(capture=str(capture.relative_to(REPO)).replace('\\','/'),capture_sha256=sha(capture),generated_ids=ids,generated_ids_sha256=array_sha(ids),prompt_ids_sha256=array_sha(data['prompt_ids']),context=data['context'])
        if input_ids.exists():valid=valid and read(input_ids)==data['prompt_ids']
        else:save(input_ids,data['prompt_ids'])
        valid=valid and len(data['decisions'])==len(ids) and data['context']['n_ubatch']==ubatch and data['context']['n_ctx']==1024 and data['context']['n_batch']==512
        row['execution_valid'] &= valid
    else:row['execution_valid']=False
    rows.append(row);save(directory/'executions.json',{'schema':'heterospec.b570.mechanism.executions.v08','executions':rows})
    print(f'{stage} {len(rows)}: {task} r{rep} valid={row["execution_valid"]}',flush=True)
    return row
def qualify():
    check_build();assets()
    if (RAW/'qualification/executions.json').exists():raise RuntimeError('Qualification already started')
    old=read(OLD)['executions'];by={(r['task_id'],r['repetition'],r['condition']):r for r in old}
    rows=[];pairs=[]
    for rep in range(1,4):
        for task in V1['task_ids']:
            row=execute('qualification',task,rep,128,rows)
            ref=by[(task,rep,'TARGET_REFERENCE')]
            result=compare(ref['generated_ids'],row.get('generated_ids',[]));result.update(task_id=task,repetition=rep,execution_valid=row['execution_valid'],reference_sha256=ref['generated_ids_sha256'],harness_sha256=row.get('generated_ids_sha256'))
            pairs.append(result)
            save(PROTOCOL/'HARNESS_QUALIFICATION.json',{'status':'RUNNING','pairs':pairs,'expected':90})
            if not row['execution_valid'] or not result['exact']:
                finish_qualification(rows,pairs,False);return
    finish_qualification(rows,pairs,True)
def finish_qualification(rows,pairs,passed):
    status='PASS' if passed else 'HARNESS_NOT_QUALIFIED'
    save(PROTOCOL/'HARNESS_QUALIFICATION.json',{'status':status,'expected':90,'executions':len(rows),'exact_pairs':sum(r['exact'] and r['execution_valid'] for r in pairs),'pairs':pairs,'finished_utc':utc(),'reserved_executions':0})
    failures=[r for r in pairs if not r['exact'] or not r['execution_valid']]
    (PROTOCOL/'HARNESS_QUALIFICATION_REPORT.md').write_text('# Common harness qualification\n\n'+f'Status: **{status}**. Completed {len(rows)}/90 planned observations; exact valid sequences {sum(r["exact"] and r["execution_valid"] for r in pairs)}/{len(pairs)}.\n\n'+('All 30 historical target trajectories reproduced across three repetitions. Discovery may begin only after committing this result.\n' if passed else 'Stopped at the first failed qualification observation as preregistered. No discovery or reserved inference is permitted.\n\nFailure details:\n\n```json\n'+json.dumps(failures,indent=2)+'\n```\n'),encoding='utf-8')
    print(status,flush=True)
def discover():
    if read(PROTOCOL/'HARNESS_QUALIFICATION.json')['status']!='PASS':raise RuntimeError('Harness not qualified')
    check_build();assets()
    if (RAW/'discovery_h1/executions.json').exists():raise RuntimeError('Discovery already started')
    old=read(OLD)['executions'];by={(r['task_id'],r['repetition'],r['condition']):r for r in old}
    rows=[];pairs=[]
    for rep in range(1,4):
        for task in DISC['tasks']:
            row=execute('discovery_h1',task,rep,1,rows)
            serialized=by[(task,rep,'B570_SERIALIZED_K2')]['generated_ids'];ref=by[(task,rep,'TARGET_REFERENCE')]['generated_ids']
            result=compare(serialized,row.get('generated_ids',[]));result.update(task_id=task,repetition=rep,execution_valid=row['execution_valid'],relative_to_reference=compare(ref,row.get('generated_ids',[])),historical_serialized_relative_to_reference=compare(ref,serialized))
            pairs.append(result)
            if not row['execution_valid']:raise RuntimeError('Operational discovery failure; retain and stop')
    count=sum(r['exact'] for r in pairs);selected='H1_SELECTED' if count==36 else 'H1_FAILED_EVALUATE_H2'
    save(PROTOCOL/'DISCOVERY_ANALYSIS.json',{'status':selected,'H1_exact_pairs':count,'denominator':36,'pairs':pairs,'finished_utc':utc(),'reserved_executions':0})
    (PROTOCOL/'DISCOVERY_REPORT.md').write_text('# Exploratory discovery\n\n'+f'H1: {count}/36 complete predictor-to-archived serialized sequences. Decision: {selected}.\n\nThe 12 discovery prompts are exposed and outcome-informed; this is no evidence of transfer.\n',encoding='utf-8')
    print(selected,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['prepare-build','qualify','discover']);a=p.parse_args()
    {'prepare-build':prepare_build,'qualify':qualify,'discover':discover}[a.stage]()
