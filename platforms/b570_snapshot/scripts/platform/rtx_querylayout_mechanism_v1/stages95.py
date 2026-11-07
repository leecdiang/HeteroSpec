from common95 import *
from runner95 import *
import struct,csv,math,shutil,heapq

def canonical_native(root,meta):
    assert meta['type']==0,'NOT_COMPARABLE non-F32 intermediate'
    b=(root/meta['file']).read_bytes();ne=meta['ne'];nb=meta['nb'];out=bytearray()
    for a3 in range(ne[3]):
        for a2 in range(ne[2]):
            for a1 in range(ne[1]):
                for a0 in range(ne[0]):
                    offset=sum(a*n for a,n in zip([a0,a1,a2,a3],nb));out+=b[offset:offset+4]
    assert len(out)==4*math.prod(ne);return bytes(out)
def distance(a,b):
    assert len(a)==len(b) and len(a)%4==0
    aa=struct.unpack('<'+'f'*(len(a)//4),a);bb=struct.unpack('<'+'f'*(len(b)//4),b)
    ia=struct.unpack('<'+'I'*(len(a)//4),a);ib=struct.unpack('<'+'I'*(len(b)//4),b)
    finite=[i for i,(x,y) in enumerate(zip(aa,bb)) if math.isfinite(x) and math.isfinite(y)]
    def ordered(x):return 0x80000000-(x&0x7fffffff) if x&0x80000000 else 0x80000000+x
    def top(x):
        if not x or any(not math.isfinite(v) for v in x):return None
        pairs=heapq.nsmallest(2,enumerate(x),key=lambda p:(-p[1],p[0]));return dict(argmax=pairs[0][0],top2_margin=pairs[0][1]-pairs[1][1])
    return dict(bitwise_equal=a==b,equal_elements=sum(x==y for x,y in zip(ia,ib)),elements=len(aa),max_abs=max((abs(aa[i]-bb[i]) for i in finite),default=None),max_rel=max((abs(aa[i]-bb[i])/max(abs(aa[i]),abs(bb[i]),1e-30) for i in finite),default=None),max_ULP=max((abs(ordered(ia[i])-ordered(ib[i])) for i in finite),default=None),nonfinite_pairs=len(aa)-len(finite),left_operator_flat_top=top(aa),right_operator_flat_top=top(bb),argmax_scope='flattened operator values; not native model decision logits')
def admit_snapshot(root,registry):
    assert set(registry)=={p.name for p in root.iterdir() if p.is_file()}
    for name,h in registry.items():assert sha(root/name)==h,'INPUT_NOT_IDENTICAL:'+name
    return read(root/'snapshot.json')
def run_p1(ledger):
    plan=read(PUB/'P0_PLAN.json');cases=[];contexts=[];dispatch=[];controls=[]
    for family,selection in plan['P1_selection'].items():
        for index,task in enumerate(selection['tasks']):
            name=f'case{index}';status('P1_NATIVE_CAPTURE',family=family,task=task['id']);cooling('diag-'+family+'-'+name)
            c=condition('C_MQ',capture=True)
            try:
                with Worker95(ledger,family,c,'diag',name) as w:
                    w.complete(plan['warmups'][family],f'diag/{family}/{name}/WARM',warmup=True,meta=dict(study_phase='P1'))
                    heavy=w.complete(task,f'diag/{family}/{name}/CAPTURE',mode='heavy',meta=dict(study_phase='P1',exposed=True))
                    ordinary=w.complete(task,f'diag/{family}/{name}/CAPTURE_OFF',meta=dict(study_phase='P1',exposed=True))
                cases.append(dict(family=family,task=task['id'],status='COMPLETED',capture_on_off_full_equal=signature(heavy)==signature(ordinary),heavy_slot=heavy['slot'],counts_slot=ordinary['slot'],heavy_wall_ms=heavy['wall_ms'],counts_wall_ms=ordinary['wall_ms'],observer_difference_ms=heavy['wall_ms']-ordinary['wall_ms'],overhead_not_subtracted=True))
                snapshots=LOCAL/'runs/diag'/family/name/'snapshots'
                trace=[json.loads(b) for b in (snapshots.parent/'trace.jsonl').read_bytes().splitlines()]
                for root in sorted(snapshots.glob('*')):
                    if not (root/'snapshot.json').exists():continue
                    assert len(contexts)<24
                    m=read(root/'snapshot.json');decode=next(x for x in trace if x.get('event')=='decode' and x.get('role')=='target' and (x.get('phase')=='prefill')==(m['phase']=='prefill') and x.get('caller_batch',0)>1)
                    boundary=dict(native_decode=decode,first_physical_query_positions=decode['positions'][:m['q_occupancy']],first_physical_query_token_ids=decode['tokens'][:m['q_occupancy']],committed_generated_prefix=[] if m['phase']=='prefill' else heavy['output']['ids'][:1],pending_token=None if m['phase']=='prefill' else heavy['output']['ids'][0],exposed_task=task['id'],source='First layer0 physical target micrograph in the first eligible native caller; raw positions/ownership trace retained, no synthesized logits')
                    save(root/'LOGICAL_BOUNDARY.json',boundary)
                    registry={p.name:sha(p) for p in root.iterdir() if p.is_file()};assert admit_snapshot(root,registry)==m
                    controls.append(dict(family=family,task=task['id'],phase=m['phase'],bitwise_duplicate_inputs=True,changed_mask_rejection='Verified below before GPU replay',changed_position_rejection='Verified below before GPU replay'))
                    # Test the real admission gate on altered bytes and logical positions; no GPU invocation.
                    for name2 in ['mask.bin','LOGICAL_BOUNDARY.json']:
                        bad=LOCAL/'negative-controls'/f'{family}-{index}-{m["phase"]}-{name2}';shutil.copytree(root,bad)
                        if name2=='mask.bin':
                            b=(bad/name2).read_bytes();(bad/name2).write_bytes(bytes([b[0]^1])+b[1:])
                        else:
                            value=read(bad/name2);value['native_decode']['positions'][0]+=1;(bad/name2).write_text(json.dumps(value),encoding='utf-8')
                        try:admit_snapshot(bad,registry);raise RuntimeError('negative control admitted')
                        except AssertionError:pass
                    context=dict(family=family,task=task['id'],phase=m['phase'],root=str(root),registry=registry,replays=[],failures=[])
                    ctxid=len(contexts);save(LOCAL/'snapshot-registry'/f'{ctxid:03d}.json',context)
                    for repeat in range(3):
                        for arm in ['MQ','PQ','QB'][repeat:]+['MQ','PQ','QB'][:repeat]:
                            admit_snapshot(root,registry);slot=f'operator/{ctxid}/{arm}/r{repeat}';ledger.charge(family,'operator','operator',slot)
                            out=LOCAL/'operator'/f'{ctxid:03d}'/f'{arm}-r{repeat}';start=time.perf_counter()
                            try:
                                p=subprocess.run([str(LOCAL/'native/build/bin/querylayout-replay.exe'),str(root),arm,str(out),str(LOCAL/'native/build/bin')],capture_output=True,timeout=120,creationflags=subprocess.CREATE_NO_WINDOW)
                            except subprocess.TimeoutExpired as e:
                                out.mkdir(parents=True,exist_ok=True);(out/'stdout.log').write_bytes(e.stdout or b'');(out/'stderr.log').write_bytes(e.stderr or b'')
                                save(out/'FAILED.json',dict(slot=slot,error=repr(e),started_not_retried=True))
                                context['failures'].append(dict(slot=slot,error=repr(e)));continue
                            finally:
                                seconds=time.perf_counter()-start;life=LOCAL/'runs/operator'/f'{ctxid:03d}-{arm}-r{repeat}'/'LIFETIME.json';save(life,dict(seconds=seconds,utc=now(),phase='operator'));ledger.life+=seconds
                            out.mkdir(parents=True,exist_ok=True);(out/'stdout.log').write_bytes(p.stdout);(out/'stderr.log').write_bytes(p.stderr)
                            if p.returncode:
                                context['failures'].append(dict(slot=slot,returncode=p.returncode,stderr=p.stderr.decode(errors='replace')));continue
                            r=read(out/'REPLAY.json');assert r['backend']=='CUDA0' and all(v['readback_bitwise_equal'] for v in r['fixed_inputs'].values())
                            context['replays'].append(dict(arm=arm,repeat=repeat,path=str(out),files={p.name:sha(p) for p in out.iterdir() if p.is_file()}));dispatch.append(dict(context=ctxid,arm=arm,repeat=repeat,receipt=r))
                    contexts.append(context)
            except (AssertionError,RuntimeError,OSError,TimeoutError) as e:
                cases.append(dict(family=family,task=task['id'],status='BLOCKED',error=repr(e),started_not_retried=True))
        task=selection['tasks'][0];c=condition('C_QB',reuse_probe=True);c['mask']=1
        cooling('diag-'+family+'-reuse');status('P1_REUSE_ADVERSARIAL',family=family)
        with Worker95(ledger,family,c,'diag','reuse') as w:r=w.complete(task,f'diag/{family}/reuse/PROBE',mode='heavy',meta=dict(study_phase='P1_adversarial',not_tuning=True))
        path=LOCAL/'runs/diag'/family/'reuse/reuse-rejection.jsonl';events=[json.loads(b) for b in path.read_bytes().splitlines()] if path.exists() else []
        controls.append(dict(family=family,failed_topology_reuse_rejected=bool(events) and all(x['cached_active']!=x['new_active'] and x['rejected'] for x in events),events=events,slot=r['slot']))
    comparisons=[]
    for i,c in enumerate(contexts):
        root=Path(c['root']);m=read(root/'snapshot.json');native_bytes={name:canonical_native(root,m['native_'+name]) for name in ['QK','softmax','AV']}
        by={(r['arm'],r['repeat']):Path(r['path']) for r in c['replays']}
        for left,right in [('MQ','PQ'),('MQ','QB'),('PQ','QB')]:
            if (left,0) not in by or (right,0) not in by:continue
            values={stage:distance((by[left,0]/(stage+'.bin')).read_bytes(),(by[right,0]/(stage+'.bin')).read_bytes()) for stage in ['QK','softmax','AV']}
            comparisons.append(dict(context=i,family=c['family'],task=c['task'],phase=c['phase'],pair=left+'/'+right,first_divergent_operator=next((s for s in ['QK','softmax','AV'] if not values[s]['bitwise_equal']),None),stages=values))
        c['within_arm_repeatability']={arm:dict(complete=all((arm,r) in by for r in range(3)),stages={stage:all((arm,r) in by and (by[arm,r]/(stage+'.bin')).read_bytes()==(by[arm,0]/(stage+'.bin')).read_bytes() for r in range(3)) for stage in ['QK','softmax','AV']}) for arm in ['MQ','PQ','QB'] if (arm,0) in by}
        c['own_path_MQ_vs_native']={stage:distance(native_bytes[stage],(by['MQ',0]/(stage+'.bin')).read_bytes()) for stage in native_bytes} if ('MQ',0) in by else None
    save(PUB/'OPERATOR_REPLAY.json',dict(cases=cases,contexts=contexts,comparisons=comparisons,controls=controls,post_mask_scores='NOT_COMPARABLE fused native softmax stage',model_decision_causal_claim='UNRESOLVED; no full-path logits synthesized from operator-only replays',historical_width_probe='NOT_ADMITTED: MBPP229 original failing q6/8,k5/7 geometry exceeds frozen q<=4,k3 contract',new_blind_inputs=False))
    save(PUB/'KERNEL_DISPATCH.json',dict(status='RUNTIME_DISPATCH_ONLY',kernel_scheduling='UNKNOWN',actual_replay_dispatch=dispatch,profiler_admission=read(PUB/'PROFILER_ADMISSION.json')))
    with (PUB/'OPERATOR_NUMERICAL.csv').open('x',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['context','family','task','phase','pair','stage','bitwise_equal','equal_elements','elements','max_abs','max_rel','max_ULP'])
        for c in comparisons:
            for stage,a in c['stages'].items():w.writerow([c[k] for k in ['context','family','task','phase','pair']]+[stage]+[a[k] for k in ['bitwise_equal','equal_elements','elements','max_abs','max_rel','max_ULP']])
    status('P1_COMPLETE',contexts=len(contexts),comparisons=len(comparisons))

def engineering(ledger):
    plan=read(PUB/'P0_PLAN.json');qual={};graphs=[]
    for family in plan['families']:
        by={}
        for c in plan['arms']:
            arm=c['name'];cooling('engineering-'+family+'-'+arm);status('NATIVE_COMPARATOR_QUALIFICATION',family=family,arm=arm)
            try:
                with Worker95(ledger,family,c,'engineering',arm) as w:
                    w.complete(plan['warmups'][family],f'engineering/{family}/{arm}/WARM',warmup=True,meta=dict(study_phase='P0_engineering'))
                    probe=w.complete(plan['P2_panel'][family][0],f'engineering/{family}/{arm}/GRAPH_PROBE',mode='heavy',meta=dict(study_phase='P0_actual_graph_admission',excluded_from_paid=True))
                    by[arm]=[w.complete(t,f'engineering/{family}/{arm}|'+t['id'],meta=dict(study_phase='P0_engineering',exposed=True)) for t in plan['P2_panel'][family]]
                    events=[json.loads(line) for line in (w.d/'trace.jsonl').read_bytes().splitlines()]
                    nodes=[g for x in events if x.get('event')=='decode' for g in x.get('graphs',[]) if g['role']=='target']
                    evidence=arm=='R' or (arm.endswith('_GS') and all(int(k)==1 for k in probe['workload']['target_physical_width_hist'])) or (arm.endswith('_PQ') and any(g['name']=='hs_attn_single_query-0' for g in nodes)) or (arm.endswith('_QB') and any(g['name']=='hs_attn_query_batch-0' for g in nodes))
                    graphs.append(dict(family=family,arm=arm,actual_declared_graph_admitted=bool(evidence),nodes=nodes,probe_slot=probe['slot'],probe_vs_counts_full_equal=signature(probe)==signature(by[arm][0]),target_physical_width_hist=probe['workload']['target_physical_width_hist'],ordinary_has_no_draft=not c['spec'] and probe['workload']['draft_continuation_calls']==0))
                    assert evidence,'actual declared topology not observed'
            except (AssertionError,RuntimeError,OSError,TimeoutError) as e:by[arm]=dict(error=repr(e),started_not_retried=True)
        qual[family]={}
        for arm,rows in by.items():
            valid=isinstance(rows,list) and isinstance(by.get('R'),list) and len(rows)==12 and all(r['contract_valid'] and not r['workload_error'] and signature(r)==signature(ref) for r,ref in zip(rows,by['R']))
            qual[family][arm]=dict(admitted=valid,status='PASS_ENGINEERING_PANEL' if valid else 'NONQUALIFIED_OR_BLOCKED',mismatch_tasks=[r['task'] for r,ref in zip(rows,by['R']) if signature(r)!=signature(ref)] if isinstance(rows,list) and isinstance(by.get('R'),list) else None,failure=rows if isinstance(rows,dict) else None)
    save(PUB/'ENGINEERING_QUALIFICATION.json',dict(families=qual,formal_arm_admission_only=True,scope='12 predeclared exposed tasks; final full-output/stable-reference qualification is independently repeated on all formal slots'))
    save(PUB/'ACTUAL_GRAPH_ADMISSION.json',dict(actual_graphs=graphs,paid_scope_uninstrumented=True,heavy_probes_are_excluded_diagnostics=True))
    blocks=[]
    for session in [0,1]:
        for fi,family in enumerate(plan['families']):
            arms=plan['arms'][fi:]+plan['arms'][:fi]
            if session:arms=list(reversed(arms))
            for ai,c in enumerate(arms):
                slots=[];tasks=plan['P2_panel'][family]
                for round in range(4):
                    offset=(3*round+ai+6*session)%12;order=tasks[offset:]+tasks[:offset]
                    for position,t in enumerate(order):slots.append(dict(slot=f'{family}/s{session}/r{round}/{c["name"]}|{t["id"]}',task=t['id'],round=round,position=position,input_sha256=digest(t)))
                blocks.append(dict(family=family,session=session,condition=c,admitted=qual[family][c['name']]['admitted'] and qual[family]['R']['admitted'],slots=slots))
    save(PUB/'FORMAL_PLAN.json',dict(design_head=DESIGN_HEAD,P0_plan_sha256=sha(PUB/'P0_PLAN.json'),families=plan['families'],blocks=blocks,total_registered_slots=2016,admitted_slots=sum(len(b['slots']) for b in blocks if b['admitted']),resource_estimate_seconds=plan['prospective_owned_reserve_seconds'],arm_exclusions_only_for_native_output_or_isolated_implementation_failure=True,family_cost_pruning=False,request_timer='Inherited complete JSON encode/submission/native full IDs+stop parse+endpoint validation; no added sync or phase timers',parent_exposed_inputs=True))
def formal(ledger):
    plan=read(PUB/'FORMAL_PLAN.json');p0=read(PUB/'P0_PLAN.json');failures=[];blocked=set()
    for i,b in enumerate(plan['blocks']):
        if not b['admitted']:continue
        family=b['family'];arm=b['condition']['name'];name=f's{b["session"]}-{arm}';slots=b['slots']
        if (family,arm) in blocked:continue
        assert not any(ledger.started(s['slot']) for s in slots),'Formal blocks are immutable; no retries'
        status('P2_FORMAL',block=i+1,blocks=len(plan['blocks']),family=family,arm=arm,completed=sum(e['phase']=='formal' and e['kind']=='request' for e in ledger.events));cooling('formal-'+family+'-'+name)
        by={t['id']:t for t in p0['P2_panel'][family]}
        try:
            with Worker95(ledger,family,b['condition'],'formal',name) as w:
                w.complete(p0['warmups'][family],f'formal/{family}/{name}/WARM',warmup=True,meta=dict(study_phase='P2'))
                for s in slots:w.complete(by[s['task']],s['slot'],meta=dict(study_phase='P2',session=b['session'],round=s['round'],position=s['position'],exposed=True))
        except (AssertionError,RuntimeError,OSError,TimeoutError) as e:
            failures.append(dict(family=family,arm=arm,block=i,error=repr(e),started_not_retried=True));blocked.add((family,arm))
            if ledger.owned_now()>=43200-252:break
            # Source/asset hashes are global authority: do not continue after a failed identity.
            if isinstance(e,AssertionError) and not str(e):break
    save(PUB/'FORMAL_FAILURES.json',dict(failures=failures,blocked_arms=[list(x) for x in sorted(blocked)],started_not_retried=True))
