"""Separate32 target-replay measurements and64 live descriptive pilot tests."""
from collections import defaultdict
from pathlib import Path
import copy,datetime,json,time
import harness as h
from qualify import dispatch_gate

CUTOFF=datetime.datetime(2026,11,8,21,0,tzinfo=datetime.timezone.utc)
def may_start():return (CUTOFF-datetime.datetime.now(datetime.timezone.utc)).total_seconds()>=960

def selection(s):
    read,save,sha,need=h.read,h.save,h.sha,h.need
    if s.prior_manifest is not None:
        p=s.prior/'ROOT_SELECTION.json';s.verify(p)
        import shutil
        shutil.copy2(p,s.w/'ROOT_SELECTION.json')
        save(s.w/'ROOT_SELECTION_REUSE.json',dict(prior_sha256=sha(p),current_sha256=sha(s.w/'ROOT_SELECTION.json'),
            unchanged_original_pre_candidate_selection=True,no_new_root_selection=True))
        return
    roots=read(s.root/'m1-run-01/panel-01/PLAN.json')['roots'][:4]
    bank=read(s.baseline/'stage-04/authenticated-kit/samples/R2-INPUTS.json')['inputs']
    primers=read(s.baseline/'inputs-01/PRIMERS.json')['inputs'];lookup={x['id']:x for x in bank+primers}
    need(len(set(roots))==4 and not set(roots)&{x['id']for x in primers},'Four exposed roots and two distinct primers')
    old=read(s.baseline/'panel-01/PLAN.json');order=old['workers'][0]['primers']+old['workers'][0]['roots'];ref=s.baseline/'panel-01/reference-01'
    for p in (ref/'launch.json',ref/'HOST.json',s.baseline/'panel-01/REFERENCE-JOB.json'):s.verify(p)
    need(read(ref/'HOST.json')['status']=='COMPLETE' and read(ref/'launch.json')['build_sha256']==h.sha(s.ref_build),'Original autonomous panel R binding')
    expected={}
    for key in roots+[x['id']for x in primers]:
        path=ref/'native'/('reference-'+str(order.index(key)))/'receipt.json';s.verify(path);expected[key]=dict(receipt=read(path),path=str(path),sha256=sha(path))
    save(s.w/'ROOT_SELECTION.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),roots=roots,primers=[x['id']for x in primers],
        rule='First four roots in immutable completed M1 root list; fixed before any new M2 candidate outputs, no selection by M2 speed/acceptance',
        sample_scope='Exposed deployment-transfer pilot, not new blind roots or population confirmation',new_candidate_outputs_seen=0,
        old_M1_plan_sha256=sha(s.root/'m1-run-01/panel-01/PLAN.json'),expected=expected,inputs={key:lookup[key]for key in expected}))

