"""Fixed paid engineering, bounded profiling, immutable formal schedule."""
from resident import *
import collections, statistics

def ordinary(ub,name=None):
    return dict(name=name or 'ordinary_ub'+str(ub),mode='ordinary',spec=False,prefill_ub=ub,continuation_ub=ub,maximum_k=0,mask=0,required_output_rows=1)
def conditions(d,selected,family):
    a=[]
    for c in d['conditions']:
        c=dict(c)
        if c['name']=='R_prod':c['prefill_ub']=c['continuation_ub']=selected[family]
        a.append(c)
    return {c['name']:c for c in a}
def eng_plan(d):
    jobs=[]
    for f in d['families']:
        for ub in d['ordinary_ub_grid']:
            for repeat in range(2):jobs.append(dict(family=f,name=f'ordinary-{ub}-r{repeat}',condition=ordinary(ub,'R' if ub==1 else None),tasks='families',repeat=repeat,ub=ub))
        fixed={c['name']:c for c in d['conditions'] if c['name'] in ('M0','M3','C3')};fixed['N']=d['diagnostic_N']
        for arm in ['M0','M3','C3','N']:
            for repeat in range(2):jobs.append(dict(family=f,name=arm+'-r'+str(repeat),condition=fixed[arm],tasks='families',repeat=repeat))
        for arm in ['R','M0','M3','C3','N']:
            c=ordinary(1,'R') if arm=='R' else fixed[arm]
            jobs.append(dict(family=f,name='qualification-'+arm,condition=c,tasks='boundary',repeat=0))
    return jobs
def profile_plan(d):
    out=[];modes=d['mechanism']['profile_modes']
    for f in d['families']:
        for arm in d['mechanism']['profile_arms']:
            seq=[]
            for i,t in enumerate(d['mechanism']['calibration_task_ids']):
                order=modes[i%4:]+modes[:i%4]
                for pos,mode in enumerate(order):seq.append(dict(task=t,mode=mode,position=pos))
            out.append(dict(family=f,arm=arm,name='profile-'+arm,slots=seq))
    return out
def records(phase):
    out=[]
    for p in sorted((LOCAL/'runs'/phase).rglob('COMPLETED.json')):
        record=p.parent/'RECORD.json';assert sha(record)==read(p)['record_sha256'];out.append(read(record))
    return out
def run_engineering(ledger):
    d=read(DESIGN/'DESIGN.json');inputs=read(PUB/'ENGINEERING_INPUTS.json');plan=read(PUB/'ENGINEERING_PLAN.json')
    for j in plan['jobs']:
        f=j['family'];name=j['name'];tasks=inputs[j['tasks']][f]
        slots=[f'core/{f}/{name}|'+t['id'] for t in tasks]
        if all(ledger.started(s) for s in slots):continue
        # A crash cannot replay a paid load; resume only unstarted request slots in a new worker.
        load=f'core/{f}/{name}/LOAD'
        if ledger.started(load):name+='-resume-'+str(ledger.count(f,'core','load'))
        status('CORE_ENGINEERING',family=f,block=j['name'],paid=ledger.count(f,'core'))
        cooldown(LOCAL/'cooldown'/('core-'+f+'-'+name+'.json'))
        with Resident(ledger,f,j['condition'],'core',name) as worker:
            worker.complete(inputs['warmups'][f],f'core/{f}/{name}/WARM',warmup=True)
            for t,s in zip(tasks,slots):
                if ledger.started(s):continue
                worker.complete(t,s,meta=dict(repeat=j['repeat'],ub=j.get('ub'),job=j['name']))
    rr=records('core');rows=[];failures=[];qualification={}
    for f in d['families']:
        ref={t['id']:[r for r in rr if r['family']==f and r.get('ub')==1 and r['task']==t['id'] and not r['warmup']] for t in inputs['families'][f]}
        stable=all(len(a)==2 and all(r['contract_valid'] for r in a) and closeout.signature(a[0])==closeout.signature(a[1]) for a in ref.values())
        for r in rr:
            if r['family']!=f or r['warmup'] or r.get('ub')is None:continue
            a=ref[r['task']];rows.append(dict(family=f,ub=r['ub'],task=r['task'],repeat=r['repeat'],phase='exposed_engineering',complete_raw_equal=stable and closeout.signature(r)==closeout.signature(a[0]),contract_valid=r['contract_valid'],reference_stable=stable,wall_ms=r['wall_ms'],slot=r['slot']))
        c3=[r for r in rr if r['family']==f and r['condition']=='C3' and not r['warmup'] and r.get('job','').startswith('C3-r')]
        matched=[r for r in rr if r['family']==f and r['condition']=='M3' and not r['warmup'] and r.get('job','').startswith('M3-r')]
        def equal(a):return len(a)==24 and all(r['contract_valid'] and closeout.signature(r)==closeout.signature(ref[r['task']][0]) for r in a) if stable else False
        bounds=[r for r in rr if r['family']==f and r.get('job')=='qualification-C3' and not r['warmup']]
        refbounds={r['task']:r for r in rr if r['family']==f and r.get('job')=='qualification-R' and not r['warmup']}
        boundary_ok=len(bounds)==len(refbounds)==8 and all(r['contract_valid'] and refbounds[r['task']]['contract_valid'] and closeout.signature(r)==closeout.signature(refbounds[r['task']]) for r in bounds)
        q=dict(stable_reference=stable,C3_complete_raw_equal=equal(c3),M3_complete_raw_equal=equal(matched),C3_boundary_contract=boundary_ok,counter_error_slots=[r['slot'] for r in rr if r['family']==f and r.get('workload_error')])
        qualification[f]=q
        if not(stable and q['C3_complete_raw_equal'] and q['C3_boundary_contract']):failures.append(dict(family=f,reason='FIXED_C3_OR_REFERENCE_ENGINEERING_GATE_FAILED',qualification=q))
    save(PUB/'ORDINARY_ROWS.json',rows);selected=closeout.select_ordinary(rows,d)
    save(PUB/'SELECTED_ORDINARY.json',selected);save(PUB/'ENGINEERING_QUALIFICATION.json',dict(families=qualification,stops=failures,selected=selected,records=len(rr),utc=now()))
    assert not failures,'fixed native/reference engineering blocked; no alternate k/mask search'
    status('ORDINARY_SELECTION_FROZEN',selected=selected)

