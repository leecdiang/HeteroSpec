"""Independent A coverage, arrays, replay, stability and sealed-prediction checks."""
import json
from pathlib import Path
from verify_common import read,require,check_run,arr,difference,sha
CONDITIONS=['A_REFERENCE_UB1','A_TARGET_ONLY_UB2','A_H2_P_R','A_R_ONLY','A_NATIVE_BATCHED_LIVE']
def entries(root,phase,metadata):
    manifest=read(root/'work'/phase/'records.json');rows=manifest['runs'];results=[]
    stage='F1' if phase=='A-pre-live' else 'F2';receipt=read(metadata/(stage+'_REMOTE_RECEIPT.json'))
    for row in rows:
        d=root/row['path'];tape=d.parent/row['run_id'].replace('R_ONLY','H2_P_R')/'tape.jsonl' if row['canonical_condition']=='A_R_ONLY' else None
        v=check_run(d,tape,metadata);raw=v['record'];require(raw['generated_ids']==row['generated_ids'],'manifest vs raw A arrays')
        require(raw['source_head']==receipt['commit'] and receipt['remote_ack_utc']<manifest['started_utc']<=raw['started_utc']<raw['ended_utc']<=manifest['ended_utc'],'A source/order/process envelope')
        if (metadata/'F0_MANIFEST.json').exists() and raw.get('source_files_sha256'):
            frozen=read(metadata/'F0_MANIFEST.json')['files']
            for name,h in raw['source_files_sha256'].items():require(frozen['scripts/platform/rtx_trajectory_cost_v3/'+name]['sha256']==h,'A execution source differs from reviewed F0')
        results.append({**v,'task_id':row['task_id'],'repetition':row['repetition'],'canonical_condition':row['canonical_condition'],'path':row['path']})
    return manifest,results
def pre_live(root,metadata=None):
    root=Path(root);metadata=Path(metadata or root/'benchmarks/rtx_trajectory_cost_v3');p=read(metadata/'JOINT_PROTOCOL.json');tasks=p['A']['task_ids'];m,rows=entries(root,'A-pre-live',metadata)
    require([(r['task_id'],r['repetition'],r['canonical_condition']) for r in rows]==[(t,rep,c) for t in tasks for rep in [1,2,3] for c in CONDITIONS[:4]],'A pre-live fixed coverage/order')
    require(len({r['run_id'] for r in rows})==len(rows),'A duplicate run')
    stable={t+'|'+c:len({arr(r['ids']) for r in rows if r['task_id']==t and r['canonical_condition']==c})==1 for t in tasks for c in CONDITIONS[:4]}
    lookup={(r['task_id'],r['repetition'],r['canonical_condition']):r for r in rows};pairs=[]
    for t in tasks:
        for rep in [1,2,3]:
            a=lookup[t,rep,CONDITIONS[2]];b=lookup[t,rep,CONDITIONS[3]];pairs.append({'task_id':t,'repetition':rep,'first_divergence':difference(a['ids'],b['ids'])})
    exact=sum(x['first_divergence'] is None for x in pairs)
    status='PRE_LIVE_QUALIFIED' if all(stable.values()) and exact==len(tasks)*3 else 'REPEAT_INSTABILITY' if not all(stable.values()) else 'REPLAY_QUALIFICATION_FAILED'
    require(len(tasks)==24 and len(rows)==288,'A fixed 24x3x4 denominator')
    f1=read(metadata/'F1_REMOTE_RECEIPT.json');require(f1['remote_ack_utc']<m['started_utc'] and f1['full_retrieval_verified'],'A F1 ordering/retrieval')
    return {'status':status,'execution_complete':True,'valid_complete_runs':len(rows),'distinct_prompts':24,'repeat_stability':stable,'H2_R_ONLY':{'exact_pairs':exact,'total_pairs':72,'comparisons':pairs},'rows':rows}
def full(root,metadata=None):
    root=Path(root);metadata=Path(metadata or root/'benchmarks/rtx_trajectory_cost_v3');pre=pre_live(root,metadata);require(pre['status']=='PRE_LIVE_QUALIFIED','A live after failed pre-live')
    p=read(metadata/'JOINT_PROTOCOL.json');tasks=p['A']['task_ids'];lm,live=entries(root,'A-live',metadata)
    require([(r['task_id'],r['repetition'],r['canonical_condition']) for r in live]==[(t,rep,CONDITIONS[4]) for t in tasks for rep in [1,2,3]],'A live fixed coverage/order')
    f2=read(metadata/'F2_REMOTE_RECEIPT.json');require(f2['remote_ack_utc']<lm['started_utc'] and f2['full_retrieval_verified'],'A F2 before live/full retrieval')
    sealed=read(metadata/'A_trajectory/RESERVED_PREDICTIONS.json');require(len(sealed['rows'])==72,'full sealed rows missing')
    rows=pre['rows']+live;lookup={(r['task_id'],r['repetition'],r['canonical_condition']):r for r in rows};require(len(lookup)==360,'A five-condition coverage')
    for s,(t,rep) in zip(sealed['rows'],[(t,r) for t in tasks for r in [1,2,3]]):
        require((s['task_id'],s['repetition'])==(t,rep),'sealed row order')
        for c in CONDITIONS[:4]:
            r=lookup[t,rep,c];v=s['conditions'][c];require(v['generated_ids']==r['ids'] and v['array_sha256']==arr(r['ids']) and v['run_id']==r['run_id'],'sealed full arrays/run association')
        h=lookup[t,rep,CONDITIONS[2]];require(s['tape_sha256']==h['record']['tape_sha256'],'sealed proposal tape')
    comparisons={}
    for label,left,right in [('UB2_live',1,4),('H2_live',2,4),('R_ONLY_live',3,4),('reference_live',0,4),('H2_R_ONLY',2,3)]:
        pairs=[{'task_id':t,'repetition':r,'first_divergence':difference(lookup[t,r,CONDITIONS[left]]['ids'],lookup[t,r,CONDITIONS[right]]['ids'])} for t in tasks for r in [1,2,3]]
        comparisons[label]={'exact_pairs':sum(x['first_divergence'] is None for x in pairs),'total_pairs':72,'distinct_prompts':24,'wholly_exact_prompts':sum(all(x['first_divergence'] is None for x in pairs if x['task_id']==t) for t in tasks),'comparisons':pairs}
    divergent=[t for t in tasks if any(x['first_divergence'] is not None for x in comparisons['reference_live']['comparisons'] if x['task_id']==t)]
    stable={t+'|'+c:len({arr(lookup[t,r,c]['ids']) for r in [1,2,3]})==1 for t in tasks for c in CONDITIONS}
    candidates={}
    for label in ['UB2_live','H2_live','R_ONLY_live']:
        v=comparisons[label];status=('MATCH_DISCRIMINATING' if divergent else 'MATCH_NONDISCRIMINATING') if v['exact_pairs']==72 else 'PARTIAL_MATCH'
        candidates[label]={'status':status,'reference_divergent_prompt_results':[{'task_id':t,'all_three_exact':all(x['first_divergence'] is None for x in v['comparisons'] if x['task_id']==t)} for t in divergent]}
    return {'status':'COMPLETE_VALID' if all(stable.values()) else 'LIVE_REPEAT_INSTABILITY','execution_complete':True,'valid_complete_runs':360,'distinct_prompts':24,'comparisons':comparisons,'reference_divergent_prompts':divergent,'repeat_stability':stable,'candidates':candidates,'interpretation_limit':'Two predefined candidates on this frozen cohort; no necessity, uniqueness, minimality or cross-backend generalization'}