def tapes_and_gate(s):
    read,save,sha,need=h.read,h.save,h.sha,h.need
    chosen=read(s.w/'ROOT_SELECTION.json');requests=[];lookup={}
    for i,(key,item) in enumerate(chosen['expected'].items()):
        x=chosen['inputs'][key];requests.append(dict(name='panel-'+str(i),root=key,prompt_ids=x['prompt_ids'],greedy_ids=item['receipt']['ids'],autonomous_R_receipt_sha256=item['sha256']));lookup[key]='panel-'+str(i)
    dev=read(s.baseline/'inputs-01/Qwen-DEVELOPMENT.json')['inputs'][0];free=s.retained('Qwen-free-independent-R')/'native/dev-0'
    fixture=read(s.out/'EOG_FIXTURE_REGISTERED.json')['input'];ep=s.custom_reference[('Qwen',4)]
    requests.append(dict(name='qualification-short',root='qualification-short',prompt_ids=dev['prompt_ids'],greedy_ids=read(free/'receipt.json')['ids'][:16],autonomous_R_receipt_sha256=sha(free/'receipt.json')))
    requests.append(dict(name='qualification-eog',root='qualification-eog',prompt_ids=fixture['prompt_ids'],greedy_ids=read(ep/'receipt.json')['ids'],autonomous_R_receipt_sha256=sha(ep/'receipt.json')))
    actual=s.execute('native-owned-tape-producer','Qwen',dict(proposal_tape_requests=requests,lowering='LOCAL'),'loop4',7,'producer')
    meta=read(actual/'native/result.json');need(len(meta['proposal_tapes'])==8,'All owned native tapes produced')
    tapes={}
    for row in meta['proposal_tapes']:
        p=actual/'native'/row['path'];x=read(p);need(h.canonical(x)==row['canonical_tape_sha256'],'Native tape content identity')
        need(row['target_calls']==row['target_rows']==0 and row['draft_rows']>0,'Draft-only known-tape producer, no target replay masquerading as live drafting')
        tapes[row['root']]=dict(tape=x,canonical_sha256=row['canonical_tape_sha256'],file_sha256=sha(p),path=str(p),producer_record=row)
    save(s.w/'OWNED_TAPES_FROZEN.json',dict(passed=True,native_result_sha256=sha(actual/'native/result.json'),tapes=tapes,
        rule='Same position-indexed seven-proposal tape for both k3 first3 and k7 all7, all four cut/projection paths; tape production cost separate from replay and live service'))
    proofs=[]
    for arm,(core,cut,k) in h.ARMS.items():
        for name,index,base in [('qualification-short',0,{**dev,'cap':16}),('qualification-eog',4,fixture)]:
            tape=tapes[name];x={**base,'proposal_tape':tape['tape'],'proposal_tape_sha256':tape['canonical_sha256']}
            actual=s.execute('owned-tape-gate-'+arm+'-'+name,'Qwen',dict(lowering=cut,inputs=[dict(name='heavy',input=x,capture=True),dict(name='clean',input=x,capture=False)]),core,k,'replay')
            proof=s.check_pair('Qwen',index,x,actual,'heavy','clean');dispatch_gate(proof,core,cut,k)
            path=s.out/('OWNED-TAPE-'+arm+'-'+name+'-CHECKED.json');save(path,dict(passed=True,arm=arm,tape_sha256=tape['canonical_sha256'],proof=proof));proofs.append(path)
            print('M2_OWNED_TAPE_REPLAY_PASS',arm,name,flush=True)
    save(s.out/'OWNED-TAPE-REPLAY-CHECKED.json',dict(passed=True,proofs=[dict(path=str(p),sha256=sha(p))for p in proofs],
        both_k_same_owned_tape=True,full_vectors_active_KV_frontier_transactions=True,zero_draft_calls_in_replay=True))

def prepare(s):
    read,save,sha,need=h.read,h.save,h.sha,h.need
    chosen=read(s.w/'ROOT_SELECTION.json');tapes=read(s.w/'OWNED_TAPES_FROZEN.json')['tapes'];out=s.w/'panel-01';out.mkdir()
    arms=list(h.ARMS);row=[arms[i]for i in (0,1,7,2,6,3,5,4)];orders=[row,list(reversed(row))]
    workers=[]
    for mode,sessions in [('replay',1),('live',2)]:
        for session in range(sessions):
            for arm in orders[session]:
                core,cut,k=h.ARMS[arm];keys=chosen['primers']+(chosen['roots']if session==0 else list(reversed(chosen['roots'])))
                inputs=[]
                for i,key in enumerate(keys):
                    x=copy.deepcopy(chosen['inputs'][key])
                    if mode=='replay':x.update(proposal_tape=tapes[key]['tape'],proposal_tape_sha256=tapes[key]['canonical_sha256'])
                    inputs.append(dict(name='request-'+str(i),input=x,capture=False))
                job={**s.models['Qwen'],'draft':True,'draft_width':4,'lowering':cut,'residency':'matched','profile':False,
                    'k':k,'target_output_reserve':8,'proposal_mode':mode,'capability_request':h.capability(s.models['Qwen'],s.structures['Qwen'],core,cut,k,mode),'inputs':inputs}
                name=f'M2-{mode}-s{session}-{arm}';path=out/(name+'.json');save(path,job)
                workers.append(dict(id=name,arm=arm,core=core,k=k,proposal_mode=mode,session=session,job=path.name,job_sha256=sha(path),
                    primers=chosen['primers'],roots=keys[2:]))
    plan=dict(schema='heterospec.m2.descriptive-plan.v1',study='server_m2_v1',panel='width_pilot_plus_separate_target_replay',
        workers=workers,roots=chosen['roots'],arms=arms,measurements=96,primers=48,
        live_pilot=dict(roots=4,arms=8,sessions=2,measurements=64,primers=32,inference='DESCRIPTIVE_ONLY'),
        target_replay=dict(roots=4,arms=8,sessions=1,measurements=32,primers=16,inference='MECHANISM_DESCRIPTION_ONLY'),
        order_rows=orders,order_scope='Pilot rows reverse all arm precedences and complementary positions; only two of eight possible rows, not full position/neighbor balance. Replay one row only.',
        confirmation576='PROHIBITED_NOT_QUEUED',original_k3_reserve4_baseline='UNCHANGED_SEPARATE_CONFIGURATION')
    need(len(workers)==24,'Original exact24-slot supervisor guard retained');save(out/'PLAN.json',plan)
    registry=read(s.out/'REGISTRY.json');registry['checks']['owned_proposal_tape_replay']=dict(passed=True,evidence=str(s.out/'OWNED-TAPE-REPLAY-CHECKED.json'))
    for summary in (s.out/'NATIVE_CHECKS_COMPLETE.json',s.out/'OWNED-TAPE-REPLAY-CHECKED.json'):
        for row in read(summary)['proofs']:need(sha(row['path'])==row['sha256'] and read(row['path'])['passed'],'Immutable qualified proof changed before freeze')
    for name,digest in read(s.w/'SOURCE_FREEZE.json')['driver_sources'].items():need(sha(name)==digest,'Qualified driver source bytes changed')
    save(out/'REGISTRY-COMPLETE.json',registry)
    h.freeze.confirmation(s.baseline/'reference-01/REFERENCE_FREEZE.json',out/'REGISTRY-COMPLETE.json',out/'PLAN.json',out/'FREEZE.json')
    cfg=read(s.cfg);cfg.update(freeze=str(out/'FREEZE.json'),freeze_sha256=sha(out/'FREEZE.json'));save(out/'config.private.json',cfg)

