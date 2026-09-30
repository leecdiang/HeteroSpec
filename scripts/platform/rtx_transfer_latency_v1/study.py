"""One platform, two independent prospective arms; sequential, no overwrite."""
import argparse, ctypes, gzip, hashlib, json, math, os, random, re, shutil, statistics, subprocess, sys, time
from pathlib import Path
import native as n

ROOT=n.ROOT; STUDY=n.STUDY; SOURCE=Path(__file__).parent
BRANCH='experiment/rtx-transfer-and-matched-latency-v1'
MAIN='f8290281156f6b3de8fbc8b44fd10a4afa7bcd89'
DISCOVERY=[f'HumanEval/{i}' for i in (64,106,119,128,129,3,10,19,20,28,32,44)]
PRED=ROOT/'artifacts/rtx_predictive_transfer_v1'; LAT=ROOT/'artifacts/rtx_matched_latency_v1'
TIMER=re.compile(rb'HS_TIMER start_qpc=(\d+) end_qpc=(\d+) frequency=(\d+) start_steady_ns=(\d+) end_steady_ns=(\d+) count=(\d+) terminal_id=(\d+)')

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,v):n.save(p,v)
def prompt_map():
    with gzip.open('D:/HeteroSpec-PC/datasets/humaneval/HumanEval.jsonl.gz','rt',encoding='utf-8') as f:
        return {r['task_id']:n.PROMPT.replace('{humaneval_prompt}',r['prompt']) for r in map(json.loads,f)}
def telemetry():
    return {'utc':n.now(),'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=name,driver_version,temperature.gpu,clocks.current.graphics,clocks.current.memory,utilization.gpu,memory.used,pstate,power.draw','--format=csv,noheader'],text=True).strip()}
def commands():
    ap=n.paths(Path('D:/HeteroSpec-PC'));a=n.templates(ap)
    a['H1_TARGET_UB2']=a['TARGET_REFERENCE'].copy()
    a['H1_TARGET_UB2'][a['H1_TARGET_UB2'].index('--ubatch-size')+1]='2'
    b={c:a[c].copy() for c in ('TARGET_REFERENCE','RTX_SERIALIZED_K2')}
    for cmd in b.values():cmd[0]=str(ROOT/'work/timer-build/bin/llama-cli.exe')
    return a,b
def timer(r,out):
    matches=TIMER.findall((out/r['stderr_path']).read_bytes())
    if len(matches)!=1:raise ValueError('expected exactly one complete native timer event')
    start,end,freq,sns,ens,count,terminal=map(int,matches[0])
    if end<=start or ens<=sns or freq<=0:raise ValueError('nonpositive timer interval')
    ms=(end-start)*1000/freq;secondary=(ens-sns)/1e6
    if abs(ms-secondary)>max(.020,ms*.001):raise ValueError('independent clock records disagree')
    if count!=r['output_length'] or terminal!=r['generated_ids'][-1]:raise ValueError('timer endpoint ID/count differs')
    return {'start_qpc':start,'end_qpc':end,'frequency':freq,'start_steady_ns':sns,'end_steady_ns':ens,
            'output_count':count,'terminal_id':terminal,'milliseconds':ms,'secondary_milliseconds':secondary,
            'boundary':'after synchronized target+draft initial prefill, before per-request sampler creation/seed; through final committed ID, sync and slot release',
            'qualified':True}
def execute(t,rep,c,out,arm,phase,prompt=None):
    a,b=commands();cmds=a if arm=='prediction' else b
    identity=read(STUDY/'asset_identity.json')[arm]
    before=telemetry()
    r=n.execute(t,rep,c,prompt if prompt is not None else prompt_map()[t],cmds,out,identity)
    r.update(arm=arm,phase=phase,device_before=before,device_after=telemetry(),protocol_sha256=n.sha(STUDY/'protocol.json'))
    if arm=='latency' and r['status']=='VALID':
        try:r['timer']=timer(r,out)
        except Exception as e:r.update(status='TIMING_INVALID',error=str(e))
    write(out/'runs'/r['run_id']/'record.json',r)
    print(arm,phase,r['run_id'],r['status'],flush=True)
    return r
