"""Single durable GPU queue, finite budget, seal-before-native and autonomous closeout."""
import ctypes, threading, time, traceback, shutil
from prepare import *
import execution as ex
import integrity as g
import qualification

STATE={};MUTEX=threading.RLock()

def status():
    with MUTEX:
        queue=read(DOC/'QUEUE.json');done=[p for p in (OUT/'formal').glob('*/result.json') if read(p).get('valid')]
        failed=list((OUT/'formal').rglob('FAILURE.json'))
        remaining=(datetime.fromisoformat(read(DOC/'BUDGET.json')['deadline_utc'])-datetime.now(timezone.utc)).total_seconds()
        STATE.update(completed=len(done),planned=645,failed_attempts=len(failed),remaining_budget_seconds=max(0,remaining),heartbeat_utc=utc())
        save(OUT/'STATUS.json',STATE)

def advance(name):
    with MUTEX:
        stages=[r['stage'] for r in g.events() if r['event']=='STAGE']
        if name not in stages:g.stage(name)
        STATE.update(stage=name,current_unit=None,progress_utc=utc());status()

def checkpoint_assets():
    g.check_freeze(full=True)
    for name,record in read(DOC/'LOADED_MODULE_IDENTITY.json')['modules'].items():
        p=Path(name);stat=p.stat();assert stat.st_size==record['bytes'] and stat.st_mtime_ns==record['mtime_ns'] and sha(p)==record['sha256']

