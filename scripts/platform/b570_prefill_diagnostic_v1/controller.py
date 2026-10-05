"""Single-process, fail-closed local study pipeline. No LLM calls."""
import argparse, ctypes, hashlib, json, os, pathlib, re, shutil, subprocess, sys, time, traceback, uuid, threading, tarfile
from datetime import datetime, timezone
ROOT=pathlib.Path(__file__).resolve().parents[3]
HERE=pathlib.Path(__file__).parent
STUDY='B570_PREFILL_DIAGNOSTIC_V1'
OUT=ROOT/'artifacts/b570_prefill_diagnostic_v1'
DOC=ROOT/'benchmarks/b570_prefill_diagnostic_v1'
OLD=pathlib.Path('C:/Users/DIANG/Documents/ChatGPT/HeteroSpec')
BIN=pathlib.Path('C:/hs/b570-prefill-build/Release')
TARGET=OLD/'models/gguf/Qwen3-8B-Q8_0.gguf'
DRAFT=OLD/'models/gguf/Qwen3-0.6B-Q8_0.gguf'
TASKS=['HumanEval/'+str(i) for i in [58,156,134,42,122,114,93,115,151,63,125,133,43,139,77,35,27,34,145,82,154,78,96,138]]
CASES=['HumanEval/'+str(i) for i in [134,42,145,138]]
G0TASKS=CASES+['HumanEval/58']
CONDITIONS=['R','T0','N0','T1','N1']
STATE={};MUTEX=threading.RLock()
def utc():return datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with pathlib.Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
def save(p,x):
    p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_name(p.name+'.tmp')
    with tmp.open('w',encoding='utf-8',newline='\n') as f:json.dump(x,f,indent=2,ensure_ascii=False);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(tmp,p)
def event(kind,**kw):
    with MUTEX:
        x={'event_id':uuid.uuid4().hex,'utc':utc(),'event':kind,**kw}
        with (OUT/'RUN_LEDGER.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(x,ensure_ascii=False)+'\n');f.flush();os.fsync(f.fileno())
        return x
def ledger():
    p=OUT/'RUN_LEDGER.jsonl'
    return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines()] if p.exists() else []
def identity(pid):
    h=ctypes.windll.kernel32.OpenProcess(0x1000,False,pid)
    if not h:return None
    try:
        times=[ctypes.c_ulonglong() for _ in range(4)]
        if not ctypes.windll.kernel32.GetProcessTimes(h,*[ctypes.byref(x) for x in times]):return None
        return str(times[0].value)
    finally:ctypes.windll.kernel32.CloseHandle(h)
def environment():
    cmd="[Console]::OutputEncoding=[Text.UTF8Encoding]::new(); [ordered]@{os=(Get-CimInstance Win32_OperatingSystem|Select-Object Caption,Version,BuildNumber,CSName);gpu=@(Get-CimInstance Win32_VideoController|Select-Object Name,DriverVersion,PNPDeviceID);vulkan_runtime=(Get-Item C:\\Windows\\System32\\vulkan-1.dll).VersionInfo.FileVersion}|ConvertTo-Json -Depth 5"
    return json.loads(subprocess.check_output(['powershell.exe','-NoProfile','-Command',cmd],encoding='utf-8-sig'))
def endpoint(ids,flags):
    if not ids or len(ids)!=len(flags) or any(type(i)!=int or i<0 or i>=151936 for i in ids) or any(type(f)!=bool for f in flags):raise RuntimeError('Bad endpoint schema')
    stop=next((i+1 for i,b in enumerate(flags) if b),len(ids));n=min(128,stop)
    a=ids[:n];e=flags[:n]
    if not e[-1] and n!=128:raise RuntimeError('Incomplete non-EOG endpoint')
    return {'ids':a,'eog':e,'endpoint':'EOG' if e[-1] else 'CAP128','raw_overshoot':len(ids)-n}
def same(a,b):return a['ids']==b['ids'] and a['eog']==b['eog'] and a['endpoint']==b['endpoint']
def rel(p):return str(pathlib.Path(p).relative_to(ROOT)).replace('\\','/')
def inventory():return {str(p):sha(p) for p in sorted(HERE.glob('*')) if p.is_file() and p.suffix in ('.py','.cpp','.h','.txt')}
def file_metadata(p):
    s=pathlib.Path(p).stat();return {'bytes':s.st_size,'mtime_ns':s.st_mtime_ns}
def quick_gate():
    m=read(DOC/'ASSET_MANIFEST.json')
    if inventory()!=m['source_files']:raise RuntimeError('Source drift before worker')
    if sha(DOC/'PROTOCOL.json')!=STATE['protocol_sha256']:raise RuntimeError('Protocol drift before worker')
    for p,meta in m.get('file_metadata',{}).items():
        if file_metadata(p)!=meta:raise RuntimeError('Asset/input metadata drift before worker: '+p)