def prepare():
    audit_path=STUDY/'exposure_inventory.json'
    if not audit_path.exists():audit_path=ROOT/'work/exposure_inventory.json'
    audit=read(audit_path);assert audit['status']=='PASS'
    a,b=commands();rng=random.Random(2026093001)
    schedule=[]
    for t in n.TASKS:
        for rep in (1,2,3):
            order=['TARGET_REFERENCE','RTX_SERIALIZED_K2'];rng.shuffle(order)
            schedule.append({'task_id':t,'repetition':rep,'order':order})
    protocol={'schema':'heterospec.rtx_transfer_latency.protocol.v1','study_id':'RTX_TRANSFER_AND_MATCHED_LATENCY_V1','starting_main':MAIN,
      'branch':BRANCH,'created_utc':n.now(),'arms_independent':True,'no_shared_formal_observations':True,
      'endpoint':'first 128 native committed generated IDs, or earlier inclusive first EOG; prompt and rejected proposal IDs excluded',
      'decoding':{'target':'Qwen3-8B Q8_0','draft':'Qwen3-0.6B Q8_0','llama_commit':n.LLAMA,'greedy':True,'seed':123,'k':2,'flash_attention':'off','device':'CUDA0','offload':'all','n_ctx':4096,'fresh_process_context':True},
      'fixed_sequence':['joint source preregistration push','shared R0 and B timer R0','joint source and per-arm runtime freeze push','A harness 90-run engineering qualification','A H1 exposed discovery 36 predictor + 36 batched','H2 only if H1 fails and independent proposal construction exists','A selected hypothesis push BEFORE reserved inference','A 144 reserved reference+predictor','A complete prediction file digest commit+push','A 72 reserved batched live','host idle/stability and asset rehash','B 180 randomized paired qualification/timing','independent per-arm verification and archives','draft PR closeout'],
      'prediction':{'question':'Does a discovery-selected predictor transfer prospectively to complete RTX batched trajectories?',
        'task_ids':audit['selected_task_ids'],'eligible_pool':audit['eligible_pool'],'exclusion_reasons':{t:{'sources':v[:5],'source_count':len(v)} for t,v in audit['exclusion_reasons'].items()},
        'selection_salt':audit['selection_salt'],'selection_keys':audit['selection_keys'],'input_hashes':audit['input_hashes'],'exposure_audit_sha256':n.sha(audit_path),
        'discovery_tasks':DISCOVERY,'repetitions':3,'harness_qualification_tasks':n.TASKS,'harness_qualification_runs':90,
        'harness_definition':'original common CLI target-only frontend/sampler UB1, fresh process, empirically reproduces every archived reference; H1 changes only UB2',
        'H1':'target-only common CLI frontend UB2; actual native decode partitions retained; parameter name alone is not mechanism evidence',
        'H2':'fixed proposal target verification replay; permitted only with independent pre-live proposal tape generator. Pinned CLI has no fixed tape importer/generator. No reserved live call is allowed to produce that tape. If no independent generator can be specified, H2 is unavailable and A stops.',
        'decision':'H1 complete discovery equality 36/36 selects H1; otherwise examine H2 availability, require H2 36/36 if implementable; else MECHANISM_NOT_ISOLATED. No H3/search.',
        'commands':a,'reserved_reference_predictor_order':'selection rank; repetitions 1..3; TARGET_REFERENCE then selected predictor',
        'reserved_live_order':'selection rank; repetitions 1..3; RTX_BATCHED_K2','planned_reserved_runs':216,'formal_pairs':72,
        'success':'72/72 full-array predictor/live equality; at least one actual reference-divergent correctly predicted prompt for discrimination',
        'zero_reference_divergent':'NONDISCRIMINATING','repeat_instability':'stop before live, REPEAT_INSTABILITY','harness_failure':'HARNESS_NOT_QUALIFIED'},
      'latency':{'question':'What is matched post-prefill latency on a freshly qualified serialized RTX path?',
        'task_ids':n.TASKS,'repetitions':3,'commands':b,'schedule_seed':2026093001,'schedule':schedule,'planned_runs':180,'formal_pairs':90,
        'timer_start':'after synchronized target and draft initial prompt prefill; before request sampler constructor/seed/reset/prompt acceptance and common_speculative_begin',
        'timer_end':'after last committed generated ID, target/draft synchronization and required slot release; includes final response/log work before release; excludes model destruction',
        'timer_includes':['sampler initialization/seed','draft generation','target verification','acceptance/correction/bonus','synchronization','KV rollback/state cleanup','proposal/scheduling','terminal slot release'],
        'primary_timer':'QueryPerformanceCounter ticks with recorded frequency','secondary_timer':'separate std::chrono::steady_clock start/end record; APIs share Windows clock oscillator',
        'r0_timer_agreement':'absolute difference <= max(0.020 ms, 0.001*QPC interval)',
        'r0_hook_threshold':'10000 pairs of QPC/steady-clock records: p99 empty-hook <= 10 microseconds and p99 < 1% shortest R0 interval; Python ctypes probe provides conservative clock-call overhead bound',
        'qualification':'90/90 complete new serialized/reference ID arrays AND 180 valid native timer/device records; otherwise no speed estimate',
        'estimator':'for each prompt median of 3 reference milliseconds divided by median of 3 serialized milliseconds; geometric mean over 30 prompt ratios',
        'bootstrap':{'unit':'distinct prompt','samples':10000,'seed':2026093002,'percentiles':'linear interpolation at .025 and .975','task_input_order':'numeric original 30 task order'},
        'failure_statuses':['TIMING_INVALID','QUALIFICATION_BLOCKED','INCOMPLETE_OPERATIONAL_FAILURE'],
        'thermal_rule':{'pre_B':'minimum 120s idle; three 10s-separated samples utilization<=5%, GPU temp<=55C, spread<=2C; maximum 600s then operational stop',
                        'pre_each_run':'fixed 2s idle; thermal/device snapshots before and after, no outcome-dependent delays','clock_lock':'no unsupported clock lock; observed clocks preserved; prompt pairing randomized'},
        'energy_claims':False},
      'planned_counts':{'A_reserved':216,'B_formal':180,'base_formal':396,'A_harness':90,'A_discovery_H1':72,'R0':23,'H2_if_available':'36 replay plus separately counted tape generation'},
      'failures':'retain every failure/mismatch; mismatch continues, operational failure stops affected arm; no selective replacement/restart after formal data; A failure does not alter frozen B',
      'immutable':'old v2, old timing, manuscripts and PR40 untouched; no auto merge'}
    write(STUDY/'protocol.json',protocol)
    # Store the large complete audit in the evidence package, not as bulk Git logs.
    if audit_path!=ROOT/'work/exposure_inventory.json':shutil.move(audit_path,ROOT/'work/exposure_inventory.json')
    summary={k:v for k,v in audit.items() if k not in ('catalog','evidence','exclusion_reasons')}
    summary['full_audit_sha256']=n.sha(ROOT/'work/exposure_inventory.json')
    summary['exclusion_reasons']=protocol['prediction']['exclusion_reasons']
    write(STUDY/'RESERVED_SET.json',summary)
    assets=n.identities(n.paths(Path('D:/HeteroSpec-PC')))
    bm=read(STUDY/'timer_build_manifest.json')
    bassets=json.loads(json.dumps(assets));bassets['binary_dir']=bm['binary_dir'];bassets['binaries']=bm['binaries'];bassets['version']='b10839/0cae43063, isolated timer frontend, Clang 21.1.0, original CUDA backend DLLs'
    write(STUDY/'asset_identity.json',{'prediction':assets,'latency':bassets})
    write(STUDY/'environment.json',n.environment())
    (STUDY/'PREREGISTRATION.md').write_text('''# RTX transfer and freshly qualified matched latency v1

One RTX platform campaign with two independent arms. The complete user-supplied specification is retained as USER_SPECIFICATION.md. protocol.json is the machine-readable authority. Both source/timer and B R0 are frozen before A discovery. Known historical observations informed design, but no historical observation enters either formal denominator. No positive outcome is required.

A excludes every recorded or ambiguous task exposure across audited accessible scientific directories and archive members, including prior RTX, B570 reserved and other-platform results. Universe/input-only listings explicitly marked unused do not establish output exposure. Select exactly 24 from 61 eligible IDs by the fixed salt and full task ID SHA-256 ordering. No reserved inference precedes hypothesis commit AND remote acknowledgement. H1 requires 36/36 discovery; H2 has a separate independent-tape prerequisite. A scientific stop leaves B unchanged. The common CLI reference harness is empirical (90/90 old references), and its UB2 target-only decode does not become speculative verification merely by the UB2 parameter.

B uses the old 30 IDs with entirely new 180 executions. Its isolated build moves request sampler initialization to after synchronized initial prefill. Timing includes the complete loop, terminal synchronization, response/log work and slot release. It excludes model loading, target/draft initial prefill and process teardown. Both QPC and a separately implemented chrono record capture endpoints; these share Windows' oscillator. Empty clock-call overhead is bounded before formal runs. Changed build bytes have no inherited v2 qualification. Only new 90/90 equality and all 180 timers/device checks permit the predeclared prompt-median-ratio geometric mean and 10,000 prompt bootstrap. No energy claim.

Fixed phase order, commands, tasks, pairing, gates, failure handling and complete counts are in protocol.json. Every inference has a fresh process/context and native committed-ID capture read losslessly as bytes. Raw logs, all arrays, hashes, exact commands and pre/post device state are retained separately per arm. No mismatch is dropped and no run is selectively replaced. Performance is never estimated for A's batched path. Old artifacts and paper files are read-only. Final delivery is one draft PR with two reports, two independent verifiers, two content-addressed evidence packages and a joint chronology; never automatic merge.
''',encoding='utf-8',newline='\n')
    print('Prepared protocol and assets',flush=True)

