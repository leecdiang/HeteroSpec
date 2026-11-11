"""Independent engineering gates, ledger counts, selection and reached-stage order."""
import hashlib,json,math
from pathlib import Path
from verify_common import read,require,sha,arr,check_run,difference
import observations
def metadata(root):
    return root/'metadata' if (root/'metadata').exists() else root/'benchmarks/rtx_trajectory_cost_v4'
def launch_order(m,phase,started):
    m=Path(m);p=read(m/'JOINT_PROTOCOL.json')
    if phase=='B_FORMAL' and p['mode']=='A_BLOCKED_B30':return
    if phase=='B_FORMAL' and (m/'A_TERMINAL.json').exists():
        t=read(m/'A_TERMINAL.json');require(t['utc']<started and t['same_cohort_A_resume_forbidden'],'A terminal not prior/irreversible');return
    require((m/'F2_REMOTE_RECEIPT.json').is_file(),'F2 missing before live/B')
    r=read(m/'F2_REMOTE_RECEIPT.json');require(r['full_retrieval_verified'] and r['remote_ack_utc']<started,'F2 chronology/retrieval invalid')
def counts(root,m):
    ledger=[json.loads(x) for x in (m/'EXECUTION_LEDGER.jsonl').read_bytes().splitlines()] if (m/'EXECUTION_LEDGER.jsonl').exists() else []
    reserved=set(read(m/'JOINT_PROTOCOL.json')['A']['task_ids']);actual_process=[e for e in ledger if e.get('event')=='process_started'];calls=[e for e in ledger if e.get('event')=='model_call_completed']
    native_reserved=0;native_unknown=False
    for e in ledger:
        if e.get('event')=='process_completed' and e.get('task_id') in reserved and str(e.get('phase','')).startswith('A_'):
            if e.get('status')!='VALID':native_unknown=True
            if e.get('implementation'):
                try:native_reserved+=len(observations.native(Path(root)/e['record_path']/'native.log')['logical_batches'])
                except (ValueError,KeyError,FileNotFoundError):native_unknown=True
    started_calls=sum(e.get('event')=='model_call_started' and e.get('task_id') in reserved and str(e.get('phase','')).startswith('A_') for e in ledger)
    completed_calls=sum(e.get('task_id') in reserved and str(e.get('phase','')).startswith('A_') for e in calls)
    # Native allocator metadata is not a uniquely identified decode-call log.
    # Its counts cannot establish the distinct reserved-forward denominator.
    native_unknown=native_unknown or started_calls!=completed_calls or native_reserved>0
    return {'A_reserved_processes':sum(e.get('task_id') in reserved and str(e.get('phase','')).startswith('A_') for e in actual_process),'A_reserved_model_forwards':None if native_unknown else sum(e.get('decode_count',0) for e in calls if e.get('task_id') in reserved and str(e.get('phase','')).startswith('A_'))+native_reserved,'A_reserved_live_processes':sum(e.get('phase')=='A_LIVE' for e in actual_process),'B_formal_processes':sum(e.get('phase')=='B_FORMAL' for e in actual_process),'engineering_model_processes':sum(e.get('phase')=='ENGINEERING' for e in actual_process),'worker_logical_forwards':sum(e.get('decode_count',0) for e in calls),'worker_operation_calls':len(calls),'tokenizer_only_processes':sum(e.get('event')=='tokenizer_only_completed' for e in ledger),'tokenizer_only_forwards':sum(e.get('forward_calls',0) for e in ledger if e.get('phase')=='TOKENIZER_ONLY'),'launch_rejections':sum(e.get('event')=='launch_rejected' for e in ledger),'native_allocator_records':sum(e.get('event')=='native_forward_observed' for e in ledger),'ledger_events':len(ledger),'native_forward_count_limit':'Native allocator records include logical and physical metadata, so this is not a distinct logical-forward denominator; zero reserved inference follows no reserved process launch'}
def selection(m):
    a=read(m/'EXPOSURE_AUDIT.json');r=read(m/'RESERVED_SET.json');p=read(m/'JOINT_PROTOCOL.json')
    require(not a['errors'] and a['status'] in ['PASS','RESERVED_POOL_BLOCKED'],'audit incomplete')
    require(len(r['universe'])==164 and set(r['eligible_pool'])==set(a['eligible_pool']),'universe/eligible pool identity')
    eligible=[t for t in r['universe'] if t not in a['exclusion_reasons']];require(set(eligible)==set(r['eligible_pool']),'exclusions do not reproduce pool')
    keys={t:hashlib.sha256((r['salt']+t).encode('utf-8')).hexdigest() for t in eligible};ordered=sorted(eligible,key=lambda t:(keys[t],t))
    require(keys==r['selection_keys'],'salt selection hashes')
    require(len(eligible)==19 and ordered==r['selected_task_ids']==p['A']['task_ids']==p['B']['task_ids'] and p['mode']=='A19_B19','fixed untouched 19-task study')
    return {'status':'PASS','mode':p['mode'],'eligible':len(eligible),'excluded':164-len(eligible),'selected':len(r['selected_task_ids'])}