def prepare():
    OUT.mkdir(parents=True,exist_ok=True);DOC.mkdir(parents=True,exist_ok=True)
    if (DOC/'ASSET_MANIFEST.json').exists() or (DOC/'FREEZE.json').exists():raise RuntimeError('Already prepared; do not overwrite')
    oldpred=read(OLD/'benchmarks/b570_mechanism_v08/RESERVED_PREDICTIONS.json')
    authoritative=read(ROOT/'benchmarks/b570_mechanism_v08/RESERVED_PREDICTIONS.json')
    assert oldpred==authoritative
    assert read(ROOT/'benchmarks/b570_mechanism_v08/RESERVED_VALIDATION_SET.json')['selected_task_ids']==TASKS
    expected={};inputs={}
    outcomes=read(OLD/'artifacts/b570_mechanism_v08/raw/reserved_outcomes/executions.json')['executions']
    for task in TASKS:
        pbase=OLD/'artifacts/b570_mechanism_v08/raw/reserved_predictions'
        short=task.replace('/','_')
        p=OUT/'inputs'/short;p.mkdir(parents=True,exist_ok=True)
        for suffix in ('.prompt.txt','.prompt_ids.json'):shutil.copy2(pbase/(short+suffix),p/('prompt'+suffix.removeprefix('.prompt')))
        for r in range(1,4):
            ref=read(pbase/(short+f'-r{r}-ub128.capture.json'));h1=read(pbase/(short+f'-r{r}-ub1.capture.json'))
            assert ref['prompt_ids']==h1['prompt_ids']==read(p/'prompt_ids.json')
            native=next(x for x in outcomes if x['task_id']==task and x['repetition']==r)
            assert native['execution_valid']
            expected[f'{task}/R/{r}']=endpoint(ref['generated_ids'],ref['eog'])
            expected[f'{task}/T0/{r}']=endpoint(h1['generated_ids'],h1['eog'])
            expected[f'{task}/N0/{r}']=endpoint(native['raw_committed_ids'],native['raw_eog_flags'])
            assert same(expected[f'{task}/T0/{r}'],expected[f'{task}/N0/{r}'])
        inputs[task]={'text':str(p/'prompt.txt'),'ids':str(p/'prompt_ids.json'),'text_sha256':sha(p/'prompt.txt'),'ids_sha256':sha(p/'prompt_ids.json')}
    save(OUT/'evaluation/HISTORICAL_EXPECTED.json',expected)
    save(OUT/'INPUTS.json',inputs)
    protocol={'study':STUDY,'version':1,'tasks':TASKS,'cases':CASES,'conditions':CONDITIONS,'repetitions':3,'planned':360,
      'base_commit':'3dac2600f84955b36944a6bd19574577775ccdfb','science_commit':'01682f3b992a11b36b309fbd6c9e9950f1dc5d89',
      'endpoint':'inclusive-first-runtime-EOG or first 128 IDs; retain raw native overshoot exactly as legacy collector',
      'candidate':'target prefill context UB128, pending first sample in that context, serialized KV plus post-sample sampler clone to UB1; same transfer in T0/N0; draft stays UB1',
      'caller_grouping':{'target_only':'common_prompt_batch_decode chunks <=512','native':'prompt[:-1] then prompt[-1]; unchanged across N0/N1'},
      'known_grouping_difference':'T1 uses original H1 grouping, N1 uses original native grouping; comparison is migration across these preserved callers, not identical prefill batch APIs',
      'g0_tasks':G0TASKS,'g0_repetitions':3,'g0_variants':['R_old','T_old','N_old','R','T_plain','N_plain','T0','N0'],
      'order':['G0','PROTOCOL_FROZEN','BASELINES','T1_CAPTURE','T1_SEALED','N1_LIVE','ANALYZE','PACKAGE','COMPLETE'],
      'retries':{'infrastructure':2,'valid_output':0,'deterministic_crash':0,'select':'first valid complete attempt; never rerun different valid IDs'},
      'budget_hours':10,'analysis_reserve_hours':0.75,'exposure':'all 24 tasks previously exposed; no candidate native output seen before seal',
      'isolation':'native process receives asset paths, prompt and fixed config only; evaluation arrays not supplied; shared OS is not adversarial isolation',
      'timing':'local ledger supports ordering, no independently certified absolute timestamp','performance_claims':False}
    save(DOC/'PROTOCOL.json',protocol)
    known=read(ROOT/'benchmarks/b570_mechanism_v08/build_manifest.json')
    files={str(TARGET):sha(TARGET),str(DRAFT):sha(DRAFT)}
    for p in (TARGET,DRAFT):assert files[str(p)]==known['assets'][str(p.relative_to(OLD)).replace('/','\\')]
    for p in BIN.glob('*.dll'):assert sha(p)==known['binary_hashes'][p.name];files[str(p)]=sha(p)
    for p in BIN.glob('*.exe'):files[str(p)]=sha(p)
    original=pathlib.Path('C:/hs/b570-direct-id-v1-src')
    for name,h in known['source_file_hashes'].items():
        p=original/name
        assert sha(p)==h,('Pinned header/source changed',p);files[str(p)]=h
    for p,h in known['static_import_library_hashes'].items():assert sha(p)==h;files[p]=h
    for p in [pathlib.Path('C:/hs/b570-mechanism-v08-build/Release/heterospec-mechanism.exe'),pathlib.Path('C:/hs/b570-direct-id-v1-build/bin/Release/llama-speculative.exe')]:files[str(p)]=sha(p)
    assert files[str(pathlib.Path('C:/hs/b570-mechanism-v08-build/Release/heterospec-mechanism.exe'))]==known['binary_hashes']['heterospec-mechanism.exe']
    for directory in ['C:/hs/b570-mechanism-v08-build/Release','C:/hs/b570-direct-id-v1-build/bin/Release']:
        for p in pathlib.Path(directory).glob('*.dll'):assert sha(p)==known['binary_hashes'][p.name];files[str(p)]=sha(p)
    native_src=original/'examples/speculative/speculative.cpp';files[str(native_src)]=sha(native_src)
    assert sha(native_src)==read(ROOT/'benchmarks/b570_partition_intervention_v1/BUILD_IDENTITY.json')['pinned_source_files']['examples/speculative/speculative.cpp']
    env=environment()
    devices=subprocess.check_output([str(BIN/'heterospec-mechanism.exe'),'--list-devices'],stderr=subprocess.STDOUT).decode('utf-8',errors='replace')
    assert 'Vulkan0: Intel(R) Arc(TM) B570 Graphics' in devices
    save(DOC/'ASSET_MANIFEST.json',{'created':utc(),'files':files,'source_files':inventory(),'inputs':inputs,'environment':env,'vulkan_devices':devices,'historical_environment_equal':env==known['environment'],'os_drift':'26200 to 26300; new empirical qualification mandatory','unknown':['opaque sampler byte serialization','driver installation package digest','unique Vulkan kernel cause'],'historical_binaries':'retained, not rebuilt; new frontends rebuilt against verified pinned headers/import libraries and identical DLLs'})
    save(OUT/'QUEUE.json',[{'id':f'{STUDY}/v1/{t}/{c}/{r}','task':t,'condition':c,'repetition':r} for c in CONDITIONS for r in range(1,4) for t in TASKS])
    event('BOOTSTRAP',protocol_sha256=sha(DOC/'PROTOCOL.json'))
    (OUT/'RESUME.md').write_text(f'# {STUDY}\n\nRead STATE.json, STATUS.json and RUN_LEDGER.jsonl first. Check controller PID creation identity and exclusive LOCK.json. Do not start a second active controller.\n\nResume: `{sys.executable} {HERE / "controller.py"} run`\n\nController validates input, source and asset hashes, resumes only complete verified units, and blocks N1 without a valid 72-unit T1 seal. All attempts are retained. G0/pilot never enter formal denominators.\n\nStatus: `{sys.executable} {HERE / "controller.py"} status`\n\nFormal state is not COMPLETE until independent verification and clean archive extraction succeed.\n',encoding='utf-8')