def r0():
    out=ROOT/'work/joint-r0';out.mkdir(exist_ok=False)
    results={'started_utc':n.now(),'formal':False,'runs':[],'status':'STARTED'};write(out/'r0.json',results)
    for t in ('HumanEval/3','HumanEval/106','HumanEval/50'):
        for c in ('TARGET_REFERENCE','RTX_BATCHED_K2','H1_TARGET_UB2'):
            r=execute(t,1,c,out/'prediction','prediction','R0');results['runs'].append(r);write(out/'r0.json',results)
            if r['status']!='VALID':raise RuntimeError(r.get('error'))
        for c in ('TARGET_REFERENCE','RTX_SERIALIZED_K2'):
            baseline=execute(t,1,c,out/'original-b','prediction','R0')
            r=execute(t,1,c,out/'latency','latency','R0');results['runs'] += [baseline,r]
            if r['status']!='VALID' or baseline['status']!='VALID' or r['generated_ids']!=baseline['generated_ids']:
                results['status']='TIMING_INVALID';write(out/'r0.json',results);raise RuntimeError('timer build changed IDs or timer failed')
            write(out/'r0.json',results)
    # A synthetic non-HumanEval input explicitly exercises inclusive EOG.
    synthetic='Reply with only OK.'
    for c in ('TARGET_REFERENCE','RTX_SERIALIZED_K2'):
        r=execute('R0_EOG',1,c,out/'latency','latency','R0_EOG',synthetic);results['runs'].append(r)
        if r['status']!='VALID' or r['termination']!='EOS':raise RuntimeError('R0 missing inclusive EOG test')
    qpc=ctypes.windll.kernel32.QueryPerformanceCounter;freq=ctypes.c_longlong();ctypes.windll.kernel32.QueryPerformanceFrequency(ctypes.byref(freq))
    costs=[]
    for _ in range(10000):
        st=time.perf_counter_ns();q=ctypes.c_longlong();qpc(ctypes.byref(q));time.perf_counter_ns();qpc(ctypes.byref(q));time.perf_counter_ns();costs.append(time.perf_counter_ns()-st)
    p99=sorted(costs)[9900]/1000;shortest=min(r['timer']['milliseconds'] for r in results['runs'] if r.get('timer'))
    results['hook_probe']={'samples':10000,'p99_microseconds':p99,'shortest_r0_ms':shortest,'threshold_us':10,'relative_threshold':.01,'PASS':p99<=10 and p99/1000<shortest*.01}
    if not results['hook_probe']['PASS']:raise RuntimeError('timer clock hook overhead exceeds predeclared threshold')
    results.update(status='PASS',ended_utc=n.now());write(out/'r0.json',results);write(STUDY/'R0_REVIEW.json',results)