def engineering(root,m):
    base=read(root/'work/engineering-attempt1/records.json');extra=read(root/'work/engineering-extra/records.json');p=read(m/'JOINT_PROTOCOL.json');runs=base['runs'];tasks=p['engineering']['task_ids'];order=p['engineering']['base_order']
    require(base['status']=='BASE_PASS' and len(runs)==360,'engineering base incomplete')
    require([(r['task_id'],r['repetition'],r['condition']) for r in runs]==[(t,r,c) for t in tasks for r in [1,2,3] for c in order],'fixed exposed engineering schedule')
    require(len({r['run_id'] for r in runs})==360,'duplicate engineering run')
    actual={};obs=[]
    for r in runs+extra['runs']:
        d=root/r['path'];tape=d.parent/r['run_id'].replace('R_ONLY','H2_P_R')/'tape.jsonl' if r['condition']=='R_ONLY' else None
        off=r.get('process_environment_overrides',{}).get('HS_GRAPH_OBSERVER')=='0';v=check_run(d,tape,m,off);require(v['ids']==r['generated_ids'],'engineering manifest arrays differ');actual[(r['task_id'],r['repetition'],r['condition'],str(d.parent))]=v
        if r.get('process_environment_overrides',{}).get('LLAMA_BATCH_DEBUG')=='1':
            o=observations.native(d/'native.log') if r.get('implementation') else observations.worker(d/'events.jsonl');obs.append({'run_id':r['run_id'],'path':r['path'],'physical_group_sizes':o.get('physical_group_sizes'),'worker_logical_forwards':o.get('forward_count')})
    lookup={(r['task_id'],r['repetition'],r['condition']):r for r in runs};gates={'reference':0,'replay':0,'timer_reference':0,'timer_batched':0,'timer_serialized':0};candidate_observations=[]
    for t in tasks:
        for rep in [1,2,3]:
            def ids(c):return lookup[t,rep,c]['generated_ids']
            gates['reference']+=ids('E_ORIGINAL_REFERENCE_UB1')==ids('R_REFERENCE_UB1');gates['replay']+=ids('H2_P_R')==ids('R_ONLY')
            for label,c in [('reference','REFERENCE_UB1'),('batched','BATCHED_K2'),('serialized','SERIALIZED_K2')]:gates['timer_'+label]+=ids('E_ORIGINAL_'+c)==ids('E_TIMER_'+c)
            candidate_observations.append({'task_id':t,'repetition':rep,'UB2_live':difference(ids('E_ORIGINAL_TARGET_ONLY_UB2'),ids('E_ORIGINAL_BATCHED_K2')),'H2_live':difference(ids('H2_P_R'),ids('E_ORIGINAL_BATCHED_K2'))})
    require(all(n==36 for n in gates.values()),'engineering mandatory 36/36 gate failed')
    require(extra['status']=='PASS' and len(extra['runs'])==40 and len(extra['observer_pairs'])==20,'extra engineering count')
    for pair in extra['observer_pairs']:
        on=next(r for r in runs if r['run_id']==pair['on_run_id']);off=next(r for r in extra['runs'] if r['run_id']==pair['off_run_id'] and r['task_id']==pair['task_id']);require(on['generated_ids']==off['generated_ids'],'observer semantic change')
    require(len(extra['endpoint_probes'])==20 and all(x['termination']==('EOS' if x['task_id']=='SYNTH_EOG' else 'limit') and (x['task_id']!='SYNTH_CAP' or x['length']==128) for x in extra['endpoint_probes']),'real inclusive EOG/cap coverage')
    hook=read(root/'work/engineering-extra/CLOCK_PROBE.json');require(len(hook['costs_ns'])==10000,'clock probe count');p99=sorted(hook['costs_ns'])[9900]/1000;shortest=min(r['timer']['milliseconds'] for r in runs+extra['runs'] if r.get('timer'));require(p99==hook['p99_microseconds'] and p99<=10 and p99/1000<.01*shortest,'clock-hook bound')
    from verify_capture_repair import check
    repaired=check(root,m)
    return {'status':'PASS','base_valid_complete_runs':360,'extra_valid_complete_runs':40,'gates':gates,'observer_pairs':20,'endpoint_complete_runs':20,'clock_probe_p99_us':p99,'candidate_observations':candidate_observations,'observations':obs,'constructed_contexts':3,'capture_repair':repaired,'actual_complete_conditions_total':430}
def preparation(root):
    root=Path(root);m=metadata(root);s=selection(m);e=engineering(root,m);c=counts(root,m)
    require(c['A_reserved_processes']==c['A_reserved_model_forwards']==c['A_reserved_live_processes']==c['B_formal_processes']==0,'PREPARE_ONLY reserved/formal execution violation')
    n=read(m/'NEGATIVE_VALIDATION.json');require(n['status']=='PASS' and len(n['cases'])>=12 and all(x['rejected'] for x in n['cases']),'independent negatives missing/accepted')
    require(read(m/'PROTECTED_FILES_CHECK.json')['status']=='PASS','protected scientific files changed')
    return {'status':'PASS','selection':s,'engineering':e,'counts':c,'negative_rejections':len(n['cases']),'formal_stage':'NOT_REACHED'}