def check_assets(full=False):
    m=read(DOC/'ASSET_MANIFEST.json')
    if inventory()!=m['source_files']:raise RuntimeError('Source drift')
    for p,h in m['files'].items():
        if not full and pathlib.Path(p).suffix.lower()=='.gguf':continue
        if sha(p)!=h:raise RuntimeError('Asset drift: '+p)
    for inp in m['inputs'].values():
        for k in ['text','ids']:
            if sha(inp[k])!=inp[k+'_sha256']:raise RuntimeError('Prompt drift')
    if environment()!=m['environment']:raise RuntimeError('Environment drift')
    if STATE.get('protocol_sha256') and STATE['protocol_sha256']!=sha(DOC/'PROTOCOL.json'):raise RuntimeError('Protocol drift')
def write_status():
    with MUTEX:
        STATE['heartbeat_utc']=utc()
        valid=[];failed=[]
        for p in (OUT/'formal').glob('*/result.json'):valid.append(read(p)['unit_id'])
        starts=[e for e in ledger() if e['event']=='ATTEMPT_END' and e.get('formal') and not e.get('valid')]
        failed=[e['unit_id'] for e in starts]
        STATE.update(completed_units=valid,failed_attempt_units=failed,unexecuted_units=[j['id'] for j in read(OUT/'QUEUE.json') if j['id'] not in valid],completed=len(valid),planned=360,failed_attempts=len(starts),seal=(OUT/'T1_SEAL.json').exists())
        save(OUT/'STATE.json',STATE)
        save(OUT/'STATUS.json',{k:v for k,v in STATE.items() if k not in ['completed_units','failed_attempt_units','unexecuted_units']})
