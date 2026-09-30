"""Official independent validator: immutable core checks plus all-endpoint classification.

The original core was committed before R0. This supplement is frozen before
reserved inference and preserves all core integrity checks and the R0 gate.
"""
import argparse, json, hashlib
from pathlib import Path
from verify import verify

def digest(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def complete(root):
    root=Path(root);r=verify(root)
    p=root/'benchmarks/b570_partition_intervention_v1'
    formal=p/'FORMAL_FREEZE.json'
    if formal.exists():
        f=json.loads(formal.read_text(encoding='utf-8'))
        for name,h in f['source_files'].items():
            r['checks']+=1
            if digest(root/'scripts/platform/b570_partition_intervention_v1'/name)!=h:r['errors'].append('formal source digest: '+name)
    events=[e for e in r['fork_events'] if e['stage']=='reserved']
    score_changed=set();top1_changed=set();trajectory_changed=set()
    for e in events:
        directory=root/'artifacts/b570_partition_intervention_v1/raw/reserved'/(e['task_id'].replace('/','_')+f"-r{e['repetition']}-intervention")
        c=json.loads((directory/'capture.json').read_text(encoding='utf-8'))
        key=(e['task_id'],e['repetition'])
        if c['primary_scores']!=c['alternate_scores']:score_changed.add(key)
        if any(a['raw_top1_id']!=b['raw_top1_id'] for a,b in zip(c['primary_scores'],c['alternate_scores'])):top1_changed.add(key)
        if e['trajectory_first_divergence'] is not None:trajectory_changed.add(key)
    r['score_difference_executions']=len(score_changed);r['score_difference_prompts']=len({t for t,_ in score_changed})
    r['raw_top1_difference_executions']=len(top1_changed);r['raw_top1_difference_prompts']=len({t for t,_ in top1_changed})
    r['trajectory_difference_executions']=len(trajectory_changed);r['trajectory_difference_prompts']=len({t for t,_ in trajectory_changed})
    if r['status']=='NO_EFFECT_DETECTED_ON_TESTED_STATES' and (score_changed or trajectory_changed):
        r['status']='SCORE_OR_DOWNSTREAM_EFFECT_WITHOUT_IMMEDIATE_DECISION_EFFECT_AT_SAMPLED_CHECKPOINTS'
    r['validation']='FAIL' if r['errors'] else 'PASS'
    return r

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[3]);p.add_argument('--output',type=Path);a=p.parse_args()
    result=complete(a.root)
    if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='fork_events'},indent=2))
    raise SystemExit(bool(result['errors']))
