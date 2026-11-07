"""Independent raw semantics. No imports from executor, adapter, or contracts.
Rebuilds values from native JSON/stdout and checks endpoint, identity, counters and trace.
"""
import json,hashlib,math
from pathlib import Path
EOG={128001,128008,128009}
def require(x,msg):
 if not x:raise ValueError(msg)
def load(p):
 def pairs(rows):
  out={}
  for k,v in rows:require(k not in out,'duplicate raw key');out[k]=v
  return out
 return json.loads(Path(p).read_text(encoding='utf-8-sig'),object_pairs_hook=pairs)
def audit(directory,slot,runtime):
 d=Path(directory);req=load(d/'REQUEST.json');result=load(d/'RESULT.json');ident=load(d/'IDENTITY.json');life=load(d/'LIFECYCLE.json')
 events=[json.loads(line) for line in (d/'stdout.jsonl').read_text(encoding='utf-8').splitlines()];native_results=[e for e in events if e.get('event')=='RESULT'];require(native_results==[result],'RESULT is not exact unique native stdout emission')
 launch=load(d/'LAUNCH.json');require(launch['runtime_role']==slot['request']['recipe']['runtime'] and launch['argv']==ident['argv'],'launch role/identity')
 wire=(d/'REQUEST.wire').read_bytes();require(hashlib.sha256(wire).hexdigest()==launch['wire_sha256'] and wire.decode()==launch['wire_utf8'],'actual sent bytes/launch admission');require(json.loads(wire)==req,'disk wire vs request');expected=slot['request'];recipe=expected['recipe'];pid=life['pid']
 require(life['returncode']==0 and life['closed'] and ident['pid']==result['pid']==pid,'owned lifecycle identity')
 require(req['request_id']==result['request_id']==slot['slot'] and req['prompt_ids']==result['prompt_ids']==expected['prompt_ids'],'request source identity')
 require(result['cap']==req['cap']==128 and result['observation_mode']==slot['mode'],'cap/observer drift')
 if recipe['runtime']=='new':
  require(req['normalized108']==result['normalized108']==expected,'actual native normalized echo')
  require(result['layout108']==recipe['continuation'] and result['effective_k108']==recipe['k'] and result['native_arg_k108']==1,'actual layout/effective CLI k')
 ids=result['ids'];flags=result['eog'];require(0<len(ids)<=128 and all(type(v)is int and 0<=v<128256 for v in ids),'native IDs')
 require(flags==[v in EOG for v in ids] and not any(flags[:-1]),'EOG/trailing suffix');require(result['length']==len(ids)==len(flags) and result['terminal_id']==ids[-1],'complete endpoint')
 require(result['stop_reason']==('EOG' if flags[-1] else 'CAP') and (flags[-1] or len(ids)==128),'stop')
 a=result['actual_condition'];require(a['prefill_ub']==expected['producer_plan']['ubatch'] and a['output_capacity']==recipe['capacity'] and a['maximum_k']==recipe['k'],'actual recipe')
 require(a['continuation_ub']==expected['continuation_ubatch'] and a['logical_batch']==512 and a['n_ctx']==1024 and a['threads']==10 and a['kv']=='F16' and a['flash_attention'] is False,'runtime condition')
 require(result['reset_target_min']==result['reset_target_max']==-1,'target reset')
 if recipe['draft']:require(result['reset_draft_min']==result['reset_draft_max']==-1,'draft reset')
 require(result['memory_violation'] is False,'native memory gate')
 for key in ('target','draft'):
  pins=runtime['roles'][recipe['runtime']]['modules'];actual={x['name'].lower():x for x in ident['modules']}
  for pin in pins:require(pin['name'].lower() in actual and actual[pin['name'].lower()]['sha256']==pin['sha256'],'loaded module drift')
 weights=[e for e in events if e.get('event')=='WEIGHT_MAP'];require(weights==ident['weights'] and len(weights)==(2 if recipe['draft'] else 1),'raw placement sources')
 require(all(e['pid']==pid and e['all_weights_Vulkan0'] and e['tensors'] and all(v['backend_device']=='Vulkan0' and v['gpu_backend_buffer'] for v in e['tensors']) for e in weights),'raw weight placement')
 require(ident['all_target_weights_offloaded'] and ident['no_draft_offload_violation'],'placement')
 side=load(d/(slot['slot']+('.trace.json' if slot['mode']=='diagnostic' else '.memory.json')));mem=side['memory'] if slot['mode']=='diagnostic' else side
 require(not mem['violation'] and mem['samples'],'memory receipt')
 for sample in mem['samples']:
  heaps=[v for v in sample['heaps'] if v['device_local']];require(len(heaps)==1 and heaps[0]['index']==0 and heaps[0]['physical_size_bytes']==10563354624,'dedicated B570 heap')
  free=int(heaps[0]['budget_bytes'])-int(heaps[0]['usage_bytes']);require(sample['pid']==pid and sample['vendor_id']==0x8086 and sample['device_id']==0xE20C and sample['adapter_luid_valid'] and sample['device_local_headroom_bytes']==free and free>=536870912,'signed same-PID memory headroom')
 w=result['workload'];require(w['output_ids_count']==len(ids),'output counter')
 require(w['proposal_generated']==sum(w[k] for k in ('accepted_committed','first_mismatch_rejected','unexamined_after_mismatch','terminal_discarded','unverified_before_verify')),'proposal conservation')
 require(len(ids)==sum(w[k] for k in ('initial_target_committed','accepted_committed','bonus_committed','correction_committed','fallback_committed')),'commit conservation')
 require(w['proposal_verified']==w['proposal_generated'] and w['accepted_committed']<=w['proposal_verified'],'verified proposals')
 for role in ('target','draft'):
  h=w[role+'_physical_width_hist'];require(all(str(int(k))==k and type(v)is int and v>=0 for k,v in h.items()),'hist schema')
  require(sum(h.values())==w[role+'_micrographs'] and sum(int(k)*v for k,v in h.items())==w[role+'_micrograph_rows'],'raw physical work')
 pre=w['target_prefill_physical_width_hist'];cont=w['target_continuation_physical_width_hist'];require(sum(int(k)*v for k,v in pre.items())==len(expected['prompt_ids']),'prefill consumed once')
 require(w['target_micrograph_rows']==len(expected['prompt_ids'])+w['target_verification_rows']+w['target_ordinary_rows'],'target row conservation')
 require(w['target_verification_rows']==w['proposal_verified']+w['verification_seed_rows'],'verify seed/proposal rows')
 require(w['verify_cycles']==w['verification_seed_rows']==w['rollback_calls'],'cycle rollback count')
 require(result['target_decode_calls']==w['target_prefill_calls']+sum(w['verification_caller_width_hist'].values())+w['target_ordinary_rows'],'target actual forwards')
 require(result['draft_decode_calls']==w['draft_prefill_calls']+w['draft_continuation_calls'],'draft actual forwards')
 require(math.isfinite(result['native_request_ms']) and result['native_request_ms']>0,'native request timer')
 observation=result['observation'];require(not observation['phase_timers'] and not observation['etw'],'unexpected observer')
 if slot['mode']=='counts':require(not observation['heavy_capture'] and not observation['added_sync'],'counts contamination')
 ordered=None;witnesses=[]
 if slot['mode']=='diagnostic':
  trace=load(d/(slot['slot']+'.trace.json'));pref=[r for r in trace['target'] if r.get('phase')=='PREFILL'];ordered=[]
  for row in pref:
   require(row['requested_logit_positions']==[len(expected['prompt_ids'])-1],'prefill final-only logits')
   ordered.extend(row['ordered_micrograph_widths'])
  for row in trace['target']:
   if row.get('phase')=='VERIFY':
    require(row['all_outputs'] and row['requested_logit_positions']==list(range(row['pos'],row['pos']+row['caller_rows'])),'VERIFY all-output positions')
    require(sum(row['ordered_micrograph_widths'])==row['caller_rows'],'VERIFY trace rows')
    if any(x>1 for x in row['ordered_micrograph_widths']):witnesses.append(row)
  if recipe['capacity']==4:
   before=(d/'initial.seqkv.bin').read_bytes();after=(d/'handoff.after.seqkv.bin').read_bytes();require(before==after,'independent handoff sequence bytes differ');require(len(result['binding108'])==1 and hashlib.sha256(before).hexdigest()==result['binding108'][0]['serialized_sequence_sha256'],'handoff raw/source hash')
  import struct
  require(len(result['initial108'])==(2 if recipe['draft'] else 1),'initial logits role count')
  for info in result['initial108']:
   p=(d/info['path']).resolve();require(p.is_relative_to(d.resolve()),'initial payload escape');data=p.read_bytes();require(len(data)==info['bytes']==128256*4 and hashlib.sha256(data).hexdigest()==info['sha256'],'full initial FP32 payload');values=[v[0] for v in struct.iter_unpack('<f',data)];require(all(math.isfinite(v) for v in values),'nonfinite initial logits')
   if info['role']=='TARGET':require(max(range(len(values)),key=values.__getitem__)==ids[0],'natural first target decision')
 return dict(endpoint={k:result[k] for k in ('ids','eog','length','terminal_id','stop_reason','cap')},work=w,ordered_prefill=ordered,verify_multirow_witnesses=witnesses,request_ms=result['native_request_ms'],target_forwards=result['target_decode_calls'],draft_forwards=result['draft_decode_calls'],pid=pid)