def audit_heavy(r):
    root=next(p.parent.parent for p in (LOCAL/'runs/profile'/r['family']).rglob('RECORD.json') if read(p)['slot']==r['slot'])
    # root is requests/, trace lives in its parent worker directory.
    path=root.parent/'trace.jsonl';a=r['trace_range'];b=path.read_bytes()[a['start']:a['end']]
    events=[json.loads(line) for line in b.splitlines()];decodes=[e for e in events if e.get('event')=='decode']
    w=r['workload'];expected={role:collections.Counter() for role in ['target','draft']}
    for e in decodes:
        assert e['returncode']==0
        n=e['caller_batch'];ub=e['ub_capacity'];q,rem=divmod(n,ub)
        expected[e['role']][str(ub)]+=q
        if rem:expected[e['role']][str(rem)]+=1
    for role in expected:
        expected[role]={k:v for k,v in expected[role].items() if v}
        assert expected[role]==w[role+'_physical_width_hist'],('physical row mismatch',r['slot'],role)
    proposed=sum(len(e['ids']) for e in events if e.get('event')=='draft_proposal')
    assert proposed==w['proposal_generated']
    ver=[e for e in events if e.get('event')=='verify_result'];assert not any(e['replay'] for e in ver)
    assert len(ver)==w['verify_cycles'] and sum(len(e['proposed_ids']) for e in ver)==w['proposal_verified']
    # Independently replay commit boundaries without altering the original native output array.
    output=r['output']['ids'];first=[e['pending_id'] for e in events if e.get('event')=='first_pending'];assert first==output[:1]
    rebuilt=first[:];outcomes=collections.Counter();prefix=collections.Counter();progress=collections.Counter()
    for e in ver:
        p=e['proposed_ids'];ids=e['accepted_plus_last'];a=len(ids)-1
        available=len(output)-len(rebuilt);committed=ids[:min(len(ids),available)]
        assert committed==output[len(rebuilt):len(rebuilt)+len(committed)]
        actual=min(a,len(committed));outcomes['accepted_committed']+=actual;outcomes['terminal_discarded']+=a-actual
        if a<len(p):outcomes['first_mismatch_rejected']+=1;outcomes['unexamined_after_mismatch']+=len(p)-a-1
        prefix[str(actual)]+=1;progress[str(len(committed))]+=1;rebuilt+=committed
    if r['actual_condition']['spec']:
        # Tail fallback may occur when fewer than two outputs remain; independently account it.
        assert rebuilt==output[:len(rebuilt)]
        for k in ['accepted_committed','terminal_discarded','first_mismatch_rejected','unexamined_after_mismatch']:assert outcomes[k]==w[k]
        assert dict(prefix)==w['accepted_prefix_hist'] and dict(progress)==w['cycle_progress_hist']
    return dict(slot=r['slot'],trace_sha256=hashlib.sha256(b).hexdigest(),decode_events=len(decodes),verification_events=len(ver),physical_histograms=expected,status='PASS')

