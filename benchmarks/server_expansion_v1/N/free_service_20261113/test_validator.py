"""Synthetic validator boundary regressions; explicitly NOT native evidence."""
import argparse,copy,importlib.util,json,struct
from pathlib import Path
def main(config):
 here=Path(__file__).resolve().parent;spec=importlib.util.spec_from_file_location('verify',here/'verify.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);cfg=json.loads(Path(config).read_text());base=Path(cfg['root'])/'validator-cpu01';base.mkdir(mode=0o700);root=base/'fixture';root.mkdir();ep=root/'episode';ep.mkdir();user=[dict(role='user',content='a'),dict(role='user',content='b')];eog=128247;history=[user[0]];rs=[]
 def put(p,j):p.open('x').write(json.dumps(j))
 def kv(name,h):
  (ep/(name+'.kv')).write_bytes(bytes(h*147456));t=[dict(kind=k,layer=i) for k in ['K','V'] for i in range(36)] if h else [];put(ep/(name+'.json'),dict(head=h,capacity=4096,active_bytes=h*147456,tensors=t,cells=[[i,i,0] for i in range(h)],physical_by_position=list(range(h))))
 f=[0.0]*151936;f[eog]=2.0;raw=struct.pack('<151936f',*f)
 for t,q,k in [(0,[10],0),(1,[10,11],1)]:
  message=dict(role='assistant',content='');client=dict(role='assistant',content='');wire=dict(choices=[dict(finish_reason='stop',index=0,message=client)],created=1,id='',system_fingerprint='CPU',model='synthetic',usage=dict(prompt_tokens=len(q),completion_tokens=1,prompt_tokens_details=dict(cached_tokens=k)));consumer=dict(sampled_ids=[eog],stop='EOG',cap=128,pending=eog,pieces=[dict(id=eog,piece_hex='',special=False)],parser_input_hex='',client_message=client,wire_response_json=json.dumps(wire),history_after=history+[message]);rs.append(dict(id='CPU-R-T'+str(t),turn=t,prompt=dict(canonical_ids=q,history=copy.deepcopy(history)),retained=k,native_head_after=len(q),logical_ids=q+[eog],pending=eog,frontier_valid=True,retained_frontier_valid=False,consumer=consumer,sampling_vectors=1,rows=1));history+= [message,user[1]] if t==0 else [message];(ep/f'T{t}-V000.f32').write_bytes(raw);kv(f'T{t}-prompt',len(q));kv(f'T{t}-terminal',len(q))
 kv('T1-retained',1);kv('reset',0);put(ep/'RESET.json',dict(head=0,pending=None,frontier_valid=False,native_reset_s=0));put(root/'MANIFEST.json',dict(cases=[dict(id='CPU',users=user,initial_ids=[10])],EOG_ids=[eog]));put(root/'STATE.json',dict(requests={r['id']:dict(rows=1,status='COMPLETED') for r in rs}));episode=dict(episode='CPU',stage='R',arm='R',case='CPU',requests=rs,calls=[dict(request=rs[0]['id'],input_ids=[10],rows=1,position=0,head_after=1,requested_output_mask='last_only'),dict(request=rs[1]['id'],input_ids=[11],rows=1,position=1,head_after=2,requested_output_mask='last_only')],dispatch=None,n_ctx=4096,threads=2,graphs=False,FA=False,actual_KV='F16',free_generation=True,capture_depth='synthetic fixture only');put(ep/'EPISODE.json',episode)
 report=v.verify(root,'episode','CPU_NONCE','CPU_JOB',str(Path(cfg['root'])/'raw-cpu-checker'),base/'PASS.json');tests=['synthetic valid structure/finite/greedy']
 # Fail before raw scan on a pending mismatch, then on retained KV corruption
 # at the same unchanged head. These expected failures never invoke a model.
 changed=copy.deepcopy(episode);changed['requests'][1]['pending']=64;(ep/'EPISODE.json').write_text(json.dumps(changed))
 try:v.verify(root,'episode','CPU_NONCE','CPU_JOB',str(Path(cfg['root'])/'raw-cpu-checker'),base/'should-not-pass-pending.json');raise AssertionError('pending bypass')
 except RuntimeError as e:
  if 'pending/head/ownership' not in str(e):raise
 tests.append('pending mismatch rejected');(ep/'EPISODE.json').write_text(json.dumps(episode));bad=bytearray((ep/'T1-retained.kv').read_bytes());bad[16]=1;(ep/'T1-retained.kv').write_bytes(bad)
 try:v.verify(root,'episode','CPU_NONCE','CPU_JOB',str(Path(cfg['root'])/'raw-cpu-checker'),base/'should-not-pass-KV.json');raise AssertionError('retained KV bypass')
 except RuntimeError as e:
  if 'retained-prefix bytes changed' not in str(e):raise
 tests.append('same-head retained-prefix corruption rejected');put(base/'RESULT.json',dict(status='PASS_SYNTHETIC_VALIDATOR_BOUNDARIES',tests=tests,model_calls=0,GPU_contexts=0,native_qualification=False));print(tests)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--config',required=True);a=p.parse_args();main(a.config)