def stage(name):
    with MUTEX:STATE.update(stage=name,current_job=None,worker_pid=None,progress_utc=utc());event('STAGE',stage=name);write_status()
def heartbeat(stop):
    while not stop.wait(30):
        try:write_status()
        except Exception:pass
def command(task,variant,rep,capture):
    native=variant.startswith('N');old=variant.endswith('_old')
    cond='R' if variant.startswith('R') else 'N0' if native else 'T0'
    inputs=read(OUT/'INPUTS.json')[task]
    exe=pathlib.Path('C:/hs/b570-direct-id-v1-build/bin/Release/llama-speculative.exe') if native and old else pathlib.Path('C:/hs/b570-mechanism-v08-build/Release/heterospec-mechanism.exe') if old else BIN/('heterospec-prefill-native.exe' if native else 'heterospec-mechanism.exe')
    ub=128 if cond=='R' else 1
    cmd=[str(exe),'--model',str(TARGET),'--device','Vulkan0','--n-gpu-layers','all','--fit','off','--ctx-size','1024','--batch-size','512','--ubatch-size',str(ub),'--flash-attn','off','--file',inputs['text'],'--n-predict','127' if native else '128','--temp','0','--top-k','0','--top-p','1','--min-p','0','--seed','123']
    if native:cmd+=['--verbose','--spec-type','draft-simple','--spec-draft-model',str(DRAFT),'--spec-draft-device','Vulkan0','--spec-draft-ngl','all','--spec-draft-n-max','2','--spec-draft-n-min','0']
    else:cmd+=['--reasoning','off','--simple-io','--no-warmup','--log-verbosity','4','--no-conversation']
    # An explicit environment allowlist prevents legacy prediction/proposal env variables entering native.
    keys=['SystemRoot','WINDIR','TEMP','TMP','PATH','COMSPEC','PATHEXT','USERPROFILE','LOCALAPPDATA','APPDATA','NUMBER_OF_PROCESSORS','PROCESSOR_ARCHITECTURE']
    env={k:os.environ[k] for k in keys if k in os.environ}
    env.update(HS_PREFILL_OUTPUT=str(capture),HS_PREFILL_UB=str(128 if variant in ['R','R_old','T1','N1'] else 1),HS_MECHANISM_INPUT_IDS=inputs['ids'],HS_MECHANISM_OUTPUT=str(capture))
    if native and old:env['HETEROSPEC_DIRECT_ID_PATH']=str(capture)
    if variant.endswith('_plain'):env['HS_NO_TRANSFER']='1'
    return cmd,env
def validate_capture(capture,native,old,variant):
    x=read(capture)
    ep=endpoint(x.get('ids',x.get('generated_ids')),x['eog'])
    if not old:
        assert x['prompt_ids']
        if variant not in ['R','T_plain','N_plain']:
            t=x['transfer'];assert t and t['kv_equal'] and t['source_unchanged'] and t['consumed_bytes']==t['state_bytes']
            assert t['before']==t['after']==t['source_after'] and t['destination_ub']==1
            assert t['sampler_chain']==t['clone_chain'] and t['sampler_history']==t['clone_history'] and t['seed']==t['clone_seed']==123
            assert t['pending_id']==ep['ids'][0]
            assert sha(str(capture)+'.before.kv')==sha(str(capture)+'.restored.kv')==sha(str(capture)+'.source_after.kv')
            assert pathlib.Path(str(capture)+'.pending_logits.f32').stat().st_size==151936*4
        decodes=[t for t in x['trace'] if t['event']=='decode']
        assert decodes
        for d in decodes:
            assert d['exit_code']==0
            if d['role']=='target' and d['phase']=='prefill':assert d['ub_capacity']==(128 if variant in ['R','T1','N1'] else 1)
            if d['phase']=='continuation':assert d['ub_capacity']==(128 if variant=='R' else 1)
            if d['role']=='draft':assert d['ub_capacity']==1
        assert len(x['commits'])==len(x['ids'])
    return ep,x
def cached(path,unit):
    if not path.exists():return None
    x=read(path)
    assert x['unit_id']==unit and x['protocol_sha256']==sha(DOC/'PROTOCOL.json')
    for p,h in x['files'].items():assert sha(ROOT/p)==h,('Cached result drift',p)
    return x
