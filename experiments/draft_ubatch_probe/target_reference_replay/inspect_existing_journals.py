#!/usr/bin/env python3
"""Derive replay plans from PR183 fixture reports; never treats them as GPU evidence."""
import argparse,hashlib,json
from pathlib import Path
import replay_audit as A
p=argparse.ArgumentParser();p.add_argument('--fixture-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
result={'scope':'PLAN_ONLY from existing synthetic CPU records; no new inference; tokenizer/deployment capture binding incomplete', 'models':{}}
for name in ('release-dense','release-q8','stress-dense','stress-q8'):
    published=a.fixture_root/'evidence'/(name+'-attempts.jsonl')
    if published.is_file():
        source=published;raw=source.read_bytes();events=[json.loads(line) for line in raw.splitlines()]
        A.need(len(events)%2==0,'INCOMPLETE: unmatched attempt start')
        cases=[]
        for i in range(0,len(events),2):
            start,end=events[i:i+2]
            A.need(start['status']=='STARTED' and end['status']=='COMPLETED','INCOMPLETE: non-completed attempt retained')
            c=end['result']
            A.need([start[k] for k in ('ubatch','reject','cap','stop')]==[c[k] for k in ('draft_ubatch','forced_reject_index','cap','stop_after_output_index')],'attempt start/result identity differs')
            cases.append(c)
        r={'attempts':cases};receipt=json.loads((published.parent/(name+'-RECEIPT.json')).read_text());fmt='published_attempts_jsonl'
    else:
        d=a.fixture_root/name;source=d/'native.stdout';raw=source.read_bytes();r=json.loads(raw);receipt=json.loads((d/'RECEIPT.json').read_text());fmt='local_native_stdout'
    identity={'reference_deployment_sha256':A.digest({'role':'scalar-fixture-plan','receipt':receipt}),
      'candidate_deployment_sha256':A.digest({'role':'candidate-fixture-plan','receipt':receipt}),
      'target_model_sha256':receipt['model_sha256'],'tokenizer_sha256':'0'*64,'vocab':128,'n_ctx':128,'eog_ids':[],
      'kv_bytes_per_token':0,'state_format':'UNPROVEN_NO_NORMALIZED_KV_PAYLOAD','scope':'UNBOUND_CPU_JOURNAL_PLANNING_ONLY',
      'candidate_target_ubatch':1,'candidate_prefill_recipe':'whole_prompt_last_only','reference_recipe':'tokenwise_all','binding_complete':False,'binding_notes':'Tokenizer zero digest is an explicit absent-identity sentinel; no native deployment attestation.'}
    plans=[A.make_plan(c,[1,2,3,4,5,6,7],identity) for c in r['attempts']]
    result['models'][name]={'input_sha256':hashlib.sha256(raw).hexdigest(),'input_format':fmt,'input_file':str(source.relative_to(a.fixture_root)),'cases':len(plans),
      'target_vector_uses':sum(len(x['uses']) for x in plans),
      'fresh_maximal_path_jobs':sum(len(x['fresh_replay_jobs']) for x in plans),
      'naive_reference_token_evaluations':sum(sum(len(q['tokens']) for q in x['queries']) for x in plans),
      'maximal_path_reference_token_evaluations':sum(sum(len(j['tokens']) for j in x['fresh_replay_jobs']) for x in plans),
      'verification_cycles':sum(len(x['case']['cycles']) for x in plans),
      'commit_snapshots_required':sum(len(x['commits']) for x in plans),
      'cases_with_terminal_unmaterialized_token':sum(bool(x['commits'][-1]['unmaterialized_output']) for x in plans),
      'cases_with_terminal_materialized_token':sum(not x['commits'][-1]['unmaterialized_output'] for x in plans),
      'qualification_status':'UNPROVEN: source journals lack required native capture/payloads; planning only'}
with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