def assets_ok():
    ids=read(STUDY/'asset_identity.json')
    for arm in ('prediction','latency'):
        for k in ('target','draft','dataset'):
            assert n.sha(ids[arm][k]['path'])==ids[arm][k]['sha256'],(arm,k)
        for name,h in ids[arm]['binaries'].items():assert n.sha(Path(ids[arm]['binary_dir'])/name)==h,(arm,name)
    env=n.environment();old=read(STUDY/'environment.json')
    for k in ('gpu','os','python','runtime_override_variables'):assert env[k]==old[k],k
    return {'utc':n.now(),'status':'PASS','environment':env}
def freeze():
    assert read(STUDY/'R0_REVIEW.json')['status']=='PASS'
    assert not n.git('status','--porcelain')
    assert n.git('branch','--show-current')==BRANCH
    audit=assets_ok()
    paths=list(SOURCE.glob('*.py'))+list(STUDY.glob('*'))
    paths=[p for p in paths if p.is_file() and p.name!='runtime_freeze.json']
    manifest={'source_commit':n.git('rev-parse','HEAD'),'source_tree':n.git('rev-parse','HEAD^{tree}'),
        'utc':n.now(),'arm_sources_frozen_together':True,'files':{p.relative_to(ROOT).as_posix():n.sha(p) for p in paths},
        'asset_rehash':audit,'r0_sha256':n.sha(STUDY/'R0_REVIEW.json')}
    write(STUDY/'runtime_freeze.json',manifest)