def run_unit(task,variant,rep,formal=False,pilot=False):
    if not pilot:quick_gate()
    unit=f'{STUDY}/v1/{task}/{variant}/{rep}'
    base=OUT/('formal' if formal else 'pilot' if pilot else 'g0')/(task.replace('/','_')+'-'+variant+'-r'+str(rep))
    existing=cached(base/'result.json',unit)
    if existing:return existing
    if formal and variant=='N1':verify_seal()
    base.mkdir(parents=True,exist_ok=True)
    attempts=sorted(base.glob('attempt-*'));remaining=3-len(attempts) if formal else 1-len(attempts)
    if remaining<=0:raise RuntimeError('Attempt budget exhausted: '+unit)
    for ai in range(len(attempts)+1,len(attempts)+1+remaining):
        attempt=uuid.uuid4().hex;directory=base/f'attempt-{ai:02d}-{attempt}';directory.mkdir()
        cap=directory/'capture.json';cmd,env=command(task,variant,rep,cap)
        start={'unit_id':unit,'attempt_id':attempt,'variant':variant,'formal':formal,'task':task,'rep':rep,'command':cmd,'env_overrides':{k:v for k,v in env.items() if k.startswith('HS_') or k.startswith('HETEROSPEC_')},'protocol_sha256':sha(DOC/'PROTOCOL.json'),'start_utc':utc()}
        save(directory/'START.json',start);event('ATTEMPT_START',**start)
        STATE.update(current_job=unit,progress_utc=utc());write_status()
        before=time.monotonic();err=None;code=None
        try:
            with (directory/'stdout.txt').open('wb') as out,(directory/'stderr.txt').open('wb') as er:
                proc=subprocess.Popen(cmd,env=env,cwd=directory,stdout=out,stderr=er)
                STATE.update(worker_pid=proc.pid,worker_creation_identity=identity(proc.pid));write_status()
                # No fixed token-log timeout. A generous 30-minute execution limit covers pilot variance.
                code=proc.wait(timeout=1800)
            if code:raise RuntimeError('Worker exit '+str(code))
            ep,x=validate_capture(cap,variant.startswith('N'),variant.endswith('_old'),variant)
            if not variant.endswith('_old') and x['prompt_ids']!=read(read(OUT/'INPUTS.json')[task]['ids']):raise RuntimeError('Prompt IDs differ')
            text=(directory/'stderr.txt').read_text(encoding='utf-8',errors='replace')
            off=re.findall(r'offloaded\s+(\d+)/(\d+) layers to GPU',text)
            if ['37','37'] not in [list(a) for a in off] or (variant.startswith('N') and ['29','29'] not in [list(a) for a in off]):raise RuntimeError('Offload gate')
            if 'using device Vulkan0 (Intel(R) Arc(TM) B570 Graphics)' not in text:raise RuntimeError('Device gate')
            files={rel(p):sha(p) for p in directory.iterdir() if p.is_file()}
            row={**start,**ep,'valid':True,'exit_code':code,'elapsed_seconds':time.monotonic()-before,'capture':rel(cap),'files':files,'end_utc':utc()}
            save(base/'result.json',row);event('ATTEMPT_END',unit_id=unit,attempt_id=attempt,formal=formal,valid=True,exit_code=code,elapsed_seconds=row['elapsed_seconds'],result=rel(base/'result.json'))
            STATE.update(worker_pid=None,current_job=None,progress_utc=utc());write_status();return row
        except Exception as exc:
            if isinstance(exc,subprocess.TimeoutExpired):
                # Preserve failure; do not retry a deterministic/hung computation.
                proc.terminate();proc.wait(timeout=30)
            err=str(exc);save(directory/'FAILURE.json',{**start,'end_utc':utc(),'exit_code':code,'error':err})
            event('ATTEMPT_END',unit_id=unit,attempt_id=attempt,formal=formal,valid=False,exit_code=code,error=err)
            STATE.update(worker_pid=None,current_job=None);write_status()
            infrastructure=isinstance(exc,(OSError,PermissionError)) and (code is None or code==0)
            if not formal or not infrastructure or ai>=3:raise
def g0():
    stage('G0');expected=read(OUT/'evaluation/HISTORICAL_EXPECTED.json');checks=[]
    for task in G0TASKS:
        for rep in range(1,4):
            rows={}
            for v in ['R_old','T_old','N_old','R','T_plain','N_plain','T0','N0']:
                row=run_unit(task,v,rep);c='R' if v.startswith('R') else 'N0' if v.startswith('N') else 'T0'
                assert same(row,expected[f'{task}/{c}/{rep}']),('G0 old-array regression',task,v,rep)
                rows[v]=row
            assert same(rows['R_old'],rows['R']) and same(rows['T_old'],rows['T_plain']) and same(rows['N_old'],rows['N_plain'])
            assert same(rows['T_plain'],rows['T0']) and same(rows['N_plain'],rows['N0'])
            # Instrumented sham also preserves all decisions, scores and actual proposal history.
            for plain,moved in [('T_plain','T0'),('N_plain','N0')]:
                a=read(ROOT/rows[plain]['capture']);b=read(ROOT/rows[moved]['capture'])
                assert [(c['id'],c['accepted'],c['proposal'],c['scores']) for c in a['commits']]==[(c['id'],c['accepted'],c['proposal'],c['scores']) for c in b['commits']]
                da=[d for d in a['trace'] if d['event']=='decode'];db=[d for d in b['trace'] if d['event']=='decode']
                assert da==db,('Sham decode trace changed',plain,moved)
            checks.append({'task':task,'repetition':rep,'pass':True,'arrays':8,'instrumentation_equal':True,'sham_scores_decisions_proposals_equal':True,'full_decode_traces_equal':True})
            save(DOC/'G0_PROGRESS.json',checks)
    save(DOC/'G0.json',{'status':'PASS','checks':checks,'executions':120,'scheduler_fixture':read(DOC/'FIXTURE_RECEIPT.json'),'created':utc()})
