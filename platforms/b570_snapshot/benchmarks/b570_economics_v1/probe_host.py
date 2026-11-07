"""Actual q2/q4/q32, extent-adjacent/tails, cap1 and rollback mechanisms."""
from resident_campaign import *
from stage_costs import once

def build():
 d=ROOT/'known-probe03'
 if (d/'FILES.json').exists():return d
 base=build_for('parallel','M',1);d.mkdir()
 for p in base.iterdir():
  if p.is_file() and p.suffix.lower() in ('.cpp','.h','.hpp','.txt'):shutil.copyfile(p,d/p.name)
 shutil.copyfile(HERE/'native/known_probe.inc',d/'known_probe.inc')
 p=d/'target.cpp';s=p.read_text();key='    std::vector<llama_token> generated;';s=once(s,key,'    #include "known_probe.inc"\n'+key)
 key='    auto init = common_init_from_params(params);';s=once(s,key,'    params.n_outputs_max=32;params.n_outputs_max_per_seq=32; // Explicit mechanism-only all-row outputs.\n'+key);p.write_text(s)
 command(['cmake','-S',d,'-B',d/'build','-G','Visual Studio 17 2022','-A','x64'],d/'configure.log')
 command(['cmake','--build',d/'build','--config','Release','--target','b570-closeout-target','--parallel','4'],d/'compile.log')
 bins=d/'build/Release'
 for p in (base/'build/Release').glob('*.dll'):shutil.copyfile(p,bins/p.name)
 write(d/'FILES.json',dict(files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in bins.iterdir() if p.suffix.lower() in ('.exe','.dll')]))
 write(d/'SOURCE.json',dict(files={p.name:sha(p) for p in d.iterdir() if p.suffix in ('.cpp','.h','.hpp','.txt','.inc')},mechanism_only=True,output_reserve=32,natural_pilot_uses_unchanged_reserves=True,known_tokens_from_exposed_R=True))
 return d

@meter('known-probes')
def known():
 build();r=read(ROOT/'EXPOSED_INPUTS.json')['inputs'][0];old,ref=bank(r['group'],r['index']);ids=old['ids'];cases=[]
 # Real greedy prefixes of dev0: no token padding or natural-input selection.
 for width in (2,4,32):
  for head in (254,255,256):
   start=head-len(r['prompt_ids']);cases.append(dict(name=f'q{width}-h{head}',prelude=ids[:start],known_suffix=ids[start:start+width],width=width,rollback=0))
 for tail in (1,2,3):
  cases.append(dict(name=f'q32-tail{tail}',prelude=[],known_suffix=ids[:32+tail],width=32,rollback=0))
 start=255-len(r['prompt_ids']);cases.append(dict(name='rollback-q2-h255',prelude=ids[:start],known_suffix=ids[start:start+2],after_rollback=ids[start+1:start+3],width=2,rollback=1))
 plan=ROOT/'KNOWN_PROBE_PLAN.json'
 if not plan.exists():write(plan,dict(input_id=r['id'],cases=cases,exposed_development_only=True,natural_timing=False,models_changed=False))
 assert read(plan)['cases']==cases;results=[]
 for method in ('S','L'):
  for case in cases:
   name='known-'+method+'-'+case['name'];folder=ROOT/'runs'/name;request=dict(r,**{k:v for k,v in case.items() if k!='name'})
   if not (folder/'MODULE_AUDIT.json').exists():execute(name,'M',[request,dict(request,heavy_state=True)],mode=1,heavy=True,build=build(),environment=env_for('parallel',method,True))
   a=read(folder/'1.json');ensure_references(r,folder);_,ref=bank(r['group'],r['index'])
   vals=[native_path(x['path']).read_bytes()==native_path(ref[tuple(x['prefix'])]['frontier']).read_bytes() for x in a['full_target_vectors']]
   states=[state_equal(x,ref[tuple(x['prefix'])]) for x in a['committed_states']]
   z=dict(case=case['name'],method=method,conditional_vectors=len(vals),vectors_equal=sum(vals),states=len(states),states_equal=sum(states),mechanism_only=True)
   write(folder/'QUALIFICATION.json',z);assert all(vals) and all(states),z;results.append(z);print('KNOWN_PROBE_PASS',method,case['name'],flush=True)
 write(ROOT/'KNOWN_PROBE_RESULTS.json',dict(results=results,natural_performance_samples=0,reference_producer_unchanged=True))

