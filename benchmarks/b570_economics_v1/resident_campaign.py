"""Resident lifecycle isolation and equally repaired SIMPLE/LOCAL development."""
from campaign_host import *
from costs import decompose

def build_for(stage,arm,mode):return ROOT/('resident03' if stage=='resident' else 'parallel02')/f'{arm}-mode{mode}'
def modes(stage):return ('R',) if stage=='resident' else ('S','L')
def env_for(stage,method,trace=False):
 e={}
 if method=='S':e['HS_ECON_WHOLE']='1'
 if trace:e['HS_ECON_MICROTRACE']='1';e['HS_TRANSFER_TRACE']='1'
 return e

def qualification(stage):
 inputs=read(ROOT/'EXPOSED_INPUTS.json')['inputs'];results=[]
 for i,r in enumerate(inputs):
  for method in modes(stage):
   for arm in ('M','H1','C4U4','C4U1'):
    key=f'{stage}-qual-r{i}-{method}-{arm}';h=ROOT/'runs'/(key+'-heavy');o=ROOT/'runs'/(key+'-off')
    if (h/'QUALIFICATION.json').exists():
     q=read(h/'QUALIFICATION.json');assert q['conditional_vectors']==q['equal_vectors'] and q['committed_states']==q['equal_states'] and q['heavy_off_final_equal']
    else:
     for label,folder,request,heavy in [('heavy',h,dict(r,heavy_state=True),True),('off',o,dict(r,audit_final=True),False)]:
      if not (folder/'MODULE_AUDIT.json').exists():execute(folder.name,arm,[r,request],heavy=heavy,build=build_for(stage,arm,0),environment=env_for(stage,method))
     ensure_references(r,h);q=qualify(r,arm,h,o)
    for j in (0,1):
     metrics=read(o/f'{j}.json.metrics.json')
     for k in ('reset_phase','continuation_phase'):
      p=metrics[k];assert p['same_context'] and p['same_KV_owner'] and not p['state_transfer'] and p['offline_witness_bytes']==0
     assert metrics['continuation_phase']['destination_ub']==(2 if stage=='parallel' and arm!='M' else 1)
    results.append(dict(root=i,method=method,**q));print('RESIDENT_QUALIFIED',stage,i,method,arm,flush=True)
 write(ROOT/(stage.upper()+'_QUALIFIED.json'),dict(status='COMPLETE_T_CONTRACT_PASS',results=results,original_R_unchanged=True,strong_H1_and_caller_only_retained=True))

def diagnostics(stage):
 assert (ROOT/(stage.upper()+'_QUALIFIED.json')).exists();records=[]
 inputs=read(ROOT/'EXPOSED_INPUTS.json')['inputs']
 for i,r in enumerate(inputs):
  for method in modes(stage):
   for arm in ('M','H1','C4U4','C4U1'):
    key=f'{stage}-diagnostic-r{i}-{method}-{arm}';folder=ROOT/'runs'/key
    if not (folder/'MODULE_AUDIT.json').exists():execute(key,arm,[r,dict(r,audit_final=True)],mode=1,build=build_for(stage,arm,1),environment=env_for(stage,method,True))
    clean=read(ROOT/'runs'/f'{stage}-qual-r{i}-{method}-{arm}-off/1.json');a=read(folder/'1.json')
    assert (a['prompt_ids'],a['ids'],a['eog'])==(clean['prompt_ids'],clean['ids'],clean['eog']) and state_equal(a['committed_states'][-1],clean['committed_states'][-1])
    cost=read(folder/'1.json.cost.json');z=decompose(read(folder/'1.json.metrics.json')['service_ms']/1000,cost)
    assert all(cost['phases'][k]['calls']==0 for k in ('transition','export_source','export_destination','export_source_after','import_state','context_create','context_destroy','state_checks','sampler_clone'))
    lines=(ROOT/'units'/key/'SUPERVISOR.stderr.log').read_text(encoding='utf-8',errors='replace').splitlines();micro=[]
    for line in lines:
     if line.startswith('ECON_MICRO '):
      fields=line.split();d=dict(x.split('=',1) for x in fields[2:]);d['serial']=int(fields[1]);micro.append(d)
    assert micro and len({x['serial'] for x in micro})==len(micro)
    target=next(x['ctx'] for x in micro if int(x['ub'])==128)
    work=[x for x in micro if x['ctx']==target];assert len({x['kv'] for x in work})==1
    cont=[x for x in work if int(x['ub'])!=128]
    hist={}
    for x in cont:hist[x['rows']]=hist.get(x['rows'],0)+1
    records.append(dict(root=i,method=method,arm=arm,cost=z,logical_target_verifies=cost['phases']['target_verify']['calls'],unique_target_micrographs=len(work),continuation_occupied_graphs=len(cont),continuation_rows=sum(int(x['rows']) for x in cont),continuation_width_histogram=hist,actual_reused_graphs=sum(int(x['reused']) for x in work),actual_rebuilt_graphs=sum(not int(x['reused']) for x in work),single_target_KV_owner=True,trace_includes_warmup=True,measured_service_has_final_state_observer=True,not_clean_timing=True,micrographs=work))
    print('RESIDENT_DIAGNOSTIC',stage,i,method,arm,hist,flush=True)
 write(ROOT/(stage.upper()+'_DIAGNOSTICS.json'),dict(records=records,device_time=None,scope='separate observed runs; no diagnostic cost substitutes for clean service'))

