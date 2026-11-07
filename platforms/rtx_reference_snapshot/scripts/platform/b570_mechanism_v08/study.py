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
def git(*args):return subprocess.check_output(['git',*args],cwd=REPO)
def committed_and_pushed(path):
    rel=str(Path(path).relative_to(REPO)).replace('\\','/')
    commit=git('log','-1','--format=%H','--',rel).decode().strip()
    if not commit or git('show',commit+':'+rel)!=Path(path).read_bytes():raise RuntimeError('Required immutable checkpoint not committed: '+rel)
    branch=git('branch','--show-current').decode().strip()
    git('fetch','origin',branch)
    if subprocess.run(['git','merge-base','--is-ancestor',commit,'origin/'+branch],cwd=REPO).returncode:raise RuntimeError('Required checkpoint not pushed')
    return commit
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def environment():
    return json.loads(subprocess.check_output(['powershell.exe','-NoProfile','-Command',"[Console]::OutputEncoding=[Text.UTF8Encoding]::new(); [ordered]@{os=(Get-CimInstance Win32_OperatingSystem|Select-Object Caption,Version,BuildNumber);gpu=@(Get-CimInstance Win32_VideoController|Select-Object Name,DriverVersion,PNPDeviceID);vulkan_runtime=(Get-Item C:\\Windows\\System32\\vulkan-1.dll).VersionInfo.FileVersion}|ConvertTo-Json -Depth 6"],encoding='utf-8-sig'))
def compare(a,b):
    i=next((i for i,(x,y) in enumerate(zip(a,b)) if x!=y),None)
    if i is None and len(a)!=len(b):i=min(len(a),len(b))
    return {'exact':i is None,'first_divergence_index':i,'reference_token':a[i] if i is not None and i<len(a) else None,'candidate_token':b[i] if i is not None and i<len(b) else None,'reference_length':len(a),'candidate_length':len(b)}
def assets():
    expected={TARGET:V1['target']['sha256'],DRAFT:V1['draft']['sha256'],DATA:V1['dataset']['sha256']}
    for p,h in expected.items():
        if sha(p)!=h:raise RuntimeError('Asset SHA mismatch: '+str(p))
    return {str(p.relative_to(REPO)).replace('\\','/'):h for p,h in expected.items()}
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
    if environment()!=m['environment']:raise RuntimeError('OS/driver/Vulkan stack changed')
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

def freeze_h1():
    result=read(PROTOCOL/'DISCOVERY_ANALYSIS.json')
    if result['status']!='H1_SELECTED' or result['H1_exact_pairs']!=36:raise RuntimeError('H1 not selected')
    if (PROTOCOL/'hypothesis_freeze.json').exists():raise RuntimeError('Hypothesis freeze already exists')
    check_build();identity=assets();build=read(PROTOCOL/'build_manifest.json')
    frozen={'schema':'heterospec.b570.mechanism.hypothesis.v08','status':'H1_SELECTED','created_utc':utc(),
      'source_sha':V1['upstream_commit'],'study_repository_head_before_freeze':head(),'harness_source_sha256':sha(Path(__file__).parent/'harness.cpp'),
      'executable_sha256':sha(EXE),'binary_hashes':build['binary_hashes'],'model_dataset_hashes':identity,
      'driver_and_vulkan':build['environment'],'prediction_algorithm':'Common target-only autoregressive greedy decoding with n_ubatch=1; prefill/decode APIs, sampler, context, input IDs and all other semantics identical to qualified UB128 reference.',
      'comparison_orientation':'TARGET_REFERENCE vs predicted serialized IDs; primary predicted IDs vs actual serialized IDs',
      'output_cap':128,'eog':'inclusive first runtime EOG, earlier than 128 if present','repetitions':3,
      'reserved_task_ids':read(PROTOCOL/'RESERVED_VALIDATION_SET.json')['selected_task_ids'],
      'predictor_files':{str(p.relative_to(REPO)).replace('\\','/'):sha(p) for p in [Path(__file__).parent/name for name in ('harness.cpp','CMakeLists.txt','study.py')]},
      'serialized_binary_hashes':V1['binary_hashes'],
      'serialized_runner_sha256':sha(REPO/'scripts/platform/b570_direct_id_v1/common.py'),
      'success_criterion':'72/72 complete predictor-to-actual direct-ID sequences','failure_handling':'Repeat instability stops before live outcomes as operationally ambiguous; mismatches continue without tuning or selective rerun; fewer than 72 exact closes not fully validated.',
      'confidence_intervals':False,'no_performance_or_energy':True,'discovery_result_sha256':sha(PROTOCOL/'DISCOVERY_ANALYSIS.json')}
    save(PROTOCOL/'hypothesis_freeze.json',frozen)
    (PROTOCOL/'HYPOTHESIS_FREEZE.md').write_text('# Hypothesis freeze\n\n**H1_SELECTED**. Target execution partition alone reproduced 36/36 archived serialized discovery sequences.\n\n'+f'Created before all reserved inference: {frozen["created_utc"]}.\n\n'+frozen['prediction_algorithm']+'\n\nAll predictor source/executable/runtime/model/dataset identities, driver and Vulkan runtime, 24 reserved tasks, three repetitions, comparison orientation, cap/EOG endpoint and strict 72/72 decision rule are frozen in hypothesis_freeze.json. No confidence intervals. No predictor changes after this checkpoint. Commit and push before reserved inference.\n',encoding='utf-8')
