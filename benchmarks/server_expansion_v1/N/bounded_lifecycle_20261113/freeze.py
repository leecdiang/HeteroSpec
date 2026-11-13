"""Freeze two existing supplied-history strata; read saved tokens only."""
import argparse,hashlib,json,time,datetime
from pathlib import Path
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--saved',required=True);p.add_argument('--episodes',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 source=Path(a.saved);out=Path(a.out)
 if out.exists():raise RuntimeError('fresh independent successor freeze required')
 raw={n:(source/n).read_bytes() for n in ['SPEC.json','CORPUS.json','MESSAGES.json','TOKENIZER_OUTPUT.jsonl']}
 if sha(raw['TOKENIZER_OUTPUT.jsonl'])!='23e812286a06ce6e067eb89648221b4348daeb1d3b5722aab780d09c56288350':raise RuntimeError('original saved tokens differ')
 spec=json.loads(raw['SPEC.json']);corpus=json.loads(raw['CORPUS.json']);messages={x['message_id']:x for x in json.loads(raw['MESSAGES.json'])}
 episodes=json.loads(Path(a.episodes).read_text());selected=[next(x for x in episodes if x['source_predicted_second_turn']['partition_distinct']==d) for d in (False,True)]
 tokens={};eog=None
 for line in raw['TOKENIZER_OUTPUT.jsonl'].splitlines():
  r=json.loads(line)
  if r.get('event')=='vocabulary':eog=r['eog']
  elif 'task_id' in r:tokens[r['task_id']]=r['prompt_ids']
 cases=[]
 for i,ep in enumerate(selected):
  first,next_user=ep['user_message_ids'];turn=next(t for t in corpus['user_turns'] if t['message_id']==next_user)
  body=tokens['body:'+turn['chain_to_node'][-2]];q0=tokens['prompt:'+first];q=tokens['prompt:'+next_user]
  node=messages[ep['leaf']];chain=[]
  while node:chain.append(node['message_id']);node=messages.get(node.get('parent_id'))
  chain.reverse();assistant=chain[chain.index(next_user)+1];f=tokens['body:'+assistant][:8]
  if len(f)!=8 or any(t in eog for t in f+body) or len(body)+1>128:raise RuntimeError('fixed case unsupported; no replacement selection')
  old=q0+body;logical=old+[spec['provided_history_eog_id']];k=0
  while k<min(len(old),len(q)) and logical[k]==q[k]:k+=1
  if len(q)+8>4096 or k!=ep['source_predicted_second_turn']['head']:raise RuntimeError('frozen geometry/capacity differs')
  cases.append(dict(id='C'+str(i),root=ep['root'],leaf=ep['leaf'],user_message_ids=ep['user_message_ids'],provided_assistant_source=turn['chain_to_node'][-2],fixed_continuation_source=assistant,initial_prompt_ids=q0,provided_assistant_ids=body,old_materialized_ids=old,old_logical_ids=logical,pending=logical[-1],canonical_next_ids=q,fixed_continuation_ids=f,predicted_retained_head=k,predicted_partition_distinct=ep['source_predicted_second_turn']['partition_distinct'],actual_native_head=None,initial_rows=len(old),append_rows=len(q)-k+8,cold_rows=len(q)+8))
 # Conservatively debit the completed four-request pilot without editing it.
 # The entire overnight total therefore cannot exceed the user's new total cap.
 end=datetime.datetime(2026,11,12,20,46,7,tzinfo=datetime.timezone.utc).timestamp()
 now=time.time();mono=time.monotonic()
 if now>=end-1200:raise RuntimeError('no safe new GPU start window remains')
 ops=[]
 for role in ['R','REPEAT','COLD','STRONG','LOCAL']:
  for c in cases:
   if role!='COLD':ops.append(dict(id=role+'/'+c['id']+'/INITIAL',role=role,case=c['id'],kind='INITIAL',rows=c['initial_rows']))
   ops.append(dict(id=role+'/'+c['id']+'/APPEND',role=role,case=c['id'],kind='COLD' if role=='COLD' else 'APPEND',rows=c['cold_rows'] if role=='COLD' else c['append_rows']))
 manifest=dict(schema='hs.bounded-lifecycle.manifest.v1',status='FROZEN_NOT_YET_ADMITTED',cases=cases,operations=ops,
  source_identities={n:dict(bytes=len(b),sha256=sha(b)) for n,b in raw.items()},episodes_file_sha256=sha(Path(a.episodes).read_bytes()),
  selection='first previously frozen no-difference and first previously frozen difference development episode; no offset/latency/output search',
  history='supplied assistant tokens replayed incrementally after exact canonical first-user prompt; not free generation',
  strict_rule='finite complete requested F32 vectors and canonical active F16 KV raw bits, aligned frontier/pending; no tolerance/argmax substitution',
  original_gpu_pilot=dict(requests=4,rows=732,deployments=1,archive_sha256='a4ab2f5e612fbb08a53066eb3d6f9e5c4bbcc00869c7876f1a395fa0edb1ba83',immutable=True),
  total_caps=dict(requests=76,rows=85738,deployments=10,raw_bytes=32*1024**3),
  new_remaining_caps=dict(requests=72,rows=85006,deployments=9),
  proposed_qualification=dict(requests=len(ops),rows=sum(x['rows'] for x in ops),deployments=5),
  window=dict(deadline_wall=end,deadline_mono=mono+end-now,no_new_worker_wall=end-1200,absolute_user_no_new_GPU_wall=datetime.datetime(2026,11,13,tzinfo=datetime.timezone.utc).timestamp(),worker_seconds=1200),
  disk=dict(protected_required_available_bytes=553094505923,raw_cap_bytes=32*1024**3,scope='old conservative553.1GB floor retained; selected two-case captures estimated below32GiB; no old data deletion'),
  performance='NOT_FROZEN_NOT_AUTOMATIC; only consider after reference/repeat/cold/strong and any relevant candidate qualification',
  retry='no automatic numerical retries; bounded engineering successor only after exact cause, actual release and remaining total budget checks',
  old261='not automatically required or promoted by this narrower supplied-history graph',model=spec['model'],template_sha256=spec['chat_template_sha256'],EOG_ids=eog)
 manifest['sha256']=sha(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode())
 out.write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n');print(json.dumps(dict(cases=[{k:c[k] for k in ['id','root','initial_rows','append_rows','cold_rows','predicted_retained_head']} for c in cases],qualification=manifest['proposed_qualification'],prior_immutable_debit=manifest['original_gpu_pilot'],remaining=manifest['new_remaining_caps'])))
if __name__=='__main__':main()
