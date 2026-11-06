"""Fixed exposed-root native experiments. No output screening or selective repeats."""
from evidence_host import *
from smol_stream import StateStream

def frozen_manifest(arm):
 out=ROOT/'bindings'/(arm+'-FILES.json')
 if out.exists():return out
 original=OLD_CAMPAIGN/arm/'FILES.json';freeze=read(OLD_CAMPAIGN/'FREEZE.json')
 assert sha(original)==freeze['binary_manifest_sha256'][arm]
 files=[]
 for x in read(original)['files']:
  p=old_path(x['path']);assert sha(p)==x['sha256'] and p.stat().st_size==x['bytes'];files.append(dict(x,path=str(p)))
 write(out,dict(files=files,source_manifest_sha256=sha(original)));return out

def execute(name,arm,requests,mode=0,heavy=False,frozen=False,build=None,forced=False,environment=None,draft_k=1):
 bind();folder=ROOT/'runs'/name;folder.mkdir(parents=True)
 jobs=[dict(request_id=name+'-'+str(j),prompt_ids=r['prompt_ids'],output=str(folder/(str(j)+'.json')),**{k:r[k] for k in ('heavy_state','audit_final','forced_suffix','state_prefixes','cap','known_suffix','prelude','width','rollback','after_rollback') if k in r}) for j,r in enumerate(requests)]
 inp=folder/'REQUESTS.jsonl'
 with inp.open('x') as f:
  for x in jobs:f.write(json.dumps(x)+'\n')
 write(folder/'JOBS.json',jobs)
 env=dict(HS_PREFILL_OUTPUT=jobs[0]['output'],HS_PREFILL_UB='128')
 if not heavy:env['HS_TRACE_OFF']='1'
 if arm=='M':env.update(HS_NO_TRANSFER='1',HS_SMOL_DRAFT_PATH=read(ROOT/'HOST_BINDINGS.json')['models'][1]['path'])
 if environment:env.update(environment)
 envfile=folder/'ENV.json';write(envfile,env)
 template='old-R-0' if arm=='M' else 'old-N-k1-0'
 argv=list(read(OSMOL/'units'/template/'SUPERVISOR.json')['argv'])
 assert draft_k in (1,3)
 if draft_k!=1:
  assert arm!='M';at=argv.index('--spec-draft-n-max');argv[at+1]=str(draft_k)
 d=OLD_CAMPAIGN/arm if frozen else Path(build) if build else ROOT/'a1-build'/f'{arm}-mode{mode}'
 argv[0]=str(d/'build/Release'/('b570-closeout-target.exe' if arm=='M' else 'b570-closeout-native.exe'))
 manifest=frozen_manifest(arm) if frozen else d/'FILES.json'
 if forced:
  assert arm=='M' and heavy
  manifest=ROOT/'bindings/forced-FILES.json'
  if not manifest.exists():
   original=OSMOL/'forced-reference02/FILES.json';files=[]
   freeze=read(OLD_CAMPAIGN/'FREEZE.json');assert sha(original)==freeze['forced_reference_manifest_sha256']
   for x in read(original)['files']:
    p=old_path(x['path']);assert sha(p)==x['sha256'];files.append(dict(x,path=str(p)))
   write(manifest,dict(files=files,source_manifest_sha256=sha(original)))
  argv[0]=str(OSMOL/'forced-reference02/build/Release/b570-closeout-target.exe')
 cost=dict(requests=len(jobs),token_rows=sum(len(x['prompt_ids'])+len(x['forced_suffix']) if forced else len(x['prompt_ids'])+128 if arm=='M' else 2*len(x['prompt_ids'])+256*(draft_k+1) for x in jobs),operators=0)
 stream=StateStream(folder,pack) if any(x.get('heavy_state') or x.get('audit_final') or x.get('state_prefixes') for x in jobs) else None
 unit,rc=supervised(name,manifest,argv,cost,inp,envfile,stream)
 assert rc==0,(name,rc)
 s=read(unit/'SUPERVISOR.json');assert s['status']=='complete'
 loaded={Path(x['path']).name.lower():x['sha256'] for x in s['loaded_module_hashes']}
 expected={Path(x['path']).name.lower():x['sha256'] for x in read(manifest)['files'] if x['path'].lower().endswith('.dll')}
 required={'llama.dll','llama-common.dll','ggml.dll','ggml-base.dll','ggml-cpu.dll','ggml-vulkan.dll'}
 assert required<=loaded.keys() and all(loaded[k]==v for k,v in expected.items() if k in loaded)
 write(folder/'MODULE_AUDIT.json',dict(all_observed_match=True,observed_packaged={k:loaded[k] for k in expected if k in loaded}))
 for x in jobs:assert Path(x['output']).exists()
 return folder