@meter('cap1-probes')
def caps():
 r=read(ROOT/'EXPOSED_INPUTS.json')['inputs'][0];old,ref=bank(r['group'],r['index']);reference=dict(old,ids=old['ids'][:1],eog=old['eog'][:1]);results=[]
 for stage in ('resident','parallel'):
  for method in modes(stage):
   for arm in ('M','H1','C4U4','C4U1'):
    key=f'cap1-{stage}-{method}-{arm}';h=ROOT/'runs'/(key+'-heavy');o=ROOT/'runs'/(key+'-off')
    for folder,request,heavy in [(h,dict(r,cap=1,heavy_state=True),True),(o,dict(r,cap=1,audit_final=True),False)]:
     if not (folder/'MODULE_AUDIT.json').exists():execute(folder.name,arm,[dict(r,cap=1),request],heavy=heavy,build=build_for(stage,arm,0),environment=env_for(stage,method))
    a=read(h/'1.json');b=read(o/'1.json');assert a['ids']==b['ids']==reference['ids'] and a['eog']==b['eog']==reference['eog']
    contract=boundaries(a,reference,arm);contract['terminal_kind']='CAP1'
    vals=[native_path(x['path']).read_bytes()==native_path(ref[tuple(x['prefix'])]['frontier']).read_bytes() for x in a['full_target_vectors']]
    states=[state_equal(x,ref[tuple(x['prefix'])]) for x in a['committed_states']]
    assert vals and states and all(vals) and all(states) and state_equal(a['committed_states'][-1],b['committed_states'][-1])
    z=dict(stage=stage,method=method,arm=arm,contract=contract,vectors=len(vals),states=len(states),complete_contract_equal=True);write(h/'QUALIFICATION.json',z);results.append(z);print('CAP1_PASS',stage,method,arm,flush=True)
 write(ROOT/'CAP1_RESULTS.json',dict(results=results,unmaterialized_terminal_suffix_preserved=True))

@meter('k3-probes')
def branches():
 # k1 cannot have a second-proposal rejection. Exercise the same transaction
 # loop separately at k3; these requests never enter the k1 economic panel.
 r=read(ROOT/'EXPOSED_INPUTS.json')['inputs'][0];results=[]
 for method in ('S','L'):
  key='protocol-k3-'+method;h=ROOT/'runs'/(key+'-heavy');o=ROOT/'runs'/(key+'-off')
  for folder,request,heavy in [(h,dict(r,heavy_state=True),True),(o,dict(r,audit_final=True),False)]:
   if not (folder/'MODULE_AUDIT.json').exists():execute(folder.name,'H1',[r,request],heavy=heavy,build=build_for('parallel','H1',0),environment=env_for('parallel',method),draft_k=3)
  ensure_references(r,h);q=qualify(r,'H1',h,o)
  a=read(h/'1.json');corrections=[c for c in a['commits'] if c['relationship']=='correct']
  later=sum(c['logits_index']>0 for c in corrections)
  assert corrections and later,'Declared later-rejection protocol coverage missing'
  z=dict(method=method,k=3,separate_protocol_only=True,natural_k1_claim=False,first_rejections=sum(c['logits_index']==0 for c in corrections),later_rejections=later,qualification=q)
  write(h/'BRANCH_COVERAGE.json',z);results.append(z);print('K3_PROTOCOL_PASS',method,later,flush=True)
 write(ROOT/'K3_PROTOCOL_RESULTS.json',dict(results=results,performance_comparison=False))

if __name__=='__main__':{'build':build,'known':known,'caps':caps,'branches':branches}[sys.argv[1]]()