def guard():
    f=read(STUDY/'runtime_freeze.json')
    for p,h in f['files'].items():assert n.sha(ROOT/p)==h,('source_changed',p)
    assert n.git('branch','--show-current')==BRANCH
    return f
def phase(name,arm,schedule):
    guard();out=(PRED if arm=='prediction' else LAT)/name;out.mkdir(parents=True,exist_ok=False)
    data={'arm':arm,'phase':name,'started_utc':n.now(),'execution_head':n.git('rev-parse','HEAD'),
      'freeze_sha256':n.sha(STUDY/'runtime_freeze.json'),'schedule':schedule,'runs':[],'status':'STARTED'};write(out/'records.json',data)
    for t,rep,c in schedule:
        guard()
        if arm=='latency':time.sleep(2)
        r=execute(t,rep,c,out,arm,name);data['runs'].append(r);write(out/'records.json',data)
        if r['status']!='VALID':
            data.update(status='TIMING_INVALID' if r['status']=='TIMING_INVALID' else 'INCOMPLETE_OPERATIONAL_FAILURE',ended_utc=n.now())
            write(out/'records.json',data);return data
    data.update(status='COMPLETE',ended_utc=n.now(),post_execution_rehash=assets_ok());write(out/'records.json',data)
    return data
def prediction():
    qual=phase('harness_qualification','prediction',[(t,r,'TARGET_REFERENCE') for t in n.TASKS for r in (1,2,3)])
    old=read(ROOT/'work/old-reference/formal_records.json')
    archive={(r['task_id'],r['repetition']):r['generated_ids'] for r in old['runs'] if r['condition']=='TARGET_REFERENCE'}
    matches=sum(r.get('generated_ids')==archive[(r['task_id'],r['repetition'])] for r in qual['runs'])
    if qual['status']!='COMPLETE' or matches!=90:
        result={'status':'HARNESS_NOT_QUALIFIED','matches':matches,'required':90,'reserved_runs':0};write(STUDY/'prediction/REPORT.json',result);return
    discovery=phase('discovery_H1','prediction',[(t,r,c) for t in DISCOVERY for r in (1,2,3) for c in ('H1_TARGET_UB2','RTX_BATCHED_K2')])
    keyed={(r['task_id'],r['repetition'],r['condition']):r for r in discovery['runs']}
    comparisons=[]
    if discovery['status']=='COMPLETE':
        for t in DISCOVERY:
            for rep in (1,2,3):
                a=keyed[t,rep,'H1_TARGET_UB2']['generated_ids'];b=keyed[t,rep,'RTX_BATCHED_K2']['generated_ids']
                comparisons.append({'task_id':t,'repetition':rep,'exact':a==b,'first_divergence':divergence(a,b)})
    count=sum(r['exact'] for r in comparisons)
    result={'status':'H1_SELECTED' if count==36 else ('MECHANISM_NOT_ISOLATED' if discovery['status']=='COMPLETE' else discovery['status']),
      'harness_matches':matches,'discovery_complete_matches':count,'discovery_total':36,'comparisons':comparisons,
      'H2':'UNAVAILABLE: no independent fixed-proposal generator/import interface frozen; reserved live proposal access forbidden',
      'reserved_runs':0,'utc':n.now()}
    write(STUDY/'prediction/REPORT.json',result)
    if count!=36:return
    hypothesis={'selected':'H1_TARGET_UB2','utc':n.now(),'discovery_matches':36,'protocol_sha256':n.sha(STUDY/'protocol.json'),
                'source_files':read(STUDY/'runtime_freeze.json')['files'],'reserved_tasks':read(STUDY/'protocol.json')['prediction']['task_ids']}
    write(STUDY/'prediction/HYPOTHESIS_FREEZE.json',hypothesis)
    commit_push('Freeze discovery-selected RTX predictor before any reserved inference')
    remote_checkpoint('hypothesis')
    reserved=read(STUDY/'protocol.json')['prediction']['task_ids']
    pred=phase('reserved_prediction','prediction',[(t,r,c) for t in reserved for r in (1,2,3) for c in ('TARGET_REFERENCE','H1_TARGET_UB2')])
    if pred['status']!='COMPLETE':result['status']=pred['status'];write(STUDY/'prediction/REPORT.json',result);return
    k={(r['task_id'],r['repetition'],r['condition']):r for r in pred['runs']}
    if any(len({tuple(k[t,r,c]['generated_ids']) for r in (1,2,3)})!=1 for t in reserved for c in ('TARGET_REFERENCE','H1_TARGET_UB2')):
        result['status']='REPEAT_INSTABILITY';write(STUDY/'prediction/REPORT.json',result);return
    rows=[]
    for t in reserved:
        for rep in (1,2,3):
            a=k[t,rep,'TARGET_REFERENCE']['generated_ids'];b=k[t,rep,'H1_TARGET_UB2']['generated_ids']
            rows.append({'task_id':t,'repetition':rep,'reference':a,'prediction':b,'reference_sha256':n.array_sha(a),
              'prediction_sha256':n.array_sha(b),'predicted_reference_equal':a==b,'predicted_first_divergence':divergence(a,b)})
    file=STUDY/'prediction/RESERVED_PREDICTIONS.json'
    assert not file.exists();write(file,{'utc':n.now(),'rows':rows})
    write(STUDY/'prediction/PREDICTION_DIGEST.json',{'sha256':n.sha(file),'utc':n.now()})
    commit_push('Freeze all 72 RTX complete predictions before reserved live outputs');remote_checkpoint('predictions')
    live=phase('reserved_live','prediction',[(t,r,'RTX_BATCHED_K2') for t in reserved for r in (1,2,3)])
    if live['status']!='COMPLETE':result['status']=live['status'];write(STUDY/'prediction/REPORT.json',result);return
    lk={(r['task_id'],r['repetition']):r['generated_ids'] for r in live['runs']}
    result['reserved_comparisons']=[dict(row,predictor_live_equal=row['prediction']==lk[row['task_id'],row['repetition']],
       reference_live_equal=row['reference']==lk[row['task_id'],row['repetition']],actual_first_divergence=divergence(row['reference'],lk[row['task_id'],row['repetition']])) for row in rows]
    result['predictor_live_matches']=sum(r['predictor_live_equal'] for r in result['reserved_comparisons'])
    result['reference_divergent_tasks']=sorted({r['task_id'] for r in result['reserved_comparisons'] if not r['reference_live_equal']})
    result['status']=('NONDISCRIMINATING' if not result['reference_divergent_tasks'] else 'PREDICTION_VALIDATED') if result['predictor_live_matches']==72 else 'PREDICTION_NOT_FULLY_VALIDATED'
    result['reserved_runs']=216;write(STUDY/'prediction/REPORT.json',result)