def partial(root,m,name):
    """Authenticate a real failed fixed prefix without full-denominator claims."""
    root=Path(root);m=Path(m);mfest=read(root/'work'/name/'records.json');p=read(m/'JOINT_PROTOCOL.json');rows=mfest['runs']
    require(mfest['status'] in ['INCOMPLETE_OPERATIONAL_FAILURE','PROVENANCE_INVALID'],'partial verifier requires explicit failure')
    if name=='B-formal':expected=[(b['task_id'],b['repetition'],c) for b in read(m/'B_matched_cost/schedule.json') for c in b['order']]
    else:expected=[(t,r,c) for t in p['A']['task_ids'] for r in [1,2,3] for c in (p['A']['conditions'][:4] if name=='A-pre-live' else [p['A']['conditions'][4]])]
    require(len(rows)<=len(expected) and [(r['task_id'],r['repetition'],r['canonical_condition']) for r in rows]==expected[:len(rows)],'failed phase is not exact scheduled prefix')
    require(len({r['run_id'] for r in rows})==len(rows),'failed prefix duplicated run');valid=0;failed=0
    for i,r in enumerate(rows):
        require(Path(r['path']).parts[:2]==('work',name),'failed prefix shares engineering/old observation')
        d=root/r['path'];raw=read(d/'record.json');require(raw['run_id']==r['run_id'] and raw['status']==r['status'],'failed prefix raw association')
        stage='F1' if name=='A-pre-live' else 'F2' if name=='A-live' else 'B_START';receipt=read(m/(stage+'_REMOTE_RECEIPT.json'))
        require(receipt['full_retrieval_verified'] and receipt['remote_ack_utc']<mfest['started_utc']<=raw['started_utc'] and raw['source_head']==receipt['commit'],'failed prefix source/remote chronology')
        if name!='A-pre-live':launch_order(m,'B_FORMAL' if name=='B-formal' else 'A_LIVE',mfest['started_utc'])
        if raw['status']=='VALID':
            tape=d.parent/r['run_id'].replace('R_ONLY','H2_P_R')/'tape.jsonl' if r['canonical_condition']=='A_R_ONLY' else None
            v=check_run(d,tape,m);require(v['ids']==r['generated_ids'],'failed prefix valid array');valid+=1
        else:
            require(i==len(rows)-1 and raw['status']=='OPERATIONAL_FAILURE' and raw.get('error'),'failure is not terminal/explicit');failed+=1
            for n,v in raw['files'].items():require((d/n).stat().st_size==v['bytes'] and sha(d/n)==v['sha256'],'failed raw transport lost')
    require(mfest['not_reached']==len(expected)-len(rows) and mfest.get('error'),'failed prefix missing stop/count record')
    return {'status':mfest['status'],'execution_complete':False,'actual_valid_complete_runs':valid,'actual_attempted_runs':len(rows),'actual_failed_runs':failed,'planned_runs':len(expected),'not_reached':len(expected)-len(rows),'speedup':None,'CI':None,'independent':True}
def all_reached(root):
    root=Path(root);m=metadata(root);out={'selection':selection(m),'engineering':engineering(root,m),'counts':counts(root,m)}
    if (root/'work/A-pre-live/records.json').exists():
        if read(root/'work/A-pre-live/records.json')['status']!='COMPLETE':out['A_pre_live']=partial(root,m,'A-pre-live')
        else:
            import verify_A
            out['A_pre_live']=verify_A.pre_live(root,m);out['A_pre_live'].pop('rows')
    if (root/'work/A-live/records.json').exists() and read(root/'work/A-live/records.json')['status']!='COMPLETE':out['A']=partial(root,m,'A-live')
    elif (root/'work/A-live/records.json').exists():
        import verify_A
        out['A']=verify_A.full(root,m)
    if (root/'work/B-formal/records.json').exists() and read(root/'work/B-formal/records.json')['status']!='COMPLETE':out['B']=partial(root,m,'B-formal')
    elif (root/'work/B-formal/records.json').exists():
        import verify_B
        out['B']=verify_B.full(root,m)
    if out['counts']['A_reserved_live_processes'] or out['counts']['B_formal_processes']:
        starts=[]
        for name in ['A-live','B-formal']:
            q=root/'work'/name/'records.json'
            if q.exists():starts.append(read(q)['started_utc'])
        if (m/'F2_REMOTE_RECEIPT.json').exists():require(read(m/'F2_REMOTE_RECEIPT.json')['remote_ack_utc']<min(starts),'F2 not before live/B')
        else:require((m/'A_TERMINAL.json').exists() or read(m/'JOINT_PROTOCOL.json')['mode']=='A_BLOCKED_B30','live/B without F2 or valid A terminal')
    out['status']='PASS';return out