def formal_rows():return [read(p) for p in sorted((OUT/'formal').glob('*/result.json'))]
def gate_baselines():
    expected=read(OUT/'evaluation/HISTORICAL_EXPECTED.json');rows=[r for r in formal_rows() if r['variant'] in ['R','T0','N0']]
    assert len(rows)==216
    for r in rows:assert same(r,expected[f'{r["task"]}/{r["variant"]}/{r["rep"]}']),('Baseline mismatch',r['unit_id'])
    save(DOC/'BASELINE_GATE.json',{'status':'PASS','units':216,'tasks':24,'created':utc(),'results':{r['unit_id']:sha(ROOT/pathlib.Path(r['capture']).parent.parent/'result.json') for r in rows}})
def verify_seal():
    assert read(DOC/'BASELINE_GATE.json')['status']=='PASS'
    seal=read(OUT/'T1_SEAL.json')
    assert seal['protocol_sha256']==sha(DOC/'PROTOCOL.json') and seal['manifest_sha256']==sha(DOC/'ASSET_MANIFEST.json')
    assert len(seal['predictions'])==72
    expected={f'{STUDY}/v1/{t}/T1/{r}' for t in TASKS for r in range(1,4)}
    assert set(seal['predictions'])==expected
    for unit,item in seal['predictions'].items():
        assert sha(ROOT/item['path'])==item['sha256']
        row=read(ROOT/item['path']);assert row['unit_id']==unit and row['valid']
        for p,h in row['files'].items():assert sha(ROOT/p)==h
    events=ledger();seals=[e for e in events if e['event']=='T1_SEALED']
    assert len(seals)==1 and seals[0]['seal_sha256']==sha(OUT/'T1_SEAL.json')
    for i,e in enumerate(events):
        if e['event']=='ATTEMPT_START' and e.get('variant')=='N1':assert i>events.index(seals[0])
def freeze():
    assert read(DOC/'G0.json')['status']=='PASS';check_assets(full=True)
    fixture=read(DOC/'FIXTURE_RECEIPT.json')
    assert all(fixture[k] for k in ['missing_seal_rejected','result_hash_drift_rejected','protocol_hash_drift_rejected','early_N1_rejected','bad_endpoint_rejected','duplicate_active_controller_rejected','atomic_commit_pass','partial_not_completed','detached_survival'])
    existing=DOC/'FREEZE.json'
    if existing.exists():
        f=read(existing);assert f['protocol_sha256']==sha(DOC/'PROTOCOL.json') and f['manifest_sha256']==sha(DOC/'ASSET_MANIFEST.json');return
    save(existing,{'stage':'PROTOCOL_FROZEN','utc':utc(),'protocol_sha256':sha(DOC/'PROTOCOL.json'),'manifest_sha256':sha(DOC/'ASSET_MANIFEST.json'),'sources':inventory(),'g0_sha256':sha(DOC/'G0.json'),'exposure':'old R/T0/N0 and G0 only; no N1 exposure'})
    subprocess.run(['git','add','scripts/platform/b570_prefill_diagnostic_v1','benchmarks/b570_prefill_diagnostic_v1'],cwd=ROOT,check=True)
    subprocess.run(['git','commit','-m','Freeze qualified B570 prefill diagnostic v1 protocol and implementation'],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
    event('PROTOCOL_FROZEN',commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),freeze_sha256=sha(existing))
def seal():
    if (OUT/'T1_SEAL.json').exists():verify_seal();return
    rows=[r for r in formal_rows() if r['variant']=='T1'];assert len(rows)==72
    predictions={r['unit_id']:{'path':rel(ROOT/pathlib.Path(r['capture']).parent.parent/'result.json'),'sha256':sha(ROOT/pathlib.Path(r['capture']).parent.parent/'result.json'),'ids':r['ids'],'eog':r['eog'],'endpoint':r['endpoint']} for r in rows}
    save(OUT/'T1_SEAL.json',{'study':STUDY,'created':utc(),'protocol_sha256':sha(DOC/'PROTOCOL.json'),'manifest_sha256':sha(DOC/'ASSET_MANIFEST.json'),'freeze_sha256':sha(DOC/'FREEZE.json'),'predictions':predictions,'ledger_sha256_before_seal':sha(OUT/'RUN_LEDGER.jsonl'),'timestamp_scope':'local record, not independently certified absolute time'})
    event('T1_SEALED',seal_sha256=sha(OUT/'T1_SEAL.json'));verify_seal()
