"""Four exposed diagnostic requests; no extra pilot/confirmation measurements."""
from smol_verify import *

def run():
 r=input_row('development',0);arm='C4U4'
 execute('stream-bridge-heavy',arm,[r,dict(r,heavy_state=True)],heavy=True)
 execute('stream-bridge-off',arm,[r,dict(r,audit_final=True)])
 a=read(SROOT/EPOCH/'runs/stream-bridge-heavy/1.json');b=read(captures('development',0,arm,'heavy')/'1.json');off=read(SROOT/EPOCH/'runs/stream-bridge-off/1.json')
 assert all(a[k]==b[k] for k in ('prompt_ids','ids','eog','commits','trace'))
 assert (a['ids'],a['eog'])==(off['ids'],off['eog'])
 assert len(a['full_target_vectors'])==len(b['full_target_vectors'])
 for x,y in zip(a['full_target_vectors'],b['full_target_vectors'],strict=True):
  assert x['prefix']==y['prefix'] and native_path(x['path']).read_bytes()==native_path(y['path']).read_bytes()
 assert len(a['committed_states'])==len(b['committed_states'])
 for x,y in zip(a['committed_states'],b['committed_states'],strict=True):assert state_equal(x,y)
 assert state_equal(a['committed_states'][-1],off['committed_states'][-1])
 write(SROOT/EPOCH/'STREAM_BRIDGE.json',dict(status='FINITE_NATIVE_STREAM_STORAGE_BRIDGE_PASS',exposed_development_index=0,arm=arm,conditional_vectors=len(a['full_target_vectors']),committed_states=len(a['committed_states']),all_old_independently_qualified_values_equal=True,heavy_off_final_equal=True,extra_engineering_requests=4,extra_timing_slots=0,native_executable_unchanged=True))

if __name__=='__main__':run()
