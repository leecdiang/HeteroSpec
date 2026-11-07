"""Hardware-free independent evidence recomputation; no runner imports."""
import argparse, gzip, hashlib, json, re, subprocess
from datetime import datetime
from pathlib import Path

R0=['HumanEval/'+str(i) for i in (134,42,145,138,19,20)]
SALT='B570_LIVE_PARTITION_INTERVENTION_V1|2026-09-30|'
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def digest(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def endpoint(ids,flags):
    assert ids and len(ids)==len(flags) and all(type(i)==int and i>=0 for i in ids)
    assert all(type(f)==bool for f in flags)
    cut=next((i+1 for i,f in enumerate(flags) if f),len(ids));end=min(cut,128)
    assert end==128 or flags[end-1]
    return ids[:end]
def divergence(a,b):return next((i for i in range(max(len(a),len(b))) if i>=len(a) or i>=len(b) or a[i]!=b[i]),None)

def verify(root):
    root=Path(root);p=root/'benchmarks/b570_partition_intervention_v1';raw=root/'artifacts/b570_partition_intervention_v1/raw'
    errors=[];checks=0
    def require(ok,message):
        nonlocal checks
        checks+=1
        if not ok:errors.append(message)
    identity=load(p/'BUILD_IDENTITY.json');audit=load(p/'EXPOSURE_AUDIT.json');reserved=load(p/'RESERVED_SET.json')
    require(not audit['errors'],'exposure audit has errors')
    v1=load(root/'benchmarks/b570_direct_id_v1/protocol_v1.json')
    old=load(root/'benchmarks/b570_mechanism_v08/RESERVED_VALIDATION_SET.json')['selected_task_ids']
    exposed=set(v1['task_ids'])|set(old)
    for row in audit['evidence']:exposed.update(row['task_ids'])
    require(exposed==set(audit['exposed_task_ids']),'exposure union')
    eligible={f'HumanEval/{n}' for n in range(164)}-exposed
    require(eligible==set(audit['eligible_task_ids'])==set(reserved['eligible_task_ids']),'eligible pool')
    selected=sorted(eligible,key=lambda t:hashlib.sha256((SALT+t).encode()).hexdigest())[:24]
    require(selected==reserved['task_ids'] and len(selected)==24,'salt selection')
    require(not set(selected)&(set(v1['task_ids'])|set(old)|set(R0)),'reserved disjointness')
    for t,row in reserved['prompts'].items():
        require(hashlib.sha256(row['input'].encode()).hexdigest()==row['sha256'],'reserved input bytes '+t)
        require(hashlib.sha256((SALT+t).encode()).hexdigest()==row['selection_key'],'reserved rank '+t)
    for n,h in identity['new_frontend_files'].items():require(digest(root/'scripts/platform/b570_partition_intervention_v1'/n)==h,'frozen source '+n)
    require(identity['upstream_commit']=='0cae43063cf15170e91a2ff4d034da0ecef4a1b2' and identity['build_number']==10839,'pinned upstream')
    require(identity['binaries']['ggml-vulkan.dll']==v1['binary_hashes']['ggml-vulkan.dll'],'Vulkan DLL identity')
    rows={};captures={};recomputed_events=[]
    for directory in sorted(raw.glob('*/*')):
        if not directory.is_dir():continue
        label=directory.relative_to(raw).as_posix()
        require((directory/'start.json').exists() and (directory/'record.json').exists(),'all attempts finalized '+label)
        if not (directory/'record.json').exists():continue
        row=load(directory/'record.json');rows[(row['stage'],row['task_id'],row['repetition'],row['mode'])]=row
        require(row['start_utc']<=row['end_utc'],'attempt chronology '+label)
        require(digest(p/'BUILD_IDENTITY.json')==row['identity_sha256'],'attempt frozen identity '+label)
        for name,h in row['files'].items():
            require((directory/name).is_file() and digest(directory/name)==h['sha256'],'raw file hash '+label+'/'+name)
        require(digest(directory/'prompt.txt')==row['prompt_sha256'],'actual prompt '+label)
        text=(directory/'stderr.txt').read_text(encoding='utf-8',errors='replace')
        if row['execution_valid']:
            require(row['exit_code']==0,'valid exit '+label)
            require(re.findall(r'offloaded\s+(\d+)/(\d+) layers to GPU',text)==[('37','37'),('29','29')],'full offload '+label)
            place=[s for s in text.splitlines() if 'using device ' in s]
            require(len(place)==2 and all('using device Vulkan0 (Intel(R) Arc(TM) B570 Graphics)' in s for s in place),'placement '+label)
            ids=load(directory/'ids.json');actual=endpoint(ids['ids'],ids['eog'])
            require(actual==row['generated_ids'],'direct endpoint '+label)
        state={}
        for name,obj in row['state_objects'].items():
            with gzip.open(directory/obj['compressed'],'rb') as f:b=f.read()
            require(hashlib.sha256(b).hexdigest()==obj['sha256'] and len(b)==obj['bytes'],'decompressed KV bytes '+label+'/'+name)
            state[name]=b
        if not (directory/'capture.json').exists():continue
        c=load(directory/'capture.json');captures[(row['stage'],row['task_id'],row['repetition'],row['mode'])]=c
        if not row['execution_valid']:continue
        require(c['primary_ids']==ids['ids'] and c['primary_eog']==ids['eog'],'frontend primary sidecar '+label)
        require(len(c['decisions'])==len(c['primary_ids']) and all(x['committed_id']==c['primary_ids'][i] and x['output_index']==i for i,x in enumerate(c['decisions'])),'native decisions '+label)
        for e in c['proposal_events']:
            require(e['fixed_before_target_decode'] and len(e['proposal_tape'])==2 and len(e['batch_ids'])==3,'fixed k2 tape '+label)
            require(e['committed_prefix']==c['primary_ids'][:e['output_index']],'tape prefix '+label)
            require(e['batch_ids'][1:]==e['proposal_tape'],'batch proposal IDs '+label)
            require(e['batch_positions']==list(range(e['position'],e['position']+3)),'batch positions '+label)
        if not c['forked']:
            if row['mode']!='baseline':require(len(actual)<64 and ids['eog'][len(actual)-1],'no eligible fork '+label)
            continue
        cp=c['checkpoint'];idx=cp['output_index']
        eligible_events=[e for e in c['proposal_events'] if e['output_index']>=64]
        require(eligible_events and eligible_events[0]['output_index']==idx,'frozen first checkpoint rule '+label)
        require(cp['committed_ids']==c['primary_ids'][:idx] and cp['prompt_ids']==c['prompt_ids'],'checkpoint IDs '+label)
        before=state.get('capture.json.before.kv');restored=state.get('capture.json.restored.kv');after=state.get('capture.json.source_after.kv')
        require(before is not None and before==restored==after,'exact same-state bytes '+label)
        require(cp['state_bytes']==cp['consumed_bytes']==len(before),'restoration byte count '+label)
        require(cp['source_min_position']==cp['alternate_min_position'] and cp['source_max_position']==cp['alternate_max_position']==cp['position']-1,'state position '+label)
        require(cp['position']==len(c['prompt_ids'])+idx-1,'committed/KV position relation '+label)
        require(cp['sampler_chain']==cp['clone_chain'] and cp['sampler_seed']==cp['clone_seed'] and cp['sampler_history']==cp['clone_history'],'sampler clone identity '+label)
        require(cp['source_ubatch']==1 and cp['alternate_ubatch']==(1 if row['mode']=='control' else 128) and cp['n_batch']==512,'partition context '+label)
        require([r['output_tokens'] for r in c['primary_physical_graphs']]==[1,1,1],'native physical groups '+label)
        require([r['output_tokens'] for r in c['alternate_physical_graphs']]==([1,1,1] if row['mode']=='control' else [3]),'alternate physical groups '+label)
        alt=endpoint(c['alternate_ids'],c['alternate_eog'])
        require(alt[:idx]==actual[:idx],'common pre-fork output '+label)
        alt_block=[d for d in c['alternate_decisions'] if d['fork_first_block']]
        # Only decisions up to the first split have a common proposal-conditioned prefix.
        native=[d for d in c['decisions'] if idx<=d['output_index']<idx+len(alt_block)]
        require(1<=len(alt_block)<=3,'complete alternate verification block '+label)
        event=[];first=None
        for j,(a,b) in enumerate(zip(native,alt_block)):
            if a['batch_index']!=j:break # native rejected earlier; its next block is ineligible
            require(b['batch_index']==j and a['proposal_id']==b['proposal_id'],'paired common proposal '+label)
            for side,d in [('UB1',a),('alternate',b)]:
                require(d['top1_score']>=d['top2_score'] and abs(d['margin']-(d['top1_score']-d['top2_score']))<1e-4,'raw top2/margin '+label+side)
                require(d['accepted_proposal']==(d['proposal_id']>=0 and d['committed_id']==d['proposal_id']),'actual acceptance rule '+label+side)
            diff=a['committed_id']!=b['committed_id'] or a['accepted_proposal']!=b['accepted_proposal']
            event.append({'output_index':idx+j,'native':a,'alternate':b,'different_decision':diff})
            if diff:first=idx+j;break
            if not a['accepted_proposal'] or a['eog']:break
        require(bool(event),'paired decision coverage '+label)
        # Compare complete score rows even where rejected candidates are not committed.
        require(len(c['primary_scores'])==len(c['alternate_scores'])==3,'all fixed-batch logits rows '+label)
        recomputed_events.append({'stage':row['stage'],'task_id':row['task_id'],'repetition':row['repetition'],'mode':row['mode'],
            'checkpoint_output_index':idx,'paired_decisions':event,'first_different_decision':first,
            'primary_ids':actual,'alternate_ids':alt,'trajectory_first_divergence':divergence(actual,alt)})
    q=load(p/'TECHNICAL_QUALIFICATION.json')
    require(q['attempted_executions']==sum(k[0]=='r0' for k in rows),'R0 attempt coverage')
    require(q['reserved_executions']==0,'qualification reserved denominator')
    if q['status']=='PASS':
        require(len(q['results'])==6 and all(r['pass'] for r in q['results']),'all six R0 tasks')
        for t in R0:
            base=rows.get(('r0',t,1,'original'),{}).get('generated_ids')
            for mode in ('baseline','control','intervention'):
                require(rows.get(('r0',t,1,mode),{}).get('generated_ids')==base,'fresh native original equivalence '+t+mode)
            cs=[captures[('r0',t,1,m)] for m in ('baseline','control','intervention')]
            require(cs[0]['proposal_events']==cs[1]['proposal_events']==cs[2]['proposal_events'],'fresh R0 tape equivalence '+t)
            require(cs[1]['primary_scores']==cs[1]['alternate_scores'] and cs[1]['primary_ids']==cs[1]['alternate_ids'],'same-partition restoration control '+t)
    else:
        require(q['status']=='INTERVENTION_NOT_FEASIBLE' and any(not r['pass'] for r in q['results']),'failed qualification status')
        require(not any(k[0]=='reserved' for k in rows),'no reserved inference after failure')
        # Independently recompute failed comparison rather than trusting reported booleans.
        for r in q['results']:
            if 'checks' not in r:continue
            t=r['task_id'];original=rows[('r0',t,1,'original')]['generated_ids']
            baseline= captures[('r0',t,1,'baseline')];control=captures[('r0',t,1,'control')];pair=captures[('r0',t,1,'intervention')]
            require(r['checks']['new_original_baseline_ids_equal']==(original==endpoint(baseline['primary_ids'],baseline['primary_eog'])),'failed baseline check recomputed')
            require(r['checks']['control_full_continuation_ids_equal']==(control['primary_ids']==control['alternate_ids']),'failed continuation check recomputed')
            require(r['checks']['control_full_raw_checkpoint_scores_equal']==(control['primary_scores']==control['alternate_scores']),'failed score check recomputed')
            require(r['checks']['all_native_proposal_tapes_equal']==(baseline['proposal_events']==control['proposal_events']==pair['proposal_events']),'failed tape check recomputed')
    formal=[e for e in recomputed_events if e['stage']=='reserved'];formal_rows=[r for k,r in rows.items() if k[0]=='reserved']
    status=q['status'] if q['status']!='PASS' else 'FORMAL_NOT_EXECUTED'
    if formal_rows:
        f=load(p/'FORMAL_FREEZE.json');execution=load(p/'FORMAL_EXECUTION.json')
        require(datetime.fromisoformat(f['created_utc'])<min(datetime.fromisoformat(r['start_utc']) for r in formal_rows),'formal pre-inference freeze')
        require(f['identity_sha256']==digest(p/'BUILD_IDENTITY.json') and f['qualification_sha256']==digest(p/'TECHNICAL_QUALIFICATION.json'),'formal immutable checkpoint files')
        require(all(r['task_id'] in selected for r in formal_rows),'formal reserved tasks')
        actual_schedule=[(r['task_id'],r['repetition']) for r in execution['executions']]
        expected_schedule=[(r['task_id'],r['repetition']) for r in f['schedule']]
        require(actual_schedule==expected_schedule[:len(actual_schedule)],'complete schedule prefix, no replacement')
        if execution['status']=='EXECUTION_COMPLETE':
            require(len(formal_rows)==72 and len(actual_schedule)==72 and all(r['execution_valid'] for r in formal_rows),'full 24x3 coverage')
            status='TARGET_PARTITION_INTERVENTION_EFFECT_ON_TESTED_STATES' if any(e['first_different_decision'] is not None for e in formal) else 'NO_EFFECT_DETECTED_ON_TESTED_STATES'
        else:status='FORMAL_OPERATIONAL_FAILURE'
    summary={'status':status,'checks':checks,'errors':errors,'validation':'PASS' if not errors else 'FAIL',
        'r0_attempts':sum(k[0]=='r0' for k in rows),'reserved_attempts':len(formal_rows),'reserved_eligible_forks':len(formal),
        'reserved_prompt_count':len({r['task_id'] for r in formal_rows}),
        'execution_decision_effect_count':sum(e['first_different_decision'] is not None for e in formal),
        'prompt_decision_effect_count':len({e['task_id'] for e in formal if e['first_different_decision'] is not None}),
        'paired_decision_event_count':sum(len(e['paired_decisions']) for e in formal),
        'correlation_warning':'Repeated executions and within-prompt events are correlated, never independent prompts.',
        'limitations':'Byte-checkpoint hashes authenticate retained serialized KV, not omitted model/runtime bytes. Sampler cloning is source-audited and same-partition empirically checked; no opaque sampler byte serialization API is provided. Measurements cover only the prospectively sampled block.',
        'fork_events':recomputed_events}
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[3]);p.add_argument('--output',type=Path)
    a=p.parse_args();result=verify(a.root)
    if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='fork_events'},indent=2))
    raise SystemExit(bool(result['errors']))
