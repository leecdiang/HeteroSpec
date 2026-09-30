"""Official independent validator: immutable core checks plus all-endpoint classification.

The original core was committed before R0. This supplement is frozen before
reserved inference and preserves all core integrity checks and the R0 gate.
"""
import argparse, json, hashlib
from datetime import datetime
from pathlib import Path
from verify import verify
from git_evidence import verify_proof
from kv_metadata import verify_metadata

def digest(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def complete(root):
    root=Path(root);r=verify(root)
    r['errors'].extend(verify_proof(root))
    metadata_count,metadata_errors=verify_metadata(root)
    r['checks']+=metadata_count;r['errors'].extend(metadata_errors)
    r['serialized_kv_metadata_records_checked']=metadata_count
    p=root/'benchmarks/b570_partition_intervention_v1'
    reserved=json.loads((p/'RESERVED_SET.json').read_text(encoding='utf-8'))
    q=json.loads((p/'TECHNICAL_QUALIFICATION.json').read_text(encoding='utf-8'))
    raw=root/'artifacts/b570_partition_intervention_v1/raw'
    all_rows=[]
    for file in raw.glob('*/*/record.json'):
        row=json.loads(file.read_text(encoding='utf-8'));all_rows.append(row)
        flags={'--device':'Vulkan0','--n-gpu-layers':'all','--fit':'off','--ctx-size':'1024',
            '--batch-size':'512','--ubatch-size':'1','--flash-attn':'off','--n-predict':'127',
            '--temp':'0','--top-k':'0','--top-p':'1','--min-p':'0','--seed':'123',
            '--spec-type':'draft-simple','--spec-draft-device':'Vulkan0','--spec-draft-ngl':'all',
            '--spec-draft-n-max':'2','--spec-draft-n-min':'0'}
        for flag,value in flags.items():
            r['checks']+=1
            cmd=row['command']
            if cmd.count(flag)!=1 or cmd[cmd.index(flag)+1]!=value:r['errors'].append('frozen execution parameter '+flag+' '+str(file))
        r['checks']+=1
        cmd=row['command']
        if Path(cmd[cmd.index('--model')+1]).name!='Qwen3-8B-Q8_0.gguf' or Path(cmd[cmd.index('--spec-draft-model')+1]).name!='Qwen3-0.6B-Q8_0.gguf':
            r['errors'].append('frozen model pair '+str(file))
        if row['stage']=='reserved':
            r['checks']+=1
            if (file.parent/'prompt.txt').read_bytes()!=reserved['prompts'][row['task_id']]['input'].encode('utf-8'):
                r['errors'].append('actual reserved prompt differs from frozen input '+row['task_id'])
        else:
            originals=list((raw/'r0').glob(row['task_id'].replace('/','_')+'-r1-original/prompt.txt'))
            r['checks']+=1
            if not originals or (file.parent/'prompt.txt').read_bytes()!=originals[0].read_bytes():
                r['errors'].append('R0 conditions use different prompt bytes')
    r0=[x for x in all_rows if x['stage']=='r0']
    r['checks']+=1
    if r0 and any(datetime.fromisoformat(x['end_utc'])>datetime.fromisoformat(q['created_utc']) for x in r0):
        r['errors'].append('qualification report predates a qualification execution')
    formal=p/'FORMAL_FREEZE.json'
    if formal.exists():
        f=json.loads(formal.read_text(encoding='utf-8'))
        if datetime.fromisoformat(f['created_utc'])<=datetime.fromisoformat(q['created_utc']):
            r['errors'].append('formal freeze before technical qualification report')
        for name,h in f['source_files'].items():
            r['checks']+=1
            if digest(root/'scripts/platform/b570_partition_intervention_v1'/name)!=h:r['errors'].append('formal source digest: '+name)
    execution=p/'FORMAL_EXECUTION.json'
    if execution.exists():
        ordered=json.loads(execution.read_text(encoding='utf-8'))['executions']
        for a,b in zip(ordered,ordered[1:]):
            r['checks']+=1
            if datetime.fromisoformat(a['end_utc'])>datetime.fromisoformat(b['start_utc']):r['errors'].append('formal execution temporal overlap/order')
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
