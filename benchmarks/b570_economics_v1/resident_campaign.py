"""Resident lifecycle isolation and equally repaired SIMPLE/LOCAL development."""
from campaign_host import *
from costs import decompose

def build_for(stage,arm,mode):
 if mode==1:return ROOT/'observed02'/f'{stage}-{arm}'
 return ROOT/('resident04' if stage=='resident' else 'parallel04')/f'{arm}-mode{mode}'
def modes(stage):return ('R',) if stage=='resident' else ('S','L')
def env_for(stage,method,trace=False):
 e={}
 if method=='S':e['HS_ECON_WHOLE']='1'
 if trace:e['HS_ECON_MICROTRACE']='1';e['HS_TRANSFER_TRACE']='1';e['HS_PARALLEL_DISPATCH']='1'
 return e

@meter('qualification')
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
    assert metrics['continuation_phase']['destination_ub']==(128 if arm=='M' else 2 if stage=='parallel' else 1)
    assert metrics['target_continuation_ub']==metrics['continuation_phase']['destination_ub']
    results.append(dict(root=i,method=method,**q));print('RESIDENT_QUALIFIED',stage,i,method,arm,flush=True)
 write(ROOT/(stage.upper()+'_QUALIFIED.json'),dict(status='COMPLETE_T_CONTRACT_PASS',results=results,original_R_unchanged=True,strong_H1_and_caller_only_retained=True))

@meter('diagnostics')
def diagnostics(stage):
 assert (ROOT/(stage.upper()+'_QUALIFIED.json')).exists();records=[]
 inputs=read(ROOT/'EXPOSED_INPUTS.json')['inputs']
 for i,r in enumerate(inputs):
  for method in modes(stage):
   for arm in ('M','H1','C4U4','C4U1'):
    cost_key=f'{stage}-diagnostic-r{i}-{method}-{arm}-cost-only'
    key=f'{stage}-mechanism02-r{i}-{method}-{arm}';folder=ROOT/'runs'/key
    # Cost windows have clocks only. Heavy final-state and physical tracing
    # get their own separately charged mechanism request pair below.
    cost_folder=ROOT/'runs'/cost_key
    if not (cost_folder/'MODULE_AUDIT.json').exists():execute(cost_key,arm,[r,r],mode=1,build=build_for(stage,arm,1),environment=env_for(stage,method))
    old,_=bank(r['group'],r['index'])
    for j in (0,1):
     d=read(cost_folder/f'{j}.json');assert (d['prompt_ids'],d['ids'],d['eog'])==(old['prompt_ids'],old['ids'],old['eog'])
    cost_only=read(cost_folder/'1.json.cost.json');clean_cost=decompose(read(cost_folder/'1.json.metrics.json')['service_ms']/1000,cost_only)
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
    cont=[x for x in work if int(x['pos0'])>=len(r['prompt_ids'])]
    both_costs=[read(folder/f'{j}.json.cost.json') for j in (0,1)]
    owner=work[0]['kv'];trims=[]
    for line in lines:
     if line.startswith('ECON_TRIM '):
      d=dict(x.split('=',1) for x in line.split()[1:])
      if d['kv']==owner:trims.append(d)
    hist={}
    for x in cont:hist[x['rows']]=hist.get(x['rows'],0)+1
    records.append(dict(root=i,method=method,arm=arm,cost=clean_cost,mechanism_observed_cost=z,cost_has_heavy_final_state_or_microtrace=False,logical_target_verifies=sum(c['phases']['target_verify']['calls'] for c in both_costs),logical_target_ordinary_calls=sum(c['phases']['target_ordinary']['calls'] for c in both_costs),unique_target_micrographs=len(work),continuation_occupied_graphs=len(cont),continuation_rows=sum(int(x['rows']) for x in cont),continuation_width_histogram=hist,actual_reused_graphs=sum(int(x['reused']) for x in work),actual_rebuilt_graphs=sum(not int(x['reused']) for x in work),actual_target_trim_calls=len(trims),target_position_span_reductions=sum(int(x['before_max'])>int(x['after_max']) for x in trims),trim_events=trims,single_target_KV_owner=True,trace_includes_warmup=True,mechanism_service_has_final_state_observer=True,not_primary_clean_timing=True,micrographs=work))
    print('RESIDENT_DIAGNOSTIC',stage,i,method,arm,hist,flush=True)
 write(ROOT/(stage.upper()+'_DIAGNOSTICS.json'),dict(records=records,device_time=None,scope='separate observed runs; no diagnostic cost substitutes for clean service'))

@meter('pilot')
def pilot(stage):
 assert (ROOT/(stage.upper()+'_QUALIFIED.json')).exists();inputs=read(ROOT/'EXPOSED_INPUTS.json')['inputs']
 arms=[(m,a) for m in modes(stage) for a in ('M','H1','C4U4')]
 # Caller-only remains a separate named development control, never replaces H1.
 all_arms=arms+[(m,'C4U1') for m in modes(stage)]
 schedule=[]
 for block in range(2):
  for i,r in enumerate(inputs):
   order=all_arms[:] if (block+i)%2==0 else list(reversed(all_arms))
   for method,arm in order:
    control=arm=='C4U1';label='caller' if control else 'pilot'
    schedule.append(dict(name=f'{stage}-{label}-b{block}-r{i}-{method}-{arm}',root=i,block=block,method=method,arm=arm,control=control))
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

@meter('synchronized-diagnostics')
def synchronized(stage):
 assert (ROOT/(stage.upper()+'_QUALIFIED.json')).exists();inputs=read(ROOT/'EXPOSED_INPUTS.json')['inputs'];records=[]
 for i in (0,2):
  r=inputs[i];old,_=bank(r['group'],r['index'])
  for method in modes(stage):
   for arm in ('M','H1','C4U4'):
    name=f'{stage}-synchronized-r{i}-{method}-{arm}';folder=ROOT/'runs'/name
    if not (folder/'MODULE_AUDIT.json').exists():execute(name,arm,[r,r],mode=2,build=build_for(stage,arm,2),environment=env_for(stage,method))
    for j in (0,1):
     a=read(folder/f'{j}.json');assert (a['prompt_ids'],a['ids'],a['eog'])==(old['prompt_ids'],old['ids'],old['eog'])
    z=decompose(read(folder/'1.json.metrics.json')['service_ms']/1000,read(folder/'1.json.cost.json'))
    records.append(dict(root=i,method=method,arm=arm,cost=z,heavy_state_or_microtrace=False,not_clean_primary=True,device_kernel_times=None))
    print('SYNCHRONIZED_DIAGNOSTIC',stage,i,method,arm,flush=True)
 write(ROOT/(stage.upper()+'_SYNCHRONIZED.json'),dict(records=records,scope='fixed dev0 and long test1; host blocking envelopes, no device timestamps or overhead subtraction'))

if __name__=='__main__':
 action,stage=sys.argv[1:3];{'qualify':qualification,'diagnostics':diagnostics,'pilot':pilot,'synchronized':synchronized}[action](stage)