def acquire():
    p=OUT/'LOCK.json'
    if p.exists():
        lock=read(p)
        if identity(lock['pid'])==lock['creation_identity']:raise RuntimeError('Controller already active; read STATUS only')
        event('STALE_LOCK_RECOVERY',old_lock=lock);p.rename(OUT/('LOCK.stale.'+uuid.uuid4().hex+'.json'))
    with p.open('x',encoding='utf-8') as f:json.dump({'pid':os.getpid(),'creation_identity':identity(os.getpid()),'utc':utc()},f);f.flush();os.fsync(f.fileno())
def run():
    acquire();stop=threading.Event()
    if (OUT/'STATE.json').exists():STATE.update(read(OUT/'STATE.json'))
    STATE.update(study=STUDY,protocol_sha256=sha(DOC/'PROTOCOL.json'),controller_pid=os.getpid(),controller_creation_identity=identity(os.getpid()),controller_start=utc(),worker_pid=None)
    t=threading.Thread(target=heartbeat,args=(stop,),daemon=True);t.start()
    previous_starts=[e['utc'] for e in ledger() if e['event']=='CONTROLLER_START']
    campaign_start=datetime.fromisoformat(previous_starts[0]) if previous_starts else datetime.now(timezone.utc)
    remaining_seconds=9.25*3600-(datetime.now(timezone.utc)-campaign_start).total_seconds()
    deadline=time.monotonic()+remaining_seconds
    # Thread-scoped execution-state request: automatically released on controller exit.
    ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
    event('CONTROLLER_START',pid=os.getpid(),creation_identity=identity(os.getpid()),power_policy='temporary SYSTEM_REQUIRED; no driver/clock/fan changes')
    try:
        check_assets(full=True)
        if not (DOC/'G0.json').exists():g0()
        stage('PROTOCOL_FROZEN');freeze()
        expected=read(OUT/'evaluation/HISTORICAL_EXPECTED.json')
        for s,conds in [('BASELINES',['R','T0','N0']),('T1_CAPTURE',['T1']),('N1_LIVE',['N1'])]:
            if s=='T1_CAPTURE':gate_baselines()
            if s=='N1_LIVE':seal();stage('T1_SEALED');check_assets(full=True)
            stage(s)
            for c in conds:
                for rep in range(1,4):
                    for task in TASKS:
                        if time.monotonic()>deadline:raise RuntimeError('BUDGET_PARTIAL: atomic boundary reached; preserve queue')
                        r=run_unit(task,c,rep,formal=True)
                        if c in ['R','T0','N0'] and not same(r,expected[f'{task}/{c}/{rep}']):raise RuntimeError('Baseline mismatch: '+r['unit_id'])
                check_assets()
        check_assets(full=True);verify_seal();stage('ANALYZE')
        subprocess.run([sys.executable,str(HERE/'independent_verify.py')],check=True,cwd=ROOT)
        stage('PACKAGE');package()
        summary=read(DOC/'SUMMARY.json');summary.update(status='COMPLETE',archive='PASS',remote_delivery='NOT_UPLOADED');save(DOC/'SUMMARY.json',summary)
        report=DOC/'STUDY_REPORT.md';report.write_text(report.read_text(encoding='utf-8').replace('360/360 formal units independently verified; archival completion pending.','COMPLETE: 360/360 formal units independently verified; archive contents verified.'),encoding='utf-8')
        subprocess.run(['git','add','benchmarks/b570_prefill_diagnostic_v1'],cwd=ROOT,check=True)
        subprocess.run(['git','commit','-m','Close out complete B570 prefill diagnostic v1'],cwd=ROOT,stdout=subprocess.DEVNULL,check=True)
        stage('COMPLETE');event('COMPLETE',valid_units=360)
    except Exception as e:
        error={'utc':utc(),'stage':STATE.get('stage'),'error':str(e),'traceback':traceback.format_exc()};save(DOC/'STOP_REASON.json',error)
        event('STOP',**error);stage('PARTIAL' if 'BUDGET_PARTIAL' in str(e) else 'BLOCKED')
        save(DOC/'SUMMARY.json',{'status':STATE['stage'],'planned':360,'valid':STATE['completed'],'failed_attempts':STATE['failed_attempts'],'unexecuted':360-STATE['completed'],'reason':str(e),'g0':read(DOC/'G0.json')['status'] if (DOC/'G0.json').exists() else 'NOT_PASSED','seal_valid':False,'scientific_conclusion':'No qualified formal interpretation at this stopping gate'})
        (DOC/'STUDY_REPORT.md').write_text('# B570 prefill diagnostic v1\n\n'+json.dumps(read(DOC/'SUMMARY.json'),ensure_ascii=False,indent=2)+'\n\nAll attempt records and unexecuted units retained. See STOP_REASON.json and RESUME.md.\n',encoding='utf-8')
        try:package(partial=True)
        except Exception as packerr:save(DOC/'PACKAGE_FAILURE.json',{'error':str(packerr),'utc':utc()})
    finally:
        stop.set();t.join(timeout=5);write_status();ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
        lock=OUT/'LOCK.json'
        if lock.exists() and read(lock)['pid']==os.getpid():lock.rename(OUT/('LOCK.finished.'+uuid.uuid4().hex+'.json'))