def check_hypothesis():
    frozen=read(PROTOCOL/'hypothesis_freeze.json')
    if frozen['status']!='H1_SELECTED':raise RuntimeError('Unsupported selected predictor')
    for path,h in frozen['predictor_files'].items():
        if sha(REPO/path)!=h:raise RuntimeError('Frozen predictor source changed: '+path)
    check_build();assets()
    return frozen,committed_and_pushed(PROTOCOL/'hypothesis_freeze.json')
def predict_reserved():
    frozen,freeze_commit=check_hypothesis()
    if (RAW/'reserved_predictions/executions.json').exists() or (RAW/'reserved_outcomes').exists():raise RuntimeError('No restart or outcome leakage permitted')
    save(RAW/'reserved_predictions/checkpoint.json',{'hypothesis_freeze_commit':freeze_commit,'hypothesis_sha256':sha(PROTOCOL/'hypothesis_freeze.json'),'start_utc':utc()})
    rows=[];predictions=[];by={}
    for rep in range(1,4):
        for task in frozen['reserved_task_ids']:
            for ub in (128,1):
                row=execute('reserved_predictions',task,rep,ub,rows);row['condition']='TARGET_REFERENCE' if ub==128 else 'MECHANISM_PREDICTOR'
                by[(task,rep,ub)]=row
                save(RAW/'reserved_predictions/executions.json',{'schema':'heterospec.b570.mechanism.executions.v08','executions':rows})
                if not row['execution_valid']:raise RuntimeError('Reserved operational failure; preserve and stop before outcomes')
            ref=by[(task,rep,128)]['generated_ids'];pred=by[(task,rep,1)]['generated_ids']
            predictions.append({'task_id':task,'repetition':rep,'predicted_ids':pred,'predicted_ids_sha256':array_sha(pred),'reference_ids':ref,'reference_ids_sha256':array_sha(ref),'relative_to_reference':compare(ref,pred)})
    stable=all(len({r['generated_ids_sha256'] for r in rows if r['task_id']==task and r['n_ubatch']==ub})==1 for task in frozen['reserved_task_ids'] for ub in (128,1))
    status='PREDICTIONS_READY' if stable else 'OPERATIONALLY_AMBIGUOUS_REPEAT_INSTABILITY'
    save(PROTOCOL/'RESERVED_PREDICTIONS.json',{'schema':'heterospec.b570.mechanism.predictions.v08','status':status,'created_utc':utc(),'hypothesis_freeze_commit':freeze_commit,'hypothesis_sha256':sha(PROTOCOL/'hypothesis_freeze.json'),'prediction_count':72,'predictor_reference_executions':144,'repeat_stable':stable,'predictions':predictions,'actual_serialized_outcomes_observed':False})
    (PROTOCOL/'RESERVED_PREDICTIONS_SHA256.txt').write_text(sha(PROTOCOL/'RESERVED_PREDICTIONS.json')+'  RESERVED_PREDICTIONS.json\n',encoding='ascii')
    print(status+'; commit and push predictions before outcomes.',flush=True)