def ensure_references(row,capture):
 a=read(capture/'1.json');_,ref=bank(row['group'],row['index']);wanted={tuple(x['prefix']) for x in a['committed_states'] if tuple(x['prefix']) not in ref or 'sequence' not in ref[tuple(x['prefix'])]}
 vectors={tuple(x['prefix']) for x in a['full_target_vectors'] if tuple(x['prefix']) not in ref};need=wanted|vectors
 if not need:return
 maximum=[]
 for p in sorted(need,key=lambda p:(-len(p),p)):
  if not any(q[:len(p)]==p for q in maximum):maximum.append(p)
 covered=set();jobs=[]
 for p in maximum:
  states=sorted(s for s in wanted-covered if p[:len(s)]==s);covered.update(states)
  jobs.append(dict(prompt_ids=row['prompt_ids'],forced_suffix=list(p[len(row['prompt_ids']):]),state_prefixes=[list(s) for s in states]))
 assert covered==wanted
 key=f"{row['group']}-{row['index']}";dest=ROOT/'reference'/key;dest.mkdir(parents=True,exist_ok=True)
 attempt=len(list(dest.glob('PLAN-*.json')))
 plan=dest/f'PLAN-{attempt}.json';write(plan,dict(jobs=jobs,candidate_values_received=False,producer_ub=128,producer_outer_batch=512,source_capture_sha256=sha(capture/'1.json')))
 completed=[]
 for j,r in enumerate(jobs):
  folder=execute(f'forced-{key}-{attempt}-{j}','M',[r],heavy=True,forced=True);completed.append(str(folder/'0.json'))
 write(dest/f'COMPLETE-{attempt}.json',dict(plan_sha256=sha(plan),captures=completed))

def a1_qualification():
 for i,r in enumerate(read(ROOT/'EXPOSED_INPUTS.json')['inputs']):
  for arm in ('M','H1','C4U4'):
   key=f'a1-qual-r{i}-{arm}'
   old=ROOT/'runs'/(key+'-frozen')
   if not (old/'MODULE_AUDIT.json').exists():execute(key+'-frozen',arm,[r,dict(r,audit_final=True)],frozen=True)
   for mode in (0,1,2):
    h=ROOT/'runs'/(key+f'-m{mode}-heavy');o=ROOT/'runs'/(key+f'-m{mode}-off')
    if (h/'QUALIFICATION.json').exists():
     z=read(h/'QUALIFICATION.json');assert z['conditional_vectors']==z['equal_vectors'] and z['committed_states']==z['equal_states'] and z['heavy_off_final_equal'];continue
    if not (h/'MODULE_AUDIT.json').exists():execute(h.name,arm,[r,dict(r,heavy_state=True)],mode=mode,heavy=True)
    if not (o/'MODULE_AUDIT.json').exists():execute(o.name,arm,[r,dict(r,audit_final=True)],mode=mode)
    z=qualify(r,arm,h,o,old);print('A1_QUALIFIED',i,arm,mode,z['conditional_vectors'],z['committed_states'],flush=True)
 write(ROOT/'A1_QUALIFIED.json',dict(status='ALL_MODES_COMPLETE_CONTRACT_PASS',roots=4,arms=['M','H1','C4U4'],modes=[0,1,2],original_R_unchanged=True))

def a1_timing():
 assert (ROOT/'A1_QUALIFIED.json').exists()
 schedule=[]
 rows=read(ROOT/'EXPOSED_INPUTS.json')['inputs']
 for block in range(2):
  for i,r in enumerate(rows):
   for ai,arm in enumerate(('M','H1','C4U4')):
    for mode in ((0,1) if (block+i+ai)%2==0 else (1,0)):
     schedule.append(dict(name=f'a1-time-b{block}-r{i}-{arm}-m{mode}',root=i,arm=arm,mode=mode))
 for i in (0,2):
  for arm in ('M','H1','C4U4'):schedule.append(dict(name=f'a1-sync-r{i}-{arm}-m2',root=i,arm=arm,mode=2))
 p=ROOT/'A1_SCHEDULE.json'
 if not p.exists():write(p,dict(measurements=54,warmups=54,schedule=schedule))
 assert read(p)['schedule']==schedule
 for x in schedule:
  if (ROOT/'runs'/x['name']/'MODULE_AUDIT.json').exists():continue
  r=rows[x['root']];execute(x['name'],x['arm'],[r,r],mode=x['mode']);print('A1_TIMED',x['name'],flush=True)
 write(ROOT/'A1_TIMING_COMPLETE.json',dict(measurements=54,warmups=54,all_inputs_retained=True))

if __name__=='__main__':
 {'qualify':a1_qualification,'timing':a1_timing}[sys.argv[1]]()
