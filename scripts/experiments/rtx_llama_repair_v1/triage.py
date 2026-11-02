"""Inspect a same-state probe with explicit row alignment; never guess a causal operator."""
from __future__ import annotations
import argparse, importlib, json, re
from pathlib import Path
from lr_common import *
import parent

def analyze(root,snapshot):
    root=Path(root);c=read(root/'CHECKPOINT.json')
    need(c['diagnostic_only'] and c['same_policy_own_path_vectors_equal'],'invalid own-path replay')
    need(c['source_is_canonical_R'] is False,'do not relabel C state as canonical R')
    need(file_hash(root/'before.state')==c['source_state_sha256'],'checkpoint corrupted')
    rows=[]
    for mapping,a,b,natural in zip(c['row_map'],c['scalar']['rows'],c['batch']['rows'],c['natural_rows'],strict=True):
        i=mapping['row'];need(i==a['row']==b['row']==natural['row'],'row identities')
        ap=root/'scalar'/a['file'];bp=root/'batch'/b['file']
        need(file_hash(ap)==a['sha256'] and file_hash(bp)==b['sha256']==natural['sha256'],'replay vector digest')
        rows.append(dict(mapping,bitwise_equal=a['sha256']==b['sha256'],
          scalar_argmax=a['argmax'],batch_argmax=b['argmax'],argmax_equal=a['argmax']==b['argmax']))
    result={'status':'SAME_STATE_REPLAY_REVIEWED','source_is_canonical_R':False,'rows':rows,
      'scope':'Only the selected C checkpoint and conditional verify rows. Unaccepted later rows are counterfactual, not natural R outputs.'}
    if not (root/'scalar/trace/INDEX.jsonl').exists() or not (root/'batch/trace/INDEX.jsonl').exists():return result
    parent.load(snapshot);tensors=importlib.import_module('tensors')
    def index(path):return [json.loads(l) for l in (path/'trace/INDEX.jsonl').read_text().splitlines() if l.strip()]
    left=index(root/'scalar');right=index(root/'batch');comparisons=[]
    allowed=re.compile(r'^(l_out-[0-9]+|result_norm|result_output)$')
    for b in right:
        if not allowed.fullmatch(b['name']):continue # q/k/attention nodes need separately reviewed axis maps
        need(b['caller_first_position']==c['base'] and b['caller_rows']==len(rows),'unexpected batched call')
        for mapping in c['row_map']:
            row=mapping['row'];matches=[a for a in left if a['name']==b['name'] and a['caller_first_position']==c['base']+row]
            need(len(matches)==1,'ambiguous/missing scalar checkpoint alignment')
            a=matches[0];need(a['caller_rows']==1,'scalar geometry')
            comp=tensors.compare(tensors.load_capture(root/'scalar',a),a,
              tensors.load_capture(root/'batch',b),b,left_row=0,right_row=row,axis=1)
            comparisons.append(dict(comp,name=b['name'],row=row,scalar_backend=a['scheduler_backend'],batch_backend=b['scheduler_backend']))
    result['captured_output_comparisons']=comparisons
    result['first_observed_checkpoint_mismatch']=next((x for x in comparisons if x.get('bitwise_equal') is False),None)
    result['causal_operator']='UNRESOLVED: capture producing nodes/immutable inputs and run own-path plus crossed-operand replays before attribution'
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--checkpoint',required=True);p.add_argument('--parent-snapshot',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();save(a.out,analyze(a.checkpoint,a.parent_snapshot),exclusive=True)