def commit(message,paths):
    subprocess.run(['git','add','--sparse','--',*paths],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
    subprocess.run(['git','commit','-m',message],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
    return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()

def freeze():
    assert read(DOC/'G0_THREADS24.json')['status']=='PASS' and read(DOC/'ENGINEERING.json')['status']=='PASS' and read(DOC/'FIXTURE_RECEIPT.json')['status']=='PASS'
    if (DOC/'FREEZE.json').exists():g.check_freeze(full=True);return
    assert datetime.now(timezone.utc)<datetime.fromisoformat(read(DOC/'BUDGET.json')['preparation_deadline_utc'])
    estimate=read(DOC/'ENGINEERING.json')['estimated_formal_plus_hash_seconds']
    available=(datetime.fromisoformat(read(DOC/'BUDGET.json')['measurement_deadline_utc'])-datetime.now(timezone.utc)).total_seconds()
    if estimate>available:raise RuntimeError('PARTIAL_BUDGET: qualified prepared estimate exceeds measurement window')
    shutil.copyfile(DOC/'G0_THREADS24.json',DOC/'G0.json')
    module_paths=set()
    for p in OUT.rglob('*-wire.jsonl'):
        for line in p.read_text(encoding='utf-8').splitlines():
            x=json.loads(line)
            module_paths.update(x.get('response',{}).get('modules',[]))
    for p in OUT.rglob('trace.jsonl'):
        for line in p.read_text(encoding='utf-8').splitlines():module_paths.update(json.loads(line).get('modules',[]))
    modules={}
    for name in sorted(module_paths):
        p=Path(name)
        if p.is_file():
            stat=p.stat();modules[name]={'sha256':sha(p),'bytes':stat.st_size,'mtime_ns':stat.st_mtime_ns}
    assert any(Path(p).name.lower()=='nvcuda.dll' for p in modules)
    save(DOC/'LOADED_MODULE_IDENTITY.json',{'modules':modules,'observed_in':'actual qualification worker startup/close and native first-pending captures','utc':utc()})
    protocol={'study':STUDY,'version':1,'base':BASE,'upstream':UPSTREAM,'tasks':TASKS+['MBPP/'+str(i) for i in read(DOC/'COHORT.json')['formal']],'old_tasks':TASKS,'conditions':['R','H0','H1','N0','N1'],'repetitions':3,'planned':645,'g0_tasks':G0TASKS,'g0_arrays':120,'sham_pairs':30,'order':g.STAGES,'candidate':'target post-prefill UB2->UB1; same-boundary UB2->UB2 sham baseline; prefill2,draft2,k2 fixed','R':'original released UB1 CLI','threads':24,'ctx':4096,'batch':2048,'kv':'F16/F16','FA':'off','target_offload':'37/37 CUDA0','draft_offload':'29/29 CUDA0','endpoint':'first inclusive EOG or cap128; preserve exact raw stopped-by markers and overshoot','timeout_seconds':300,'transient_retries':1,'scientific_mismatch_retries':0,'budget_file_sha256':sha(DOC/'BUDGET.json'),'native_input':'prompt, assets, fixed parameters only; no H tape, predictions or reference IDs','H_input_allowlist':{'init':['op','formatted_prompt'],'verify':['op','round','position','pending','proposal_ids'],'propose':['op','position','pending','max_proposals'],'update':['op','position','verified_batch','retain_count']},'statistics':'exact finite counts and full task tables; no CI; repeats are stability observations','performance_claim':False,'total_existing_engineering_and_qualification_attempts':len(list(OUT.glob('*/**/START.json'))),'walltime_estimate_seconds':estimate}
    save(DOC/'PROTOCOL.json',protocol)
    implementation=commit('Implement qualified RTX target continuation intervention v1', ['scripts/platform/rtx_target_verification_intervention_v1','benchmarks/rtx_target_verification_intervention_v1'])
    files=g.inventory();meta={name:{'bytes':(ROOT/name).stat().st_size,'mtime_ns':(ROOT/name).stat().st_mtime_ns} for name in files}
    critical=[name for name in files if name.startswith('scripts/') or '/inputs/' in name]
    save(DOC/'FREEZE.json',{'implementation_commit':implementation,'base':BASE,'utc':utc(),'files':files,'metadata':meta,'critical_files':critical,'protocol_sha256':sha(DOC/'PROTOCOL.json'),'cohort_sha256':sha(DOC/'COHORT.json'),'queue_sha256':sha(DOC/'QUEUE.json'),'g0_sha256':sha(DOC/'G0.json'),'fixture_sha256':sha(DOC/'FIXTURE_RECEIPT.json'),'assets_sha256':sha(DOC/'ASSET_ENVIRONMENT.json'),'sampler_byte_equality_claimed':False})
    freezecommit=commit('Freeze RTX target verification v1 qualified execution identities', ['benchmarks/rtx_target_verification_intervention_v1/FREEZE.json'])
    g.event('FROZEN',implementation_commit=implementation,freeze_commit=freezecommit,freeze_sha256=sha(DOC/'FREEZE.json'))

def formal(q):
    deadline=datetime.fromisoformat(read(DOC/'BUDGET.json')['measurement_deadline_utc'])
    if datetime.now(timezone.utc)>=deadline:raise RuntimeError('PARTIAL_BUDGET: safe unit boundary reached')
    g.check_freeze()
    existing={r['unit_id'] for r in g.events() if r['event']=='UNIT_VALID'}
    with MUTEX:STATE.update(current_unit=q['id'],progress_utc=utc());status()
    c=q['condition']
    if q['id'] not in existing:
        if c in ['N0','N1']:
            g.native_guard(c);g.event('NATIVE_FORMAL_START',unit_id=q['id'],condition=c)
        g.event('UNIT_START',unit_id=q['id'],condition=c)
    try:row=ex.unit(q['task'],c,q['rep'],'formal',instrument=c.startswith('N'),transfer=1 if c in ['H1','N1'] else 2 if c in ['H0','N0'] else 0)
    except OSError:
        # One retry only for recorded transient I/O. The failed attempt is retained.
        row=ex.unit(q['task'],c,q['rep'],'formal',instrument=c.startswith('N'),transfer=1 if c in ['H1','N1'] else 2 if c in ['H0','N0'] else 0)
    base=OUT/'formal'/(q['task'].replace('/','-')+'-'+c+'-r'+str(q['rep']));p=base/'result.json'
    if 'unit_id' not in row:
        row.update(unit_id=q['id'],freeze_sha256=sha(DOC/'FREEZE.json'),asset_manifest_sha256=sha(DOC/'ASSET_ENVIRONMENT.json'),protocol_sha256=sha(DOC/'PROTOCOL.json'),cohort_sha256=sha(DOC/'COHORT.json'));save(p,row)
    assert row['unit_id']==q['id'] and row['freeze_sha256']==sha(DOC/'FREEZE.json')
    if q['id'] not in existing:g.event('UNIT_VALID',unit_id=q['id'],condition=c,result=str(p.relative_to(ROOT)).replace('\\','/'),result_sha256=sha(p))
    if c in ['R','H0'] and q['task'].startswith('HumanEval/'):
        e=read(DOC/'HISTORICAL_EXPECTED.json')[f"{q['task']}/{c}/{q['rep']}"]
        if row['ids']!=e['ids'] or row['endpoint']!=e['endpoint']:raise RuntimeError('BLOCKED_QUALIFICATION: full old pre-live baseline mismatch '+q['id'])
    with MUTEX:STATE.update(current_unit=None,progress_utc=utc());status()

def seal():
    if (OUT/'PREDICTION_SEAL.json').exists():g.verify_seal();return
    predictions={}
    for q in read(DOC/'QUEUE.json'):
        if q['condition'] not in ['H0','H1']:continue
        p=OUT/'formal'/(q['task'].replace('/','-')+'-'+q['condition']+'-r'+str(q['rep']))/'result.json';x=read(p)
        metadata={f:{'bytes':(p.parent/f).stat().st_size,'mtime_ns':(p.parent/f).stat().st_mtime_ns} for f in x['files']}
        predictions[q['id']]={'result':str(p.relative_to(ROOT)).replace('\\','/'),'sha256':sha(p),'ids':x['ids'],'endpoint':x['endpoint'],'tape_sha256':x['tape_sha256'],'files':x['files'],'metadata':metadata}
    assert len(predictions)==258
    save(OUT/'PREDICTION_SEAL.json',{'study':STUDY,'utc':utc(),'freeze_sha256':sha(DOC/'FREEZE.json'),'protocol_sha256':sha(DOC/'PROTOCOL.json'),'cohort_sha256':sha(DOC/'COHORT.json'),'asset_manifest_sha256':sha(DOC/'ASSET_ENVIRONMENT.json'),'ledger_prefix_sha256':sha(OUT/'LEDGER.jsonl'),'predictions':predictions})
    g.event('PREDICTION_SEALED',seal_sha256=sha(OUT/'PREDICTION_SEAL.json'));g.verify_seal(full=True)

def baseline_recheck():
    rows=[]
    for q in read(DOC/'QUEUE.json'):
        if q['condition'] not in ['R','H0','N0'] or not q['task'].startswith('HumanEval/'):continue
        p=OUT/'formal'/(q['task'].replace('/','-')+'-'+q['condition']+'-r'+str(q['rep']))/'result.json';r=read(p);old=read(DOC/'HISTORICAL_EXPECTED.json')[f"{q['task']}/{q['condition']}/{q['rep']}"]
        rows.append({'unit_id':q['id'],'match':r['ids']==old['ids'] and r['endpoint']==old['endpoint']})
    assert len(rows)==171
    for task in TASKS:
        for c in ['R','H0','N0']:
            outputs=[read(OUT/'formal'/(task.replace('/','-')+'-'+c+'-r'+str(rep))/'result.json') for rep in range(1,4)]
            assert all(x['ids']==outputs[0]['ids'] and x['endpoint']==outputs[0]['endpoint'] for x in outputs)
    save(DOC/'BASELINE_RECHECK.json',{'status':'PASS' if all(r['match'] for r in rows) else 'FAIL','comparisons':171,'rows':rows,'utc':utc()})
    if not all(r['match'] for r in rows):raise RuntimeError('BLOCKED_QUALIFICATION: old native baseline failed; N1 forbidden')

def run():
    g.lock();stop=threading.Event();STATE.update(study=STUDY,controller_pid=os.getpid(),creation_identity=ex.identity(os.getpid()),stage='PREPARE',started_utc=utc(),current_unit=None)
    def heartbeat():
        while not stop.wait(60):
            try:status()
            except Exception:pass
    thread=threading.Thread(target=heartbeat,daemon=True);thread.start();ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
    g.event('CONTROLLER_START',pid=os.getpid(),creation_identity=ex.identity(os.getpid()))
    try:
        advance('PREPARE');advance('G0')
        if not (DOC/'G0_THREADS24.json').exists():qualification.run_g0()
        if not (DOC/'ENGINEERING.json').exists() or read(DOC/'ENGINEERING.json')['status']!='PASS':qualification.engineering()
        if not (DOC/'FIXTURE_RECEIPT.json').exists():
            import fixtures;fixtures.main()
        advance('FREEZE');freeze();checkpoint_assets()
        advance('PREDICTING')
        for q in read(DOC/'QUEUE.json'):
            if q['condition'] in ['R','H0','H1']:formal(q)
        checkpoint_assets();advance('PREDICTION_SEAL');seal()
        advance('REMOTE_READBACK')
        import delivery;delivery.remote_seal()
        checkpoint_assets();advance('N0')
        for q in read(DOC/'QUEUE.json'):
            if q['condition']=='N0':formal(q)
        checkpoint_assets();advance('BASELINE_RECHECK');baseline_recheck();advance('N1')
        for q in read(DOC/'QUEUE.json'):
            if q['condition']=='N1':formal(q)
        checkpoint_assets();advance('INDEPENDENT_VERIFY')
        with (OUT/'independent.stdout.log').open('wb') as so,(OUT/'independent.stderr.log').open('wb') as se:
            subprocess.run([sys.executable,str(HERE/'independent_verify.py')],cwd=ROOT,stdout=so,stderr=se,check=True)
        g.event('MEASUREMENTS_VERIFIED',valid=645)
        advance('ARCHIVE_VERIFY');delivery.archive_and_verify();advance('DELIVERY');delivery.final_delivery()
        STATE.update(status='VERIFIED_COMPLETE',delivery=read(DOC/'DELIVERY_RECEIPT.json')['status']);g.event('COMPLETE',measurements='VERIFIED_COMPLETE',delivery=STATE['delivery']);status()
    except Exception as e:
        error={'utc':utc(),'stage':STATE.get('stage'),'error':repr(e),'traceback':traceback.format_exc()};save(DOC/'STOP_REASON.json',error);g.event('STOP',**error)
        STATE.update(status='PARTIAL_BUDGET' if 'PARTIAL_BUDGET' in str(e) else 'BLOCKED_CAPTURE' if STATE['stage'] in ['PREDICTING','N0','N1'] else 'BLOCKED_QUALIFICATION',last_error=repr(e));status()
        try:
            import delivery;delivery.blocked_delivery()
        except Exception as pe:save(DOC/'DELIVERY_FAILURE.json',{'error':repr(pe),'traceback':traceback.format_exc(),'utc':utc()})
    finally:
        stop.set();thread.join(timeout=5);ctypes.windll.kernel32.SetThreadExecutionState(0x80000000);status()
        p=OUT/'LOCK.json'
        if p.exists() and read(p)['pid']==os.getpid():p.rename(OUT/('LOCK.finished-'+utc().replace(':','-')+'.json'))

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='status':print(json.dumps(read(OUT/'STATUS.json'),ensure_ascii=False))
    else:run()