def actual_reserved():
    frozen,freeze_commit=check_hypothesis();prediction=read(PROTOCOL/'RESERVED_PREDICTIONS.json')
    if prediction['status']!='PREDICTIONS_READY' or not prediction['repeat_stable']:raise RuntimeError('Prediction phase not valid and stable')
    if sha(REPO/'scripts/platform/b570_direct_id_v1/common.py')!=frozen['serialized_runner_sha256']:raise RuntimeError('Serialized execution source changed')
    for name,h in frozen['serialized_binary_hashes'].items():
        if sha(Path('C:/hs/b570-direct-id-v1-build/bin/Release')/name)!=h:raise RuntimeError('Frozen serialized runtime changed')
    prediction_commit=committed_and_pushed(PROTOCOL/'RESERVED_PREDICTIONS.json')
    if (RAW/'reserved_outcomes').exists():raise RuntimeError('Outcomes already started; no selective rerun')
    digest=sha(PROTOCOL/'RESERVED_PREDICTIONS.json')
    if (PROTOCOL/'RESERVED_PREDICTIONS_SHA256.txt').read_text().split()[0]!=digest:raise RuntimeError('Prediction freeze digest mismatch')
    save(RAW/'reserved_outcomes/checkpoint.json',{'start_utc':utc(),'hypothesis_freeze_commit':freeze_commit,'prediction_commit':prediction_commit,'prediction_sha256':digest,'hypothesis_sha256':sha(PROTOCOL/'hypothesis_freeze.json')})
    sys.path.insert(0,str(REPO/'scripts/platform/b570_direct_id_v1'))
    import common as historical_runner
    rows=[]
    for rep in range(1,4):
        for task in frozen['reserved_task_ids']:
            if sha(PROTOCOL/'RESERVED_PREDICTIONS.json')!=digest:raise RuntimeError('Predictions changed after outcome start')
            prompt=RAW/'reserved_predictions'/(task.replace('/','_')+'.prompt.txt')
            cmd=historical_runner.command(historical_runner.INSTRUMENTED,TARGET,DRAFT,prompt,'B570_SERIALIZED_K2')
            row=historical_runner.execute(RAW/'reserved_outcomes',task.replace('/','_')+f'-r{rep}',cmd)
            row.update(stage='reserved_outcomes',task_id=task,repetition=rep,condition='B570_SERIALIZED_K2',study_head=head(),prediction_commit=prediction_commit,hypothesis_freeze_commit=freeze_commit,prediction_sha256=digest)
            row['env_overrides']={'HETEROSPEC_DIRECT_ID_PATH':str(RAW/'reserved_outcomes'/'ids'/(task.replace('/','_')+f'-r{rep}.json'))}
            rows.append(row);save(RAW/'reserved_outcomes/executions.json',{'schema':'heterospec.b570.mechanism.executions.v08','executions':rows})
            print(f'reserved_outcomes {len(rows)}/72: {task} r{rep} valid={row["execution_valid"]}',flush=True)
            if not row['execution_valid']:raise RuntimeError('Invalid outcome execution; preserve attempt and stop without selective rerun')
    check_build()
    save(PROTOCOL/'POST_RUN_INPUT_AUDIT.json',{'checked_utc':utc(),'model_dataset_hashes':assets(),'binary_hashes':{p.name:sha(p) for p in EXE.parent.glob('*') if p.suffix.lower() in ('.exe','.dll')},'serialized_binary_hashes':{p.name:sha(p) for p in Path('C:/hs/b570-direct-id-v1-build/bin/Release').glob('*') if p.suffix.lower() in ('.exe','.dll')},'environment':environment(),'prediction_file_sha256':sha(PROTOCOL/'RESERVED_PREDICTIONS.json')})
    analyze_reserved()
