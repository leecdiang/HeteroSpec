"""Synthetic evidence rejection tests: CPU only, no model or executor import."""
import copy,json,struct,tempfile
from pathlib import Path
import verify100 as v
def main(root):
 rs=v.load(root/'STUDY_RECORDS.json');r=next(r for r in rs if r['phase']=='P1A' and r['observation_mode']=='heavy');x=v.load(root/r['raw_path']);tr=v.load(root/r['evidence_path'])
 def endpoint(z):v.endpoint100(z,z['prompt_ids'],128,r['owned_pid'])
 passed=[]
 def rejects(name,fn):
  try:fn()
  except (AssertionError,ValueError,struct.error,KeyError,IndexError):passed.append(name);return
  raise AssertionError('Malformed evidence accepted: '+name)
 def changed_endpoint(name,change):
  z=copy.deepcopy(x);change(z);rejects(name,lambda:endpoint(z))
 changed_endpoint('cropped_CAP_endpoint',lambda z:(z['ids'].pop(),z['eog'].pop(),z.update(length=len(z['ids']),terminal_id=z['ids'][-1],stop_reason='CAP')))
 changed_endpoint('wrong_owned_PID',lambda z:z.update(pid=z['pid']+1))
 changed_endpoint('wrong_output_capacity',lambda z:z['actual_condition'].update(output_capacity=4))
 changed_endpoint('fabricated_physical_rows',lambda z:z['workload'].update(target_micrograph_rows=z['workload']['target_micrograph_rows']+1))
 changed_endpoint('wrong_EOG_flag',lambda z:z['eog'].__setitem__(0,True))
 rejects('missing_registered_slot',lambda:v.compare_slots(['a'],['a','b']))
 rejects('duplicate_registered_slot',lambda:v.compare_slots(['a','a'],['a','b']))
 for name,change in [('intermediate_logits_request',lambda z:z['target'][0].update(last_output_requested=True,logits_requested_positions=[127])),('shifted_native_KV_positions',lambda z:z['target'][0].update(kv_max=z['target'][0]['kv_max']+1)),('fake_physical_width',lambda z:z['target'][0].update(physical_width_hist={'128':2}))]:
  z=copy.deepcopy(tr);change(z);rejects(name,lambda z=z:v.geometry100(z,x,x['prompt_ids'],128,x['partition100']['caller_lengths']))
 p=x['partition98']['full_payloads']['0'];k=bytearray(v.payload(root,p['sequence_KV']));k[0]^=1;rejects('bad_sequence_KV_magic',lambda:v.parse_kv(k,len(x['prompt_ids'])))
 k=bytearray(v.payload(root,p['sequence_KV']));struct.pack_into('<i',k,16,1);rejects('wrong_actual_KV_cell_position',lambda:v.parse_kv(k,len(x['prompt_ids'])))
 b=bytearray(v.payload(root,p['logits']));struct.pack_into('<f',b,0,float('nan'));rejects('NaN_FP32_logits',lambda:v.top2(b))
 q=dict(p['logits'],sha256='0'*64);rejects('raw_payload_tamper',lambda:v.payload(root,q))
 z=v.payload(root,p['sequence_KV']);rejects('cropped_state_payload',lambda:v.parse_kv(z[:-2],len(x['prompt_ids'])))
 # Pure parse/sample checks reject invalid injection data without unsafe native imports.
 result=dict(status='PASS',tests=len(passed),rejected=passed,model_forwards=0,native_imports=0,scope='Malformed source payloads/native endpoint/geometry/coordinate evidence')
 (root/'SYNTHETIC_REJECTION.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps(result))
if __name__=='__main__':
 import sys;main(Path(sys.argv[1]))