def run_profile(ledger):
    d=read(DESIGN/'DESIGN.json');inputs=read(PUB/'ENGINEERING_INPUTS.json');selected=read(PUB/'SELECTED_ORDINARY.json')
    for j in read(PUB/'PROFILE_PLAN.json')['jobs']:
        f=j['family'];name=j['name'];c=conditions(d,selected,f)[j['arm']]
        by={t['id']:t for t in inputs['calibration'][f]};slots=['profile/'+f+'/'+j['arm']+'/'+s['mode']+'|'+s['task'] for s in j['slots']]
        if all(ledger.started(s) for s in slots):continue
        if ledger.started('profile/'+f+'/'+name+'/LOAD'):name+='-resume-'+str(ledger.count(f,'profile','load'))
        status('EXPOSED_PROFILING',family=f,arm=j['arm'],paid=ledger.count(f,'profile'))
        cooldown(LOCAL/'cooldown'/('profile-'+f+'-'+name+'.json'))
        with Resident(ledger,f,c,'profile',name) as worker:
            worker.complete(inputs['warmups'][f],'profile/'+f+'/'+name+'/WARM',warmup=True)
            for s,slot in zip(j['slots'],slots):
                if not ledger.started(slot):worker.complete(by[s['task']],slot,mode=s['mode'],meta=dict(profile_mode=s['mode'],position=s['position']))
    rr=[r for r in records('profile') if not r['warmup']];pairs=[];heavy=[];errors=[];cal=[]
    for f in d['families']:
        for arm in d['mechanism']['profile_arms']:
            for t in d['mechanism']['calibration_task_ids']:
                a={r['profile_mode']:r for r in rr if (r['family'],r['condition'],r['task'])==(f,arm,t)}
                equality=set(a)==set(d['mechanism']['profile_modes']) and all(r['contract_valid'] and closeout.signature(r)==closeout.signature(a['baseline']) for r in a.values())
                pairs.append(dict(family=f,condition=arm,task=t,raw_equal=equality,wall_ms={m:r['wall_ms'] for m,r in a.items()},counts_minus_baseline_ms=a['counts']['wall_ms']-a['baseline']['wall_ms'],lite_minus_counts_ms=a['lite']['wall_ms']-a['counts']['wall_ms'],heavy_minus_counts_ms=a['heavy']['wall_ms']-a['counts']['wall_ms']))
                try:heavy.append(audit_heavy(a['heavy']))
                except (AssertionError,KeyError,OSError,StopIteration) as e:errors.append(dict(slot=a['heavy']['slot'],error=repr(e)))
                r=a['lite'];cal.append(dict(slot=r['slot'],family=f,condition=arm,task=t,phase='exposed_profile',profile_mode='lite',wall_ms=r['wall_ms'],feature_units=r['feature_units'],component_ms=None,actual_no_added_sync=r['observation']['added_sync'] is False,completed_wall_partition=r['response']['hs_closeout']['completed_wall_partition'],on_off_raw_equal=equality,source_identity_sha256=r['source_identity_sha256'],raw_evidence_sha256=digest(r),elapsed_hooks=r['response']['hs_closeout']['elapsed_hooks']))
    save(PUB/'OBSERVER_OVERHEAD.json',dict(pairs=pairs,warning='Single paired differences are descriptive and never subtracted from primary wall'))
    save(PUB/'HEAVY_COUNTER_AUDIT.json',dict(status='PASS' if not errors else 'PARTIAL_UNAVAILABLE',rows=heavy,errors=errors))
    save(PUB/'MODEL_CALIBRATION.json',dict(rows=cal,status='COMPLETED_SPANS_UNAVAILABLE',bounded_real_lite_attempt=True))
    model=dict(status='MODEL_TIMING_UNAVAILABLE',design_sha256=digest(d),fit_on_confirmation=False,calibration_task_ids=d['mechanism']['calibration_task_ids'],reason='All72 actual lite requests retained API enqueue and natural sampling-ready timestamps. Pinned llama_context::decode returns after asynchronous output copies, before natural sampling synchronization; target/draft enqueue and completion may overlap. No source-supported mutually exclusive completed wall partition maps these timestamps to the mandated basis including request channel. Extra synchronization would change the protocol. component_ms and coefficients are unavailable; no formal-wall fitting.',actual_lite_rows=len(cal),calibration_sha256=sha(PUB/'MODEL_CALIBRATION.json'))
    save(PUB/'BREAK_EVEN_MODEL.json',model)
    status('PROFILING_COMPLETE',rows=len(rr),model=model['status'],counter_audit_errors=len(errors))

def run_formal(ledger):
    plan=read(PUB/'FORMAL_PLAN.json');inputs=read(PUB/'CONFIRMATION_INPUTS.json');warm=read(PUB/'ENGINEERING_INPUTS.json')['warmups']
    for i,b in enumerate(plan['blocks']):
        remaining=[s for s in b['slots'] if not ledger.started(s['slot'])]
        if not remaining:continue
        f=b['family'];name=f's{b["session"]}-r{b["round"]}-p{b["position"]}-{b["condition"]["name"]}'
        if ledger.started('formal/'+f+'/'+name+'/LOAD'):name+='-resume-'+str(ledger.count(f,'formal','load'))
        status('FORMAL',block=i+1,blocks=150,family=f,arm=b['condition']['name'],started=sum(e['phase']=='formal' and e['kind']=='request' for e in ledger.events))
        cooldown(LOCAL/'cooldown'/('formal-'+f+'-'+name+'.json'))
        by={t['id']:t for t in inputs['families'][f]}
        with Resident(ledger,f,b['condition'],'formal',name) as worker:
            worker.complete(warm[f],'formal/'+f+'/'+name+'/WARM',warmup=True)
            for s in remaining:worker.complete(by[s['task']],s['slot'],meta=dict(session=b['session'],round=b['round'],position=b['position']))
