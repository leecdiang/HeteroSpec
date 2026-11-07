"""Pre-reserved analysis separating raw score, immediate decision and downstream endpoints.

Added during engineering R0, before any reserved inference. This does not modify
the frozen frontend, loop, build identity, checkpoint rule or qualification gate.
"""
import argparse, hashlib, json
from pathlib import Path

def digest(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def characterize(root):
    root=Path(root);p=root/'benchmarks/b570_partition_intervention_v1'
    v=json.loads((p/'INDEPENDENT_VALIDATION.json').read_text(encoding='utf-8'))
    assert v['validation']=='PASS',v['errors']
    events=[]
    for e in v['fork_events']:
        if e['mode']!='intervention':continue
        directory=root/'artifacts/b570_partition_intervention_v1/raw'/e['stage']/(e['task_id'].replace('/','_')+f"-r{e['repetition']}-intervention")
        c=json.loads((directory/'capture.json').read_text(encoding='utf-8'))
        score_rows=[]
        for i,(a,b) in enumerate(zip(c['primary_scores'],c['alternate_scores'])):
            score_rows.append({'batch_index':i,'native':a,'alternate':b,'score_record_exact':a==b,
                'top1_id_different':a['raw_top1_id']!=b['raw_top1_id'],
                'top1_score_delta_alternate_minus_native':b['top1_score']-a['top1_score'],
                'margin_delta_alternate_minus_native':b['margin']-a['margin'],
                'proposal_score_delta_alternate_minus_native':None if a['proposal_score'] is None else b['proposal_score']-a['proposal_score']})
        events.append({'stage':e['stage'],'task_id':e['task_id'],'repetition':e['repetition'],
            'checkpoint_output_index':e['checkpoint_output_index'],'score_rows':score_rows,
            'score_record_difference':any(not r['score_record_exact'] for r in score_rows),
            'raw_top1_difference':any(r['top1_id_different'] for r in score_rows),
            'first_immediate_different_decision':e['first_different_decision'],
            'trajectory_first_divergence':e['trajectory_first_divergence'],
            'primary_ids':e['primary_ids'],'alternate_ids':e['alternate_ids']})
    formal=[e for e in events if e['stage']=='reserved']
    q=json.loads((p/'TECHNICAL_QUALIFICATION.json').read_text(encoding='utf-8'))
    if q['status']!='PASS':status='INTERVENTION_NOT_FEASIBLE'
    elif v['status']=='FORMAL_OPERATIONAL_FAILURE':status=v['status']
    elif v['reserved_attempts']==0:status='FORMAL_NOT_EXECUTED'
    elif any(e['first_immediate_different_decision'] is not None for e in formal):
        status='TARGET_PARTITION_INTERVENTION_EFFECT_ON_TESTED_STATES'
    elif any(e['score_record_difference'] or e['trajectory_first_divergence'] is not None for e in formal):
        status='SCORE_OR_DOWNSTREAM_EFFECT_WITHOUT_IMMEDIATE_DECISION_EFFECT_AT_SAMPLED_CHECKPOINTS'
    else:status='NO_EFFECT_DETECTED_ON_TESTED_STATES'
    counts={}
    for name,condition in [('score_record_difference',lambda e:e['score_record_difference']),
        ('raw_top1_difference',lambda e:e['raw_top1_difference']),
        ('immediate_decision_difference',lambda e:e['first_immediate_different_decision'] is not None),
        ('downstream_trajectory_difference',lambda e:e['trajectory_first_divergence'] is not None)]:
        counts[name]={'executions':sum(condition(e) for e in formal),'prompts':len({e['task_id'] for e in formal if condition(e)})}
    return {'status':status,'independent_validation_sha256':digest(p/'INDEPENDENT_VALIDATION.json'),
        'reserved_executions':v['reserved_attempts'],'reserved_prompts':v['reserved_prompt_count'],
        'eligible_reserved_forks':len(formal),'counts':counts,'events':events,
        'interpretation':'Only an actual immediate decision split supports a decision effect at the sampled block. Raw score and downstream trajectory effects are separately counted. NO_EFFECT requires all three endpoints unchanged. R0 events are exposed diagnostics excluded from formal counts.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[3]);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=characterize(a.root);a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='events'},indent=2))