def divergence(a,b):
    for i in range(max(len(a),len(b))):
        if i>=len(a) or i>=len(b) or a[i]!=b[i]:return {'index':i,'reference_id':a[i] if i<len(a) else None,'candidate_id':b[i] if i<len(b) else None}
    return None
def commit_push(message):
    subprocess.run(['git','add','benchmarks/rtx_transfer_latency_v1'],cwd=ROOT,check=True)
    subprocess.run(['git','commit','-m',message],cwd=ROOT,check=True)
    subprocess.run(['git','push','origin',BRANCH],cwd=ROOT,check=True)
def remote_checkpoint(name):
    head=n.git('rev-parse','HEAD');remote=n.git('ls-remote','origin','refs/heads/'+BRANCH).split()[0];assert head==remote
    write(STUDY/'chronology'/f'{name}.json',{'commit':head,'remote_ref':remote,'remote_ack_utc':n.now()})
def stabilize():
    samples=[];start=time.monotonic();time.sleep(120)
    while time.monotonic()-start<=600:
        raw=subprocess.check_output(['nvidia-smi','--query-gpu=temperature.gpu,utilization.gpu','--format=csv,noheader,nounits'],text=True)
        temp,util=map(int,raw.strip().split(','));samples.append({'utc':n.now(),'temperature':temp,'utilization':util})
        last=samples[-3:]
        if len(last)==3 and all(x['temperature']<=55 and x['utilization']<=5 for x in last) and max(x['temperature'] for x in last)-min(x['temperature'] for x in last)<=2:
            write(STUDY/'latency/THERMAL_PRECHECK.json',{'status':'PASS','samples':samples,'asset_rehash':assets_ok()});return
        time.sleep(10)
    raise RuntimeError('predeclared thermal stability condition not met within 600s')
