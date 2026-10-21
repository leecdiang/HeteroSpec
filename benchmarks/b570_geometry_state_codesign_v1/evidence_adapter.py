"""Normalize only after the independent raw audit; no synthesized completion values."""
from pathlib import Path
from protocol import file_sha,digest
from raw_audit import audit,load
from contracts import validate_record

def adapt(directory,slot,runtime,runtime_hash):
 d=Path(directory);a=audit(d,slot,runtime);w=a['work'];ident=load(d/'IDENTITY.json');life=load(d/'LIFECYCLE.json')
 work=dict(target_continuation_width_hist=w['target_continuation_physical_width_hist'],target_continuation_graphs=sum(w['target_continuation_physical_width_hist'].values()),target_continuation_rows=sum(int(k)*v for k,v in w['target_continuation_physical_width_hist'].items()),target_continuation_callers=sum(w['verification_caller_width_hist'].values())+w['target_ordinary_rows'],draft_proposed_rows=w['draft_proposal_rows'],draft_catchup_rows=w['draft_catchup_rows'],accepted_proposals=w['accepted_committed'],rollback_calls=w['rollback_calls'])
 rec=dict(slot=slot['slot'],request_sha256=slot['request_sha256'],normalized_sent_request=slot['request'],runtime_manifest_sha256=runtime_hash,status='COMPLETED',pid=a['pid'],mode=slot['mode'],warmup=slot['warmup'],observation=dict(heavy_capture=slot['mode']=='diagnostic',added_sync=slot['mode']=='diagnostic',api_dump=False,gpu_queries=False),external_state_imports=0,teacher_forced_tokens=0,phase_recipe=slot['request']['recipe'],target_prefill_width_hist=w['target_prefill_physical_width_hist'],target_prefill_micrograph_widths=a['ordered_prefill'],all_target_weights_offloaded=ident['all_target_weights_offloaded'],no_draft_offload_violation=ident['no_draft_offload_violation'],request_begin_empty_state=True,lifecycle_closed=life['closed'],endpoint=a['endpoint'],work=work,runtime_role=slot['request']['recipe']['runtime'],process_group=slot['process_group'],lifecycle_id=life['lifecycle_id'],request_wall_ms=a['request_ms'],timer_contract='RESIDENT_RESET_PREFILL_DECODE_RECONCILE_END_SYNC',evidence_origin='NATIVE',raw_artifacts=[])
 for role,name in [('request','REQUEST.wire'),('result','RESULT.json'),('identity','IDENTITY.json'),('lifecycle','LIFECYCLE.json')]:
  p=d/name;rec['raw_artifacts'].append(dict(role=role,path=p.name,bytes=p.stat().st_size,sha256=file_sha(p)))
 if slot['mode']=='diagnostic':
  p=d/(slot['slot']+'.trace.json');rec['raw_artifacts'].append(dict(role='trace',path=p.name,bytes=p.stat().st_size,sha256=file_sha(p)))
 if slot['mode']=='diagnostic':
  for p in sorted(d.glob('*.bin'))+sorted(d.glob('*.f32')):rec['raw_artifacts'].append(dict(role='state_or_logits',path=p.name,bytes=p.stat().st_size,sha256=file_sha(p)))
 validate_record(slot,rec,runtime_hash,d)
 return rec