def pilot(stage):
 assert (ROOT/(stage.upper()+'_QUALIFIED.json')).exists();inputs=read(ROOT/'EXPOSED_INPUTS.json')['inputs']
 arms=[(m,a) for m in modes(stage) for a in ('M','H1','C4U4')]
 # Caller-only remains a separate named development control, never replaces H1.
 schedule=[]
 for block in range(2):
  for i,r in enumerate(inputs):
   order=arms[:] if (block+i)%2==0 else list(reversed(arms))
   for method,arm in order:
    schedule.append(dict(name=f'{stage}-pilot-b{block}-r{i}-{method}-{arm}',root=i,block=block,method=method,arm=arm,control=False))
   for method in modes(stage):schedule.append(dict(name=f'{stage}-caller-b{block}-r{i}-{method}-C4U1',root=i,block=block,method=method,arm='C4U1',control=True))
 out=ROOT/(stage.upper()+'_PILOT_SCHEDULE.json')
 if not out.exists():write(out,dict(schedule=schedule,main_measurements=len(arms)*8,main_warmups=len(arms)*8,caller_only_measurements=len(modes(stage))*8,caller_only_warmups=len(modes(stage))*8,structural_fixed_inputs=True))
 assert read(out)['schedule']==schedule
 records=[]
 for x in schedule:
  r=inputs[x['root']];folder=ROOT/'runs'/x['name']
  if not (folder/'MODULE_AUDIT.json').exists():execute(x['name'],x['arm'],[r,r],build=build_for(stage,x['arm'],0),environment=env_for(stage,x['method']))
  old,_=bank(r['group'],r['index'])
  for j,kind in enumerate(('warmup','measure')):
   a=read(folder/f'{j}.json');assert (a['prompt_ids'],a['ids'],a['eog'])==(old['prompt_ids'],old['ids'],old['eog'])
   p=folder/f'{j}.json.metrics.json';metrics=read(p)
   records.append(dict(**x,kind=kind,input_id=r['id'],root_id=r['root_id'],service_s=metrics['service_ms']/1000,metrics_sha256=sha(p),drafted=metrics['drafted'],accepted=metrics['accepted'],endpoint_equal=True))
  print('RESIDENT_PILOT',x['name'],flush=True)
 write(ROOT/(stage.upper()+'_PILOT.json'),dict(records=records,complete_service=True,all_inputs_and_controls_retained=True))

if __name__=='__main__':
 action,stage=sys.argv[1:3];{'qualify':qualification,'diagnostics':diagnostics,'pilot':pilot}[action](stage)