def run(s):
    read,save,sha,need=h.read,h.save,h.sha,h.need
    out=s.w/'panel-01';plan=read(out/'PLAN.json');chosen=read(s.w/'ROOT_SELECTION.json');records=[];slots={w['id']:'NOT_RUN'for w in plan['workers']}
    need(read(s.out/'NATIVE_CHECKS_COMPLETE.json')['passed'] and read(s.out/'OWNED-TAPE-REPLAY-CHECKED.json')['passed'],'Both complete native stages required')
    try:
        for worker in plan['workers']:
            need(may_start(),'Insufficient960s margin before05:00 cutoff; no new worker, retain all completed/partial slots')
            name=worker['id'];dest=out/'runs'/name;slots[name]='STARTED';job=out/worker['job'];started=time.monotonic()
            h.host.run(out/'config.private.json',s.builds/worker['core']/'BUILD.json',job,dest,'confirmation');wrapper=time.monotonic()-started
            payload=read(job);meta=read(dest/'native/result.json');need(meta['native_capability']==payload['capability_request'],'Actual full native contract')
            need(meta['total_observed_API_calls']['context_creates']==2,'Exactly one matched resident pair per worker')
            calls=[]
            for i,(key,entry)in enumerate(zip(worker['primers']+worker['roots'],payload['inputs'])):
                path=dest/'native'/entry['name']/'receipt.json';r=read(path);expected=chosen['expected'][key]
                need(h.native.endpoint(r)==h.native.endpoint(expected['receipt']),'Frozen independent R endpoint mismatch')
                r['study_cap']=entry['input']['cap'];_,decoded=h.trace(r,entry['input']['prompt_ids'],meta['vocab'],meta['eog_ids'],'rtx')
                need(all(v==0 for v in r['observed_API_calls_within_service'].values()),'Clean service performed state transfer/context/heavy work')
                p=h.physical(r,entry['input']);need(r['target_final_kv']=={'min':0,'max':len(decoded['states'][-1]['prefix'])-1},'Actual terminal active frontier')
                if worker['proposal_mode']=='replay':need(r['proposal_tape_sha256']==entry['input']['proposal_tape_sha256'],'Different owned replay tape')
                calls.append(dict(root=key,kind='primer'if i<2 else 'measurement',service_s=r['service_seconds'],request_s=r['request_seconds'],
                    target_phases=r['target_phases'],draft_phases=r['draft_phases'],physical=p,cycles=len(r['cycles']),
                    accepted_proposals=sum(c['accepted']for c in r['cycles']),proposed=sum(len(c['proposals'])for c in r['cycles']),
                    rejected_cycles=sum(c['rejected']for c in r['cycles']),output_tokens=len(r['ids']),stop_reason=r['stop_reason'],
                    receipt_sha256=sha(path),reference_receipt_sha256=expected['sha256'],endpoint_equal=True,trace_valid=True))
            samples=[json.loads(x)for x in(dest/'resources.jsonl').read_text().splitlines()];need(samples,'Actual memory telemetry required')
            host=read(dest/'HOST.json');clocks=read(dest/'CLOCKS.json')
            record=dict(**worker,status='COMPLETE',calls=calls,actual_host=host,actual_result_clocks=clocks,model_load_s=meta['model_load_s'],pool_setup_s=meta['pool_setup_s'],
                adapter_run_inclusive_s=wrapper,peak_sampled_total_minus_free_bytes=max((float(x['gpu']['memory.total'])-float(x['gpu']['memory.free']))*1024**2 for x in samples),
                minimum_sampled_free_bytes=min(float(x['gpu']['memory.free'])*1024**2 for x in samples),
                native_result_sha256=sha(dest/'native/result.json'),loaded_modules_sha256=sha(dest/'LOADED_MODULES.json'))
            save(dest/'CHECKED.json',record);records.append(record);slots[name]='COMPLETE';print('M2_DESCRIPTIVE_WORKER_COMPLETE',len(records),24,name,flush=True)
        save(out/'CHECKED.json',records);results=analyze(records);need(results['live']['measurements']==64 and results['replay']['measurements']==32,'Complete descriptive panel counts')
        save(out/'RESULTS.json',results)
    finally:save(out/'ALL_SLOT_STATUS.json',dict(slots=slots,complete_workers=len(records),expected_workers=24,no_selective_retries=True,
        inference='Descriptive only, no confidence intervals or576-test confirmation. Incomplete slots forbid complete-panel conclusions.'))

