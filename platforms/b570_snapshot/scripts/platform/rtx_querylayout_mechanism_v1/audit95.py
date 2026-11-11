"""Independent standard-library audit. No producer or archived module imports; no GPU."""
import argparse,collections,hashlib,itertools,json,math,statistics,struct
from pathlib import Path

ARMS=['R','M_QB','C_QB','M_PQ','C_PQ','M_GS','C_GS']
PAIRS=[('M_PQ','M_QB'),('C_PQ','C_QB'),('M_GS','M_QB'),('C_GS','C_QB'),('M_QB','C_QB'),('R','M_QB'),('R','C_QB')]
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def digest(o):return hashlib.sha256(json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def gm(v):return math.exp(statistics.mean(math.log(x) for x in v))
def signature(r,eog):
    o=r['output'];ids=o['ids'];flags=o['eog_flags']
    assert ids and len(ids)<=128 and all(type(x)is int and x>=0 for x in ids)
    assert flags==[x in eog for x in ids] and all(type(x)is bool for x in flags) and not any(flags[:-1])
    assert o['length']==len(ids) and o['terminal_id']==ids[-1]
    assert o['stop_reason']==('EOG' if flags[-1] else 'CAP') and (flags[-1] or len(ids)==128)
    assert o['cached_tokens']==0 and o['truncated'] is False
    return tuple(ids),tuple(flags),o['stop_reason']
def count_check(r):
    w=r['workload'];L=r['output']['length'];weighted=lambda h:sum(int(k)*v for k,v in h.items())
    assert not r['workload_error'] and w['unsupported_replay'] is False and w['output_ids_count']==L
    assert w['proposal_generated']==sum(w[k] for k in ['accepted_committed','first_mismatch_rejected','unexamined_after_mismatch','terminal_discarded','unverified_before_verify'])
    assert 0<=w['accepted_committed']<=w['proposal_verified']<=w['proposal_generated']
    assert w['unverified_before_verify']==w['proposal_generated']-w['proposal_verified']
    assert L==sum(w[k] for k in ['initial_target_committed','accepted_committed','bonus_committed','correction_committed','fallback_committed'])
    for h in ['accepted_prefix_hist','cycle_progress_hist','verification_caller_width_hist']:assert sum(w[h].values())==w['verify_cycles']
    assert weighted(w['accepted_prefix_hist'])==w['accepted_committed']
    assert weighted(w['cycle_progress_hist'])==w['accepted_committed']+w['bonus_committed']+w['correction_committed']
    assert weighted(w['verification_caller_width_hist'])==w['proposal_verified']+w['verification_seed_rows']
    assert w['draft_continuation_calls']==w['draft_continuation_rows']==w['draft_proposal_rows']+w['draft_catchup_rows']
    assert weighted(w['target_caller_width_hist'])==w['target_continuation_rows']
    assert sum(w['target_caller_width_hist'].values())==w['target_continuation_calls']
    hh=[w['target_physical_width_hist'],w['draft_physical_width_hist']]
    assert sum(sum(h.values()) for h in hh)==w['physical_micrograph_calls'] and sum(weighted(h) for h in hh)==w['physical_micrograph_rows']
    assert sum(w['target_continuation_physical_width_hist'].values())+w['target_prefill_physical_calls']==sum(w['target_physical_width_hist'].values())

def paid_check(r,eog):
    assert r['status']=='COMPLETED' and r['warmup'] is False and r['phase']=='formal'
    assert r['measurement_mode']=='counts' and r['observation']==dict(phase_timers=False,heavy_capture=False,etw=False,added_sync=False)
    assert math.isfinite(r['wall_ms']) and r['wall_ms']>0
    assert r['wall_ms']==(r['request_end_ns']-r['request_start_ns'])/1e6
    sig=signature(r,eog);response=r['response'];obs=response['hs_closeout']
    assert response['tokens']==r['output']['ids'] and response['tokens_predicted']==len(response['tokens'])
    assert response['stop_type']==('eos' if r['output']['stop_reason']=='EOG' else 'limit')
    assert obs['mode']=='counts' and all(obs[k] is False for k in r['observation'])
    assert r['workload']==obs['workload'] and r['feature_units']==obs['feature_units']
    assert obs['scope_mask']==r['actual_condition']['mask'] and obs['target_ub']==r['actual_condition']['prefill_ub']
    assert obs['context']==1024 and obs['effective_batch']==1024 and response['timings']['cache_n']==0
    count_check(r)
    if r['actual_condition']['layout']=='GS':assert all(int(k)==1 for k in r['workload']['target_physical_width_hist'])
    return sig

def paired(rows,p0,eogs):
    table={};sigs={};result={}
    for r in rows:
        key=(r['family'],r['task'],r['condition'],r['session'],r['round']);assert key not in table,'duplicate coordinate'
        table[key]=r;sigs[key]=paid_check(r,eogs[r['family']])
    for f in p0['families']:
        tasks=[t['id'] for t in p0['P2_panel'][f]];assert len(set(tasks))==12
        assert collections.Counter(t.split('/')[0] for t in tasks)=={'MBPP':6,'GSM8K':6}
        qualification={}
        for a in ARMS:
            expected=[(f,t,a,s,j) for t,s,j in itertools.product(tasks,range(2),range(4))]
            missing=[dict(task=k[1],session=k[3],round=k[4]) for k in expected if k not in table]
            mismatch=[];unstable=[]
            for t in tasks:
                refs=[sigs[f,t,'R',s,j] for s,j in itertools.product(range(2),range(4)) if (f,t,'R',s,j) in sigs]
                if len(refs)!=8 or len(set(refs))!=1:unstable.append(t)
                for s,j in itertools.product(range(2),range(4)):
                    k=(f,t,a,s,j);rk=(f,t,'R',s,j)
                    if k in sigs and rk in sigs and sigs[k]!=sigs[rk]:
                        left,right=sigs[k][0],sigs[rk][0]
                        first=next((dict(index=i,arm=x,reference=y) for i,(x,y) in enumerate(itertools.zip_longest(left,right)) if x!=y),None)
                        mismatch.append(dict(task=t,session=s,round=j,first_difference=first,ends_equal=sigs[k][1:]==sigs[rk][1:]))
            qualification[a]=dict(qualified=not(missing or mismatch or unstable),expected=96,completed=96-len(missing),missing=missing,mismatches=mismatch,unstable_or_missing_reference=unstable)
        comparisons=[]
        for a,b in PAIRS:
            q=qualification[a]['qualified'] and qualification[b]['qualified'];effects=[]
            if q:
                for t in tasks:
                    ss=[statistics.median(table[f,t,a,s,j]['wall_ms'] for j in range(4))/statistics.median(table[f,t,b,s,j]['wall_ms'] for j in range(4)) for s in range(2)]
                    effects.append(dict(task=t,ratio=gm(ss),session_ratios=ss,left_session_median_ms=[statistics.median(table[f,t,a,s,j]['wall_ms'] for j in range(4)) for s in range(2)],right_session_median_ms=[statistics.median(table[f,t,b,s,j]['wall_ms'] for j in range(4)) for s in range(2)]))
            comparisons.append(dict(pair=a+'/'+b,qualified=q,cost_ratio=gm([e['ratio'] for e in effects]) if q else None,session_ratios=[gm([e['session_ratios'][s] for e in effects]) for s in range(2)] if q else None,domains={d:gm([e['ratio'] for e in effects if e['task'].startswith(d+'/')]) for d in ['MBPP','GSM8K']} if q else None,regressions=[e['task'] for e in effects if e['ratio']<1],task_effects=effects,claim='same-reference inclusive request-cost' if q else 'NULL: missing/nonqualified/stable-reference failure'))
        result[f]=dict(qualification=qualification,comparisons=comparisons)
    expected=set((f,t['id'],a,s,j) for f in p0['families'] for t in p0['P2_panel'][f] for a,s,j in itertools.product(ARMS,range(2),range(4)))
    assert set(table)<=expected,'unregistered task or coordinate'
    return result

def relocate(path,local):
    p=Path(path.replace('\\','/'));parts=list(p.parts);idx=next(i for i,x in enumerate(parts) if x.lower()=='hsc95');return local.joinpath(*parts[idx+1:])
def float_metrics(a,b):
    assert len(a)==len(b) and len(a)%4==0
    x=struct.unpack('<'+'f'*(len(a)//4),a);y=struct.unpack('<'+'f'*(len(b)//4),b)
    u=struct.unpack('<'+'I'*(len(a)//4),a);v=struct.unpack('<'+'I'*(len(b)//4),b)
    indices=[i for i in range(len(x)) if math.isfinite(x[i]) and math.isfinite(y[i])]
    order=lambda k:0x80000000-(k&0x7fffffff) if k&0x80000000 else 0x80000000+k
    return dict(bitwise_equal=a==b,equal_elements=sum(i==j for i,j in zip(u,v)),elements=len(x),max_abs=max((abs(x[i]-y[i]) for i in indices),default=None),max_rel=max((abs(x[i]-y[i])/max(abs(x[i]),abs(y[i]),1e-30) for i in indices),default=None),max_ULP=max((abs(order(u[i])-order(v[i])) for i in indices),default=None),nonfinite_pairs=len(x)-len(indices))
def canonical(root,meta):
    assert meta['type']==0;raw=(root/meta['file']).read_bytes();out=bytearray()
    for a3,a2,a1,a0 in itertools.product(range(meta['ne'][3]),range(meta['ne'][2]),range(meta['ne'][1]),range(meta['ne'][0])):
        offset=sum(i*n for i,n in zip([a0,a1,a2,a3],meta['nb']));out+=raw[offset:offset+4]
    assert len(out)==4*math.prod(meta['ne']);return bytes(out)

def operator_audit(pub,local):
    if not (pub/'OPERATOR_REPLAY.json').exists():return dict(status='UNRESOLVED',reason='P1 did not finish; raw attempts retained')
    replay=read(pub/'OPERATOR_REPLAY.json');contexts=replay['contexts'];assert len(contexts)<=24;comparisons=[];own=[];repeat=[]
    for i,c in enumerate(contexts):
        root=relocate(c['root'],local)
        for n,h in c['registry'].items():assert sha(root/n)==h,'captured input modified'
        m=read(root/'snapshot.json');by={}
        for r in c['replays']:
            out=relocate(r['path'],local)
            for n,h in r['files'].items():assert sha(out/n)==h,'replay modified'
            rr=read(out/'REPLAY.json');assert rr['backend']=='CUDA0' and rr['arm']==r['arm'] and rr['added_sync'] is True
            for name,v in rr['fixed_inputs'].items():
                assert v['readback_bitwise_equal'] is True and v['ne']==m[name]['ne'] and v['nb']==m[name]['nb'] and v['type']==m[name]['type'] and v['bytes']==m[name]['bytes']
            by[r['arm'],r['repeat']]=out
        for left,right in [('MQ','PQ'),('MQ','QB'),('PQ','QB')]:
            if (left,0) not in by or (right,0) not in by:continue
            stages={s:float_metrics((by[left,0]/(s+'.bin')).read_bytes(),(by[right,0]/(s+'.bin')).read_bytes()) for s in ['QK','softmax','AV']}
            archived=next(x for x in replay['comparisons'] if x['context']==i and x['pair']==left+'/'+right)
            for s,metrics in stages.items():
                for k,v in metrics.items():assert archived['stages'][s][k]==v,'producer numerical summary differs'
            comparisons.append(dict(context=i,family=c['family'],task=c['task'],phase=c['phase'],pair=left+'/'+right,first_divergent_operator=next((s for s in ['QK','softmax','AV'] if not stages[s]['bitwise_equal']),None),stages=stages))
        for arm in ['MQ','PQ','QB']:
            complete=all((arm,j) in by for j in range(3))
            repeat.append(dict(context=i,arm=arm,complete=complete,all_stages_bitwise_identical=complete and all((by[arm,0]/(s+'.bin')).read_bytes()==(by[arm,j]/(s+'.bin')).read_bytes() for s,j in itertools.product(['QK','softmax','AV'],range(3)))))
        if ('MQ',0) in by:
            stages={s:float_metrics(canonical(root,m['native_'+s]),(by['MQ',0]/(s+'.bin')).read_bytes()) for s in ['QK','softmax','AV']}
            own.append(dict(context=i,all_stages_bitwise_equal=all(v['bitwise_equal'] for v in stages.values()),stages=stages))
    equality=[c for c in comparisons if c['pair']=='PQ/QB'];supported=bool(equality) and all(c['first_divergent_operator'] is None for c in equality)
    return dict(status='SUPPORTED' if supported else ('REFUTED' if equality else 'UNRESOLVED'),statement='QB and PQ bitwise attention arithmetic match at these captured contexts only',contexts=len(contexts),expected_contexts=24,comparisons=comparisons,within_arm_repeats=repeat,own_path=own,own_path_correspondence=bool(own) and all(o['all_stages_bitwise_equal'] for o in own),native_model_decision_claim='UNRESOLVED',kernel_scheduling='UNKNOWN',cases=replay['cases'],controls=replay['controls'])

def audit(repo,local):
    pub=repo/'benchmarks/rtx_querylayout_mechanism_v1';p0=read(pub/'P0_PLAN.json');errors=[];frozen=[]
    for phase in ['F0A','F0B']:
        path=pub/(phase+'.json')
        if not path.exists():continue
        freeze=read(path);receipt=read(local/(phase+'_REMOTE_RECEIPT.json'));assert receipt['actual_authenticated_remote_bytes'] is True
        for name,h in freeze['payload_sha256'].items():assert sha(repo/name)==h,'changed freeze:'+name
        assert sha(path)==receipt['readback'][path.relative_to(repo).as_posix()]['sha256'];frozen.append(phase)
    assert 'F0A' in frozen
    ledger=[read(p) for p in sorted((local/'ledger').glob('*.json'))];assert [e['index'] for e in ledger]==list(range(len(ledger)))
    assert len({e['slot'] for e in ledger})==len(ledger),'duplicate paid start'
    events={e['slot']:e for e in ledger};rows=[];attempts=[];allcompleted=0
    formal_plan=read(pub/'FORMAL_PLAN.json') if (pub/'FORMAL_PLAN.json').exists() else None
    declared={s['slot']:(s,b) for b in formal_plan['blocks'] for s in b['slots']} if formal_plan else {}
    for e in ledger:
        if e['phase']=='formal' and e['kind']=='request':assert e['slot'] in declared and declared[e['slot']][1]['admitted'],'unadmitted forward'
    if formal_plan:
        for b in formal_plan['blocks']:
            expected=[s['slot'] for s in b['slots']];started=[e['slot'] for e in ledger if e['slot'] in expected]
            assert started==expected[:len(started)],'changed frozen sequence or hidden retry'
    for p in sorted((local/'runs').rglob('REQUEST_STARTED.json')):
        start=read(p);slot=start['slot'];assert slot in events
        family=start['family'];assert start['utc']>read(local/('F0B_REMOTE_RECEIPT.json' if events[slot]['phase']=='formal' else 'F0A_REMOTE_RECEIPT.json'))['utc']
        body=start['body'];assert body['n_predict']==128 and body['seed']==123 and body['temperature']==0 and body['cache_prompt'] is False and body['return_tokens'] is True
        record=p.with_name('RECORD.json');complete=p.with_name('COMPLETED.json')
        if record.exists() and complete.exists():
            assert read(complete)['record_sha256']==sha(record);r=read(record);allcompleted+=1
            assert r['slot']==slot and r['input_sha256']==start['input_sha256'] and r['actual_condition']==start['condition']
            worker=p.parent.parent.parent;identity=read(worker/'LOAD_IDENTITY.json');module=read(worker/'MODULE_IDENTITY.json')
            assert identity['layers'] and all(x==y for x,y in identity['layers']) and module['verified'] is True
            pinned=read(pub/'NATIVE_BUILD.json')['numerical_DLL_sha256'];pins={n.lower():h for n,h in pinned.items()}
            assert all(v['sha256']==pins[Path(v['path'].replace('\\','/')).name.lower()] for v in module['modules'])
            assert int(identity['ubs'][0])==start['condition']['prefill_ub'] and int(identity['output_capacity_per_seq'][0])>=start['condition']['required_output_rows']
            if events[slot]['phase']=='formal' and events[slot]['kind']=='request':
                try:
                    s,b=declared[slot];assert r['actual_condition']==b['condition'] and r['session']==b['session'] and r['round']==s['round'] and r['position']==s['position']
                    task=next(t for t in p0['P2_panel'][family] if t['id']==r['task'])
                    assert start['input_sha256']==digest(task) and body['prompt']==task['prompt_ids']
                    build=read(pub/'NATIVE_BUILD.json');model=read(pub/'MODEL_CONTRACT.json')['families'][family]['models']
                    runtime=digest(dict(native_source=build['source_inventory_sha256'],server=build['server_sha256'],DLLs=build['numerical_DLL_sha256'],models=model,contract_sha256=sha(pub/'MODEL_CONTRACT.json')))
                    assert r['source_identity_sha256']==runtime and r['runtime_identity_verified'] is True and read(worker/'COMMAND.json')['runtime_identity_sha256']==runtime
                    assert all(int(x)==1024 for x in identity['contexts']) and (not b['condition']['spec'] or int(identity['ubs'][-1])==1)
                    assert r['response']['timings']['prompt_n']==len(task['prompt_ids']) and r['workload']['prompt_ids_count']==len(task['prompt_ids'])
                    paid_check(r,set(read(pub/'MODEL_CONTRACT.json')['families'][family]['eog']));rows.append(r)
                except (AssertionError,KeyError,StopIteration) as e:errors.append(dict(slot=slot,error=repr(e),invalid_paid_record=True))
        else:attempts.append(dict(slot=slot,failed=read(p.with_name('FAILED.json')) if p.with_name('FAILED.json').exists() else None,completed_marker_missing=True))
    eogs={f:set(v['eog']) for f,v in read(pub/'MODEL_CONTRACT.json')['families'].items()};families=paired(rows,p0,eogs)
    owned=sum(read(p)['seconds'] for p in (local/'runs').rglob('LIFETIME.json'))
    counts=dict(formal_started=sum(e['phase']=='formal' and e['kind']=='request' for e in ledger),formal_completed=len(rows),formal_registered=2016,formal_missing=2016-len(rows),warm_started=sum(e['phase']=='formal' and e['kind']=='warmup' for e in ledger),diagnostic_engineering_started=sum(e['phase']!='formal' and e['kind'] in ['request','warmup'] for e in ledger),load_starts=sum(e['kind']=='load' for e in ledger),operator_starts=sum(e['kind']=='operator' for e in ledger),all_native_completed=allcompleted,owned_GPU_seconds=owned)
    assert counts['formal_started']<=2016 and counts['warm_started']<=84 and counts['diagnostic_engineering_started']<=512 and counts['operator_starts']<=216 and owned<=43200
    mechanism=operator_audit(pub,local)
    claims=[dict(statement=mechanism['statement'] if 'statement' in mechanism else 'Fixed-input arithmetic',status=mechanism['status'],evidence='OPERATOR_REPLAY.json; raw snapshots and independent numerical recomputation',allowed_wording='Only sampled actual identical-input operator contexts; no CUDA reduction-order or full-model bitwise proof'),dict(statement='Kernel-level schedule equivalence',status='UNRESOLVED',evidence='KERNEL_DISPATCH.json',allowed_wording='Runtime dispatch recorded; kernel scheduling UNKNOWN'),dict(statement='Component-time predictor',status='UNRESOLVED',evidence='Parent #94 audit',allowed_wording='MODEL_TIMING_UNAVAILABLE; no wall-time fitting')]
    for f,res in families.items():
        for p in res['comparisons']:
            claims.append(dict(statement=f+' '+p['pair']+' request-cost ratio >1',status='UNRESOLVED' if p['cost_ratio'] is None else ('SUPPORTED' if p['cost_ratio']>1 else 'REFUTED'),cost_ratio=p['cost_ratio'],evidence='RESULTS.json; complete raw formal slots',allowed_wording='Qualified identical-reference request costs for registered exposed panel and adjacent sessions only; incremental speculation and repair cost separately labelled'))
    return dict(status='PASS_INDEPENDENT_AUDIT' if not errors else 'INVALID_PAID_ENDPOINTS_RETAINED',counts=counts,frozen=frozen,invalid_records=errors,failed_attempts=attempts,families=families,mechanism=mechanism,scientific_closeout=claims,MODEL_TIMING_UNAVAILABLE=True,paid_scope='Complete nonstreaming resident HTTP encode/submit/native full IDs+stop parsing+endpoint checks; no added synchronization',energy_throughput_component_claim=False)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--local',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    result=audit(args.repo,args.local);args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(result['status'],json.dumps(result['counts']),flush=True)
if __name__=='__main__':main()