def analyze_reserved():
    predictions=read(PROTOCOL/'RESERVED_PREDICTIONS.json')['predictions'];outcomes=read(RAW/'reserved_outcomes/executions.json')['executions'];pairs=[]
    by={(r['task_id'],r['repetition']):r for r in outcomes}
    for prediction in predictions:
        actual=by[(prediction['task_id'],prediction['repetition'])]['generated_ids']
        pair={'task_id':prediction['task_id'],'repetition':prediction['repetition'],'primary':compare(prediction['predicted_ids'],actual),'actual_relative_to_reference':compare(prediction['reference_ids'],actual),'predicted_relative_to_reference':prediction['relative_to_reference']}
        pairs.append(pair)
    exact=sum(p['primary']['exact'] for p in pairs)
    tasks=read(PROTOCOL/'RESERVED_VALIDATION_SET.json')['selected_task_ids']
    classification=sum(all(p['actual_relative_to_reference']['exact']==p['predicted_relative_to_reference']['exact'] for p in pairs if p['task_id']==task) for task in tasks)
    differing=[p for p in pairs if not p['actual_relative_to_reference']['exact']]
    first=sum(p['actual_relative_to_reference']['first_divergence_index']==p['predicted_relative_to_reference']['first_divergence_index'] for p in differing)
    prompt_trajectories=sum(all(p['primary']['exact'] for p in pairs if p['task_id']==task) for task in tasks)
    predicted_ref_exact=sum(p['predicted_relative_to_reference']['exact'] for p in pairs)
    actual_ref_exact=sum(p['actual_relative_to_reference']['exact'] for p in pairs)
    divergence_prompt_exact=sum(all(p['actual_relative_to_reference']['first_divergence_index']==p['predicted_relative_to_reference']['first_divergence_index'] for p in differing if p['task_id']==task) for task in {p['task_id'] for p in differing})
    status='MECHANISM_PREDICTION_VALIDATED' if exact==72 else 'MECHANISM_PREDICTION_NOT_FULLY_VALIDATED'
    result={'schema':'heterospec.b570.mechanism.validation.v08','executed':True,'status':status,'exact_sequences':exact,'denominator':72,'prompt_classification_matches':classification,'prompt_denominator':24,'complete_prompt_trajectory_matches':prompt_trajectories,'first_divergence_exact_pairs':first,'actual_mismatching_pairs':len(differing),'first_divergence_exact_prompts':divergence_prompt_exact,'actual_mismatching_prompts':len({p['task_id'] for p in differing}),'qualification_prediction':{'predicted_reference_exact_pairs':predicted_ref_exact,'actual_reference_exact_pairs':actual_ref_exact,'denominator':72,'predicted_status':'QUALIFIED_ON_RESERVED_PAIRS' if predicted_ref_exact==72 else 'BLOCKED_ON_RESERVED_PAIRS','actual_status':'QUALIFIED_ON_RESERVED_PAIRS' if actual_ref_exact==72 else 'BLOCKED_ON_RESERVED_PAIRS','scope':'Reserved pairs only; no production correctness certificate and no reinterpretation of historical 78/90 BLOCKED.'},'pairs':pairs,'finished_utc':utc()}
    save(PROTOCOL/'VALIDATION_ANALYSIS.json',result)
    (PROTOCOL/'VALIDATION_REPORT.md').write_text('# Reserved prospective validation\n\n'+f'**{status}**. Complete predictor-to-actual sequences: {exact}/72. Prompt mismatch/no-mismatch classification: {classification}/24. Complete prompt trajectories: {prompt_trajectories}/24. First-divergence index: {first}/{len(differing)} actually nonexact pairs.\n\nPredictions were committed and pushed before live serialized outcomes. No predictor changes, selective reruns, performance/energy study or manuscript edits. Complete token and divergence evidence are preserved in VALIDATION_ANALYSIS.json.\n',encoding='utf-8')
    print(status,flush=True)

if __name__=='__main__':
    stages={'prepare-build':prepare_build,'qualify':qualify,'discover':discover,'freeze-h1':freeze_h1,'predict-reserved':predict_reserved,'actual-reserved':actual_reserved,'analyze-reserved':analyze_reserved}
    p=argparse.ArgumentParser();p.add_argument('stage',choices=list(stages));a=p.parse_args();stages[a.stage]()