def percentile(x,p):
    x=sorted(x);position=(len(x)-1)*p;low=int(position);return x[low]+(x[min(low+1,len(x)-1)]-x[low])*(position-low)
def analyze_latency(data):
    if data['status']!='COMPLETE':return {'status':data['status'],'formal_runs':len(data['runs']),'speedup':None}
    k={(r['task_id'],r['repetition'],r['condition']):r for r in data['runs']};matches=0;rows=[];pairs=[]
    for t in n.TASKS:
        for rep in (1,2,3):
            a=k[t,rep,'TARGET_REFERENCE']['generated_ids'];b=k[t,rep,'RTX_SERIALIZED_K2']['generated_ids'];matches+=a==b
            pairs.append({'task_id':t,'repetition':rep,'exact':a==b,'first_divergence':divergence(a,b)})
        ref=statistics.median(k[t,r,'TARGET_REFERENCE']['timer']['milliseconds'] for r in (1,2,3))
        ser=statistics.median(k[t,r,'RTX_SERIALIZED_K2']['timer']['milliseconds'] for r in (1,2,3))
        rows.append({'task_id':t,'reference_median_ms':ref,'serialized_median_ms':ser,'ratio':ref/ser})
    result={'status':'QUALIFIED' if matches==90 else 'QUALIFICATION_BLOCKED','exact_pairs':matches,'total_pairs':90,'formal_runs':180,'comparisons':pairs,'per_prompt':rows,'speedup':None}
    if matches!=90:return result
    logs=[math.log(r['ratio']) for r in rows];mean=math.exp(sum(logs)/30);rng=random.Random(2026093002)
    boots=[math.exp(sum(logs[rng.randrange(30)] for _ in range(30))/30) for _ in range(10000)]
    result.update(speedup=mean,bootstrap_95_ci=[percentile(boots,.025),percentile(boots,.975)],faster_prompts=sum(r['ratio']>1 for r in rows),bootstrap_samples=10000,bootstrap_seed=2026093002,unit='distinct prompt',energy_claim=False)
    return result
def latency():
    stabilize();p=read(STUDY/'protocol.json')['latency'];schedule=[(b['task_id'],b['repetition'],c) for b in p['schedule'] for c in b['order']]
    data=phase('formal','latency',schedule);write(STUDY/'latency/REPORT.json',analyze_latency(data))
def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['prepare','r0','freeze','prediction','latency','campaign']);a=p.parse_args()
    if a.stage=='prepare':prepare()
    elif a.stage=='r0':r0()
    elif a.stage=='freeze':freeze()
    elif a.stage=='prediction':prediction()
    elif a.stage=='latency':latency()
    else:
        guard();remote_checkpoint('joint_freeze')
        try:prediction()
        except Exception as e:write(STUDY/'prediction/REPORT.json',{'status':'INCOMPLETE_OPERATIONAL_FAILURE','error':str(e),'utc':n.now()})
        try:latency()
        except Exception as e:write(STUDY/'latency/REPORT.json',{'status':'INCOMPLETE_OPERATIONAL_FAILURE','error':str(e),'utc':n.now(),'speedup':None})
        write(ROOT/'work/campaign-status.json',{'status':'EXECUTION_ENDED','utc':n.now()})
if __name__=='__main__':main()