def analyze(records):
    result={}
    for mode in ('live','replay'):
        workers=[w for w in records if w['proposal_mode']==mode];arms={};measurements=primers=0
        for arm in h.ARMS:
            ws=[w for w in workers if w['arm']==arm];calls=[c for w in ws for c in w['calls']if c['kind']=='measurement'];ps=[c for w in ws for c in w['calls']if c['kind']=='primer'];measurements+=len(calls);primers+=len(ps)
            hist=CounterLike(calls)
            arms[arm]=dict(service_total_s=sum(c['service_s']for c in calls),target_phase_totals_s={p:sum(c['target_phases'].get(p,0)for c in calls)for p in ('PREFILL','VERIFY')},
                draft_phase_total_s=sum(sum(c['draft_phases'].values())for c in calls),cycles=sum(c['cycles']for c in calls),accepted=sum(c['accepted_proposals']for c in calls),
                proposed=sum(c['proposed']for c in calls),output_tokens=sum(c['output_tokens']for c in calls),verify_physical_width_histogram=hist,
                native_process_wall_total_s=sum(w['actual_host']['worker_wall_s']for w in ws),adapter_run_inclusive_total_s=sum(w['adapter_run_inclusive_s']for w in ws),
                minimum_sampled_free_bytes=min(w['minimum_sampled_free_bytes']for w in ws),maximum_sampled_total_minus_free_bytes=max(w['peak_sampled_total_minus_free_bytes']for w in ws))
        contrasts={}
        for k in (3,7):
            for proj in ('L4','P'):contrasts[f'LOCAL_over_W_{proj}_K{k}']=arms[f'L_{proj}_K{k}']['service_total_s']/arms[f'W_{proj}_K{k}']['service_total_s']
            for cut in ('W','L'):contrasts[f'packed_over_loop4_{cut}_K{k}']=arms[f'{cut}_P_K{k}']['service_total_s']/arms[f'{cut}_L4_K{k}']['service_total_s']
        result[mode]=dict(measurements=measurements,primers=primers,arms=arms,descriptive_ratios=contrasts)
    result.update(inference='DESCRIPTIVE_ONLY; exposed roots, two live rounds/one replay round; no population confirmation or bootstrap interval',
        replay_cost_scope='Matched resident allocation, zero draft calls during service; tape generation excluded and reported separately. Replay is not end-to-end drafting.',
        timing_scope='Complete clean service per request, including reset, prefill, bookkeeping/output copies; phase times separately reported. Native process walls include hash/load/two primers/all requests, warm OS file cache; not TTFT.',
        memory_scope='Selected-GPU total-minus-free includes driver/reserved/unavailable memory;2s sampled lower bound, not per-process or exact high-water mark',
        q4_negative_control='Wide packing inactive in VERIFY at k3; prefill packing may still be active. Unexplained q4 timing differences cannot be assigned to wide verification packing.',
        k3_reserve4_baseline='Immutable and separate; all new comparisons common reserve8',confirmation576='NOT_RUN')
    return result

def CounterLike(calls):
    out=defaultdict(int)
    for c in calls:
        for key,v in c['physical']['verify_width_histogram'].items():out[key]+=v
    return dict(out)
