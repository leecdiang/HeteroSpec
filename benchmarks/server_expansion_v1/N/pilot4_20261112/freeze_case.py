"""Extract one preselected saved supplied-history case; no tokenizer/model calls."""
import argparse,hashlib,json
from pathlib import Path

ROOT='330fc1cf-53dd-4d67-8201-2782df947dd5'
NEXT='b23c5984-720f-4e0c-907d-a0f33127c944'

def freeze(source,out):
    source,out=Path(source),Path(out)
    if out.exists(): raise RuntimeError('fresh fixture output required')
    files={n:(source/n).read_bytes() for n in ('SPEC.json','CORPUS.json','TOKENIZER_OUTPUT.jsonl')}
    token_sha=hashlib.sha256(files['TOKENIZER_OUTPUT.jsonl']).hexdigest()
    if token_sha!='23e812286a06ce6e067eb89648221b4348daeb1d3b5722aab780d09c56288350':
        raise RuntimeError('saved tokenizer source identity differs')
    corpus=json.loads(files['CORPUS.json']);spec=json.loads(files['SPEC.json'])
    turn=next(x for x in corpus['user_turns'] if x['message_id']==NEXT)
    if turn['root']!=ROOT: raise RuntimeError('case provenance changed')
    chain=turn['chain_to_node']; previous=chain[-2]
    wanted={'prompt:'+ROOT,'prompt:'+NEXT,'body:'+previous,'body:'+NEXT}
    tokens={};eog=None
    for raw in files['TOKENIZER_OUTPUT.jsonl'].splitlines():
        row=json.loads(raw)
        if row.get('event')=='vocabulary': eog=row['eog']
        elif row.get('task_id') in wanted: tokens[row['task_id']]=row['prompt_ids']
    q0=tokens['prompt:'+ROOT];q=tokens['prompt:'+NEXT]
    body=tokens['body:'+previous]
    logical=q0+body+[spec['provided_history_eog_id']];materialized=logical[:-1]
    k=0
    while k<min(len(materialized),len(q)) and logical[k]==q[k]: k+=1
    # Fixed continuation comes from the next supplied assistant body, not search.
    # Find its ID from the frozen root-to-leaf path, before inspecting token geometry.
    paths=corpus['root_to_leaf_paths']
    leaf='7bae9e1f-c90c-481e-80db-105aeba0b862'
    path=next(x for x in paths if x['root']==ROOT and x['leaf_message_id']==leaf)
    # Message ancestry is in the frozen message table; this avoids inventing IDs.
    messages=json.loads((source/'MESSAGES.json').read_text())
    by_id={x['message_id']:x for x in messages}
    node=by_id[leaf]; ancestry=[]
    while node:
        ancestry.append(node['message_id']);pid=node.get('parent_id');node=by_id.get(pid)
    ancestry.reverse();assistant=ancestry[ancestry.index(NEXT)+1]
    continuation=None
    for raw in files['TOKENIZER_OUTPUT.jsonl'].splitlines():
        r=json.loads(raw)
        if r.get('task_id')=='body:'+assistant: continuation=r['prompt_ids'][:8];break
    if not continuation or any(x in eog for x in continuation):
        raise RuntimeError('fixed first-eight supplied continuation unsuitable; no replacement case/tape')
    m=len(materialized);n=len(q);f=len(continuation)
    operations=[dict(id='R1_OLD',context='resident',rows=m),
        dict(id='R2_REPEAT_OLD',context='scratch-reset',rows=m),
        dict(id='R3_COLD_Q_AND_FIXED_F',context='scratch-reset',rows=n+f),
        dict(id='R4_RESIDENT_Q_AND_FIXED_F',context='resident-preserved-from-R1',rows=n-k+f)]
    result=dict(schema='hs.pilot4.supplied-history.v1',status='FROZEN_DESIGN_NOT_EXECUTED',
        parent_head='301df2f2cb47a432c3d2afb84c69aaebb16ea3f0',root=ROOT,next_user=NEXT,leaf=leaf,
        selection='first previously frozen PR226 development episode, before new numeric/latency observations',
        history_mode='SUPPLIED_HISTORY_TEACHER_FORCED_NOT_FREE_GENERATION',
        old_materialized_ids=materialized,old_logical_ids=logical,pending=logical[-1],canonical_next_ids=q,
        fixed_continuation_ids=continuation,continuation_source_message=assistant,predicted_retained_head=k,
        actual_native_head=None,requests=operations,planned_rows=sum(x['rows'] for x in operations),
        hard_limits=dict(requests=4,rows=8192,model_deployments=1,automatic_retry=False),
        contexts=2,model_objects=1,source_identities={n:dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest()) for n,b in files.items()},
        fixed_eog_ids=eog,model=spec['model'],template_sha256=spec['chat_template_sha256'],
        guarantee='initial-state repeat only; resident transition itself not independently repeated',
        native_calls=0)
    out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(dict(rows=result['planned_rows'],m=m,q=n,k=k,f=f,operations=operations)))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();freeze(a.source,a.out)