def package(partial=False):
    # Content manifest excludes mutable status/ledger and the capsule itself; original raw records stay untouched.
    capsule=OUT/'capsule';capsule.mkdir(exist_ok=True)
    paths=[p for p in OUT.rglob('*') if p.is_file() and capsule not in p.parents and '.tmp' not in p.name and not p.name.startswith('LOCK') and p.name not in ['STATE.json','STATUS.json','RUN_LEDGER.jsonl']]
    paths+=list(DOC.glob('*'))+[p for p in HERE.glob('*') if p.is_file()]
    manifest={rel(p):sha(p) for p in paths};save(capsule/'CONTENTS.json',manifest)
    name=('partial-'+uuid.uuid4().hex if partial else 'raw-capsule-v1')+'.tar.gz';tmp=capsule/(name+'.tmp')
    with tarfile.open(tmp,'w:gz',compresslevel=3) as tf:
        for p in paths:tf.add(p,arcname=rel(p),recursive=False)
        for p in [OUT/'RUN_LEDGER.jsonl',OUT/'STATE.json',OUT/'STATUS.json',capsule/'CONTENTS.json']:tf.add(p,arcname=rel(p),recursive=False)
    os.replace(tmp,capsule/name)
    with tarfile.open(capsule/name,'r:gz') as tf:
        checked=0
        for member in tf:
            if member.name in manifest:
                f=tf.extractfile(member);h=hashlib.sha256()
                for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
                assert h.hexdigest()==manifest[member.name];checked+=1
    assert checked==len(manifest)
    extract=pathlib.Path('C:/hs/b570-prefill-archive-check')/sha(capsule/name)
    extract.mkdir(parents=True,exist_ok=True)
    with tarfile.open(capsule/name,'r:gz') as tf:tf.extractall(extract,filter='data')
    assert all(sha(extract/p)==h for p,h in manifest.items())
    if not partial:
        with (capsule/'extracted-verifier.stdout.txt').open('wb') as out,(capsule/'extracted-verifier.stderr.txt').open('wb') as err:
            subprocess.run([sys.executable,str(extract/rel(HERE/'independent_verify.py'))],cwd=extract,stdout=out,stderr=err,check=True)
    subprocess.run(['git','add','scripts/platform/b570_prefill_diagnostic_v1','benchmarks/b570_prefill_diagnostic_v1'],cwd=ROOT,check=True)
    subprocess.run(['git','commit','-m','Archive B570 prefill diagnostic v1 research state'],cwd=ROOT,stdout=subprocess.DEVNULL)
    bundle=capsule/'research.git.bundle';subprocess.run(['git','bundle','create',str(bundle),'HEAD','^3dac2600f84955b36944a6bd19574577775ccdfb'],cwd=ROOT,check=True)
    save(DOC/'ARCHIVE_RECEIPT.json',{'status':'PASS','partial':partial,'archive':str(capsule/name),'sha256':sha(capsule/name),'bytes':(capsule/name).stat().st_size,'manifest_files':checked,'validation':'read every archive member, clean-extract and recompute every raw SHA256; independently revalidate extracted complete study','clean_extraction':str(extract),'git_bundle':str(bundle),'bundle_requires_base_commit':'3dac2600f84955b36944a6bd19574577775ccdfb','bundle_sha256':sha(bundle),'remote_delivery':'NOT_UPLOADED','created':utc()})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run','status','pilot']);a=p.parse_args()
    if a.action=='prepare':prepare()
    elif a.action=='run':run()
    elif a.action=='status':print(json.dumps(read(OUT/'STATUS.json'),ensure_ascii=False,indent=2))
    elif a.action=='pilot':
        STATE.update(stage='G0_PILOT',protocol_sha256=sha(DOC/'PROTOCOL.json'))
        for c in ['R','T_plain','T0','N_plain','N0']:
            r=run_unit('HumanEval/134',c,1,pilot=True);print(c,r['elapsed_seconds'],len(r['ids']),flush=True)
