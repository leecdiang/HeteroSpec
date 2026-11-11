"""Independent stdlib-only P0 admission; imports no executor."""
import argparse,json,hashlib,struct,collections
from pathlib import Path
def load(p):return json.loads(Path(p).read_bytes())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def out(x):return {k:x[k] for k in ['ids','eog','length','terminal_id','stop_reason','cap','prompt_ids']}
def gate(root):
 records=load(root/'STUDY_RECORDS.json');slots=[s for b in load(root/'PLAN.json')['blocks'] if b['phase']=='P0' for s in b['slots']]
 rs=[r for r in records if r['phase']=='P0'];errors=[];proof=[]
 if len(rs)!=16 or {r['slot'] for r in rs}!={s['slot'] for s in slots}:errors.append('Incomplete P0 own-path grid')
 hist=load(root/'baseline/pr99/STUDY_RECORDS.json')
 for r in rs:
  try:
   x=load(root/r['raw_path']);assert sha(root/r['raw_path'])==r['raw_sha256']
   slot=next(s for s in slots if s['slot']==r['slot']);donor=slot['restore_donors'][0]
   ref=next(t for t in hist if t['task']==r['task'] and t['arm']==donor and t['repeat']==1);old=load(root/'baseline/pr99'/ref['raw_path'])
   assert out(x)==out(old),'own-path full native output mismatch'
   d=x['restore100'];assert d and d['extra_forward_calls']==0 and d['clean_context_and_scheduler']
   assert d['receiver_ub']==512 and d['capacity']==1 and d['KV_min']==0 and d['KV_max']==len(x['prompt_ids'])-1
   p=old['partition98']['full_payloads']['0'];assert d['post_restore_KV_sha256']==p['sequence_KV']['sha256'] and d['post_restore_logits_sha256']==p['logits']['sha256']
   for field,orig in [('KV_source',p['sequence_KV']),('logits_source',p['logits'])]:
    assert d[field]['sha256']==orig['sha256'] and d[field]['bytes']==orig['bytes']
    assert sha(root/'baseline/pr99'/orig['path'])==orig['sha256']
   b=(root/'baseline/pr99'/p['logits']['path']).read_bytes();f=struct.unpack('<128256f',b);top=max(range(len(f)),key=f.__getitem__)
   assert top==d['natural_first_id']==x['ids'][0] and d['first_token_consumed_count']==1
   assert x['target_decode_calls']==len(x['ids'])-1 and not x['partition100']['caller_lengths'] and x['workload']['target_prefill_calls']==0
   assert x['workload']['target_continuation_physical_width_hist']=={'1':len(x['ids'])-1}
   if r['observation_mode']=='heavy':
    tr=load(root/r['evidence_path'])['target'];assert len(tr)==len(x['ids'])-1
    for i,t in enumerate(tr):assert t['phase']=='ORDINARY' and t['pos']==len(x['prompt_ids'])+i and t['input_ids']==[x['ids'][i]] and t['logits_requested_positions']==[len(x['prompt_ids'])+i] and t['physical_width_hist']=={'1':1}
   if r['observation_mode']=='heavy':
    prior={b['output_index_zero_based']:b for b in old['phase96']['boundaries']}
    for b in x['phase96']['boundaries']:
     refb=prior[b['output_index_zero_based']];assert b['full_logits_sha256']==refb['full_logits_sha256'] and b['sequence_KV_sha256']==refb['sequence_KV_sha256'],'post-restore continuation numerical-state mismatch'
   proof.append(dict(slot=r['slot'],original_donor=donor,complete_endpoint_equal=True,KV_byte_equal=True,FP32_byte_equal=True,no_extra_forward=True,natural_top1=top))
  except Exception as e:errors.append(dict(slot=r['slot'],error=str(e)))
 result=dict(status='PASS' if not errors else 'RESTORE_GATE_FAILED',causal_cross_admitted=not errors,contract='Validated boundary0 clean receiver + exact complete sequenceKV + full initial FP32 native greedy apply/accept equivalence; not general opaque actor clone',own_path_shams=len(rs),proof=proof,errors=errors)
 (root/'STATE_RESTORE_ADMISSION.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();print(json.dumps(gate(a.root)))
