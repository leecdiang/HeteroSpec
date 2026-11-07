"""Independent CPU parser: never imports executor endpoint/comparison functions."""
import json,hashlib,statistics,math,csv,sys,random,re
from pathlib import Path
ROOT=Path(sys.argv[1] if len(sys.argv)>1 else Path(__file__).parent)
ALLOW_PARTIAL='--allow-partial' in sys.argv
if str(ROOT)=='--allow-partial':ROOT=Path(__file__).parent
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
eogs=set(load(ROOT/'TOKENIZATION_PROOF.json')['runtime_eog_ids'])
checks=0;errors=[];records=[];seen=set();incomplete={};historical_differences=[]
def require(x,msg):
 global checks;checks+=1
 if not x:errors.append(msg)
require(sha(ROOT/'TOKENIZATION.stdout.jsonl')==load(ROOT/'TOKENIZATION_PROOF.json')['stdout_sha256'],'tokenization stdout binding')
if (ROOT/'DEVICE_RECOVERY_AMENDMENT.json').exists():
 for item in load(ROOT/'DEVICE_RECOVERY_AMENDMENT.json')['rejected']:
  unit=item['unit_id'];folder=ROOT/'raw'/hashlib.sha256(unit.encode()).hexdigest()[:20]
  rejected=folder/'RESULT.INFRA_REJECTED.json';require(sha(rejected)==item['result_sha256'],'rejected result preserved '+unit)
  original=load(rejected)
  for name,h in original['files'].items():require(sha(ROOT/name)==h,'rejected payload preserved '+name)
  require('using device Vulkan0 (Intel(R) UHD Graphics 730)' in (ROOT/'sessions'/item['session']/'stderr.log').read_text(encoding='utf-8',errors='replace'),'actual rejected platform '+unit)
for path in (ROOT/'raw').glob('*/RESULT.json'):
 r=load(path);key=r['unit_id'];require(key not in seen,'duplicate '+key);seen.add(key)
 captures=[ROOT/p for p in r['files'] if p.endswith('/capture.json')];require(len(captures)==1,'capture count '+key)
 for p,h in r['files'].items():require(sha(ROOT/p)==h,'file hash '+p)
 metric_files=[ROOT/f for f in r['files'] if f.endswith('/capture.json.metrics.json')]
 if metric_files:require(len(metric_files)==1 and load(metric_files[0])==r['metrics'],'recorded metrics versus authentic file '+key)
 if r.get('CPU_payload_recovered'):
  receipt=load(ROOT/r.get('CPU_payload_recovery_receipt','CPU_PAYLOAD_RECOVERY.json'))
  require(key==receipt['unit_id'] and sha(path)==receipt['result_sha256'],'CPU recovery result binding '+key)
  output=(ROOT/'sessions'/r['session']/'stdout.log').read_text(encoding='utf-8')
  original_metrics=[json.loads(line[len('HS_RESULT '):]) for line in output.splitlines() if line.startswith('HS_RESULT ')]
  require(any(m==r['metrics'] for m in original_metrics),'CPU recovery authentic stdout metrics '+key)
  require(r['host_seconds']>=r['metrics']['whole_request_ms']/1000 and 'Upper bound' in r['host_seconds_reconstruction'],'CPU recovery explicit host upper bound '+key)
 if len(captures)!=1:continue
 raw=load(captures[0]);ids=raw['ids'];flags=raw['eog'];cap=r['config'].get('cap',128)
 require(len(ids)==len(flags)>0,'raw lengths '+key)
 require(all(type(i)==int and 0<=i<151936 for i in ids),'token range '+key)
 require(flags==[i in eogs for i in ids],'runtime EOG '+key)
 stop=next((i+1 for i,t in enumerate(ids) if t in eogs),len(ids));n=min(cap,stop)
 endpoint={'ids':ids[:n],'eog':flags[:n],'reason':'EOG' if ids[n-1] in eogs else 'CAP','raw_suffix':len(ids)-n}
 require(endpoint==r['endpoint'],'endpoint independent '+key)
 require(endpoint['reason']=='EOG' or n==cap,'incomplete output '+key)
 require(len(ids)<=cap+(r['config'].get('k',2) if r['config']['native'] else 0),'unbounded native suffix '+key)
 metrics=load(str(captures[0])+'.metrics.json');require(metrics==r['metrics'],'metrics '+key)
 require(metrics['raw_count']==len(ids),'raw count '+key)
 require(metrics['request_id']==key,'response identity '+key)
 require(metrics['generation_ms']>0 and metrics['whole_request_ms']>=metrics['generation_ms'],'timer nesting '+key)
 require(metrics['reset_target']['max']==metrics['reset_target']['min']==-1,'target reset '+key)
 require(metrics['threads']==10 and metrics['batch_threads']==10,'actual threads '+key)
 require(metrics['target_continuation_ub']==r['config']['ub'],'actual target continuation capacity '+key)
 if r['config']['native']:
  require(metrics['reset_draft']['max']==metrics['reset_draft']['min']==-1,'draft reset '+key)
  require(metrics['draft_continuation_ub']==1,'draft UB '+key)
 t=raw['transfer']
 should_transfer=r['config']['native'] and not r['config'].get('plain',False) or r['config'].get('matched',False) and not r['config'].get('plain',False)
 require(bool(t)==bool(should_transfer),'transfer gate '+key)
 if t:
  require(t['source_ub']==r['config']['prefill'] and t['destination_ub']==r['config']['ub'],'actual target phase UB '+key)
  require(t['kv_equal'] and t['source_unchanged'] and t['state_bytes']==t['consumed_bytes'],'state roundtrip '+key)
  require(t['before']==t['after']==t['source_after'],'state positions '+key)
  require(t['pending_id']==ids[0],'pending committed first '+key)
  require(t['sampler_chain']==t['clone_chain'] and t['sampler_history']==t['clone_history'] and t['seed']==t['clone_seed']==123,'sampler metadata '+key)
  if r['config'].get('capture',False):
   hashes=[sha(str(captures[0])+s) for s in ['.before.kv','.restored.kv','.source_after.kv']]
   require(len(set(hashes))==1,'KV byte proof '+key)
 if r['config'].get('capture',False):
  d=[x for x in raw['trace'] if x['event']=='decode'];require(bool(d),'actual decodes '+key)
  for call in d:
   role=call['role'];phase=call['phase'];want=1 if role=='draft' else r['config']['prefill'] if phase=='prefill' else r['config']['ub']
   require(call['ub_capacity']==want,'role phase actual UB '+key)
   require(call['exit_code']==0,'decode code '+key)
   require(len(call['input_ids'])==len(call['positions'])==len(call['sequence_ids'])==len(call['logits_requested'])==call['caller_batch_length'],'caller shape '+key)
   require(all(s==[0] for s in call['sequence_ids']),'single actual sequence '+key)
   for graph in call['graphs']:
    # A prefill microbatch may update KV without producing a requested logit row.
    lower=0 if graph['tensor']=='result_output' else 1
    require(lower<=graph['ne1']<=want,'actual graph capacity '+key)
 require(len(raw['prompt_ids'])+cap+12<=1024,'no truncation/context bound '+key)
 records.append(r)
def same(a,b):return a['ids']==b['ids'] and a['eog']==b['eog'] and a['reason']==b['reason']
for schedule_path in sorted(ROOT.glob('G0*_SCHEDULE.json')):
 stage_name=schedule_path.name[:-len('_SCHEDULE.json')];schedule=load(schedule_path)
 expected={f'{stage_name}/{si}/{ri}/{inp["id"]}':(spec['config'],inp) for si,spec in enumerate(schedule) for ri,inp in enumerate(spec['inputs'])}
 actual={r['unit_id']:r for r in records if not r['warm'] and r['unit_id'].startswith(stage_name+'/')}
 if set(actual)!=set(expected):incomplete[stage_name]={'planned':len(expected),'completed':len(actual)}
 require(set(actual)==set(expected) or ALLOW_PARTIAL and set(actual)<=set(expected),'independent old-control denominator '+stage_name)
 for key,r in actual.items():
  if key not in expected:continue
  config,inp=expected[key];require(r['config']==config and r['task']==inp['id'],'frozen old-control config '+key)
  raw=load(next(ROOT/p for p in r['files'] if p.endswith('/capture.json')));require(raw['prompt_ids']==inp['prompt_ids'],'frozen old-control prompt '+key)
for name in sorted({r['session'] for r in records if not r['unit_id'].startswith(('G0/','G0_BRIDGE/'))}):
 folder=ROOT/'sessions'/name;session=load(folder/'SESSION.json');log=(folder/'stderr.log').read_text(encoding='utf-8',errors='replace');cmd=session['command']
 require(cmd[cmd.index('--device')+1].startswith('Vulkan') and cmd[cmd.index('--n-gpu-layers')+1]=='all','requested target GPU '+name)
 require(('using device '+cmd[cmd.index('--device')+1]+' (Intel(R) Arc(TM) B570 Graphics)') in log,'observed target B570 device '+name)
 offload=re.findall(r'offloaded (\d+)/(\d+) layers to GPU',log)
 require(len(offload)==(2 if session['config']['native'] else 1) and all(int(a)==int(b)>0 for a,b in offload),'actual complete layer offload '+name)
 require(all(d==cmd[cmd.index('--device')+1] for d in re.findall(r'(Vulkan\d+) model buffer',log)),'no other GPU model buffer '+name)
 if session['config']['native']:require(cmd[cmd.index('--spec-draft-device')+1]==cmd[cmd.index('--device')+1],'requested draft GPU '+name)
historical=ROOT/'dependencies/B570/HISTORICAL_EXPECTED.json'
if historical.exists():
 h=load(historical)
 for r in records:
  name=r['unit_id'].split('/')[0]
  if r['warm'] or name not in ['G0','G0_BRIDGE','G0_REBUILT','G0_TARGET_FINAL','G0_ETA_N0','G0_DEVICE_REQUALIFICATION','G0_CONTINUATION_QUAL']:continue
  if name=='G0_TARGET_FINAL' and (r['config']['prefill']==1 or r['config']['label']=='T_FINAL_WIDTH'):continue
  if name=='G0':cond=['R','N0','R'][int(r['unit_id'].split('/')[1])%3]
  else:cond='N0' if name=='G0_ETA_N0' else 'R'
  expected=h[r['task']+'/'+cond+'/1'];expected=dict(expected,reason='EOG' if expected['endpoint']=='EOG' else 'CAP')
  if not same(r['endpoint'],expected):historical_differences.append(r['unit_id'])
 if (ROOT/'G0.json').exists() and load(ROOT/'G0.json')['status']=='PASS':require(not historical_differences,'independent historical reference fidelity')
finaltarget=ROOT/'G0_TARGET_FINAL.json'
if finaltarget.exists():
 schedule=load(ROOT/'G0_TARGET_FINAL_SCHEDULE.json')
 expected_units={f'G0_TARGET_FINAL/{si}/{ri}/{inp["id"]}' for si,spec in enumerate(schedule) for ri,inp in enumerate(spec['inputs'])}
 require({r['unit_id'] for r in records if not r['warm'] and r['unit_id'].startswith('G0_TARGET_FINAL/')}==expected_units,'final target complete frozen denominator')
 require(load(finaltarget)['status']=='PASS','final target reference gate')
 for task in ['HumanEval/134','HumanEval/42','HumanEval/145','HumanEval/138','HumanEval/58']:
  pair=[r for r in records if not r['warm'] and r['task']==task and r['unit_id'].startswith('G0_TARGET_FINAL/') and r['config']['label'] in ['T_FINAL_PLAIN','T_FINAL_SHAM']]
  require(len(pair)==2,'final target sham pair '+task)
  if len(pair)==2:
   captures=[load(next(ROOT/f for f in r['files'] if f.endswith('/capture.json'))) for r in pair]
   require(same(pair[0]['endpoint'],pair[1]['endpoint']) and captures[0]['trace']==captures[1]['trace'] and captures[0]['commits']==captures[1]['commits'],'independent final target sham equivalence '+task)
summaries={};costs=[]
if (ROOT/'INPUTS.json').exists():
 inputs=load(ROOT/'INPUTS.json');byid={r['id']:r for group in inputs.values() for r in group}
 for r in records:
  if r['unit_id'].startswith('G0'):continue
  raw=load(next(ROOT/p for p in r['files'] if p.endswith('/capture.json')))
  require(raw['prompt_ids']==byid[r['task']]['prompt_ids'],'frozen input identity '+r['unit_id'])
 for stage in ['B','C','C_ANCHOR_LONG','D_RESET','D_TIMING','E_CAPTURE','E_PILOT','E_CONFIRM','E_LONG','E_D_RESET','E_D_TIMING','MECHANISM']:
  p=ROOT/(stage+'_SCHEDULE.json')
  if not p.exists():continue
  sched=load(p);rows=[r for r in records if r['unit_id'].startswith(stage+'/') and not r['warm']]
  planned=sum(len(s['inputs']) for s in sched)
  if len(rows)!=planned:incomplete[stage]={'planned':planned,'completed':len(rows),'unexecuted':planned-len(rows)}
  require(len(rows)==planned or ALLOW_PARTIAL and len(rows)<planned,'planned denominator '+stage)
  expected={f'{stage}/{si}/{ri}/{inp["id"]}' for si,s in enumerate(sched) for ri,inp in enumerate(s['inputs'])}
  actual={r['unit_id'] for r in rows};require(actual==expected or ALLOW_PARTIAL and actual<=expected,'unique planned units '+stage)
  expected_configs={f'{stage}/{si}/{ri}/{inp["id"]}':s['config'] for si,s in enumerate(sched) for ri,inp in enumerate(s['inputs'])}
  for row in rows:require(row['unit_id'] in expected_configs and row['config']==expected_configs[row['unit_id']],'formal configuration versus deterministic schedule '+row['unit_id'])
  require(all(r['source_commit'] in (load(ROOT/('CONTINUATION_FREEZE.json' if (ROOT/'CONTINUATION_FREEZE.json').exists() else 'DEVICE_RECOVERY_FREEZE.json'))['allowed_inference_commits'] if (ROOT/'DEVICE_RECOVERY_FREEZE.json').exists() else [rows[0]['source_commit']]) for r in rows) if rows else ALLOW_PARTIAL,'frozen source epochs '+stage)
  groups={}
  for r in rows:
   c=r['config'];cohort=byid[r['task']]['cohort']
   if stage.startswith('E') and cohort=='project_unused_within_accessible_audit':cohort='B_unused_previously_executed_before_E'
   key=(cohort,c.get('width_k',0),c.get('width_ub',0),c.get('cap',128))
   groups.setdefault(key,[]).append(r)
  details=[]
  for group,rr in groups.items():
   labels=sorted({r['config']['label'] for r in rr});tasks=sorted({r['task'] for r in rr});qualified={label:True for label in labels};failed_units=[]
   for task in tasks:
    references=[r for r in rr if r['task']==task and r['config']['label']=='R_reference']
    if not references:references=[r for r in records if r['task']==task and r['unit_id'].startswith('B/') and not r['warm'] and r['config']['label']=='R_reference']
    if not references:references=[r for r in records if r['task']==task and r['unit_id'].startswith('G0/') and not r['warm'] and not r['config']['native']]
    require(bool(references) or ALLOW_PARTIAL and stage in incomplete,'paid reference '+stage+'/'+task)
    if not references:continue
    stable=all(same(r['endpoint'],references[0]['endpoint']) for r in references)
    # Reference instability is a retained scientific qualification failure, not malformed evidence.
    for label in labels:
     observed=[r for r in rr if r['task']==task and r['config']['label']==label]
     failed_units.extend(r['unit_id'] for r in observed if not stable or not same(r['endpoint'],references[0]['endpoint']))
     qualified[label]&=bool(observed) and stable and all(same(r['endpoint'],references[0]['endpoint']) for r in observed) and stage not in incomplete
   details.append({'cohort':group[0],'k_label':group[1],'ub_label':group[2],'cap':group[3],'tasks':len(tasks),'requests':len(rr),'qualification':qualified,'scientific_failed_requests':len(failed_units),'scientific_failed_unit_ids':failed_units})
   for baseline,candidate in [('T_matched','N1_repaired'),('R_reference','N1_repaired'),('N0_ordinary','N1_repaired'),('R_reference','N0_ordinary'),('T_matched','N_candidate'),('R_reference','N_candidate'),('N1_repaired','E_candidate'),('E_matched','E_candidate'),('E_ordinary','E_candidate')]:
    if baseline not in labels or candidate not in labels:continue
    ratios={};absolute=[]
    for task in tasks:
     aa=[r for r in rr if r['task']==task and r['config']['label']==baseline];bb=[r for r in rr if r['task']==task and r['config']['label']==candidate]
     if not aa or not bb:continue
     ratios[task]={}
     for field in ['generation_ms','whole_request_ms']:
      a=statistics.median(r['metrics'][field] for r in aa);b=statistics.median(r['metrics'][field] for r in bb);ratios[task][field]=a/b
      absolute.append({'stage':stage,'cohort':group[0],'task':task,'k':group[1],'ub':group[2],'cap':group[3],'baseline':baseline,'candidate':candidate,'timer':field,'baseline_median_ms':a,'candidate_median_ms':b,'speed_ratio':a/b})
    if not ratios:continue
    cost={'stage':stage,'cohort':group[0],'k':group[1],'ub':group[2],'cap':group[3],'baseline':baseline,'candidate':candidate,'qualified':qualified[baseline] and qualified[candidate],'task_ratios':ratios}
    for field in ['generation_ms','whole_request_ms']:cost[field]=math.exp(statistics.mean(math.log(x[field]) for x in ratios.values()))
    cost['round_directions']=[]
    roundkey='cycle' if any('cycle' in r['config'] for r in rr) else 'repetition'
    for index in sorted({r['config'].get(roundkey,1) for r in rr}):
     a={r['task']:r for r in rr if r['config']['label']==baseline and r['config'].get(roundkey,1)==index};b={r['task']:r for r in rr if r['config']['label']==candidate and r['config'].get(roundkey,1)==index}
     common=sorted(set(a)&set(b))
     if common:cost['round_directions'].append({'round':index,**{f:math.exp(statistics.mean(math.log(a[t]['metrics'][f]/b[t]['metrics'][f]) for t in common)) for f in ['generation_ms','whole_request_ms']}})
    seed=random.Random(123);logs=[(math.log(x['generation_ms']),math.log(x['whole_request_ms'])) for x in ratios.values()];boot=[[],[]]
    for _ in range(4000):
     draw=[seed.randrange(len(logs)) for _ in logs]
     for j in [0,1]:boot[j].append(math.exp(statistics.mean(logs[i][j] for i in draw)))
    cost['descriptive_task_resampling']={'seed':123,'draws':4000,'scope':'finite panel and conditional on selection where applicable; not population/platform-transfer confidence','generation_ms_interval':[sorted(boot[0])[100],sorted(boot[0])[3899]],'whole_request_ms_interval':[sorted(boot[1])[100],sorted(boot[1])[3899]]}
    costs.append(cost)
    output=ROOT/'derived';output.mkdir(exist_ok=True)
    with (output/(stage+'-'+group[0]+'-'+baseline+'-'+candidate+'-'+str(group[1])+'-'+str(group[3])+'.csv')).open('w',newline='',encoding='utf-8-sig') as f:
     w=csv.DictWriter(f,fieldnames=list(absolute[0]));w.writeheader();w.writerows(absolute)
  summaries[stage]={'planned':planned,'completed':len(rows),'groups':details,'warmups':sum(r['warm'] for r in records if r['unit_id'].startswith(stage+'/'))}
 # Recompute controller gates independently instead of trusting printed PASS.
 for stage,filename in [('B','B_SUMMARY.json')]:
  if stage not in summaries or not (ROOT/filename).exists():continue
  controller=load(ROOT/filename)
  for group in summaries[stage]['groups']:
   scope='shared' if group['cohort']=='cross_platform_shared_project_exposed' else 'unused'
   expected=controller[scope]['qualification']
   require(group['qualification']==expected,'controller qualification equality '+stage+'/'+scope+'/'+str(group['cap']))
 if 'C_ANCHOR_LONG' in summaries and (ROOT/'C_ANCHOR_SUMMARY.json').exists():
  controller=load(ROOT/'C_ANCHOR_SUMMARY.json')
  for cap in [256,512]:
   groups=[g for g in summaries['C_ANCHOR_LONG']['groups'] if g['cap']==cap]
   labels=set(label for g in groups for label in g['qualification'])
   aggregate={label:all(g['qualification'].get(label,False) for g in groups) for label in labels}
   require(aggregate==controller[str(cap)]['qualification'],'controller anchor joint-cohort equality '+str(cap))
 if 'C' in summaries and (ROOT/'C_SUMMARY.json').exists():
  controller=load(ROOT/'C_SUMMARY.json')
  for group in summaries['C']['groups']:
   item=next(i for i in controller if i['k']==group['k_label'] and i['cap']==group['cap'])
   scope='shared' if group['cohort']=='cross_platform_shared_project_exposed' else 'long'
   require(group['qualification']==item[scope]['qualification'],'controller C gate equality '+str(group))
  rr=[r for r in records if r['unit_id'].startswith('C/') and not r['warm'] and r['config']['label']=='R_reference']
  for task,cap in {(r['task'],r['config']['cap']) for r in rr}:
   refs=[r for r in rr if r['task']==task and r['config']['cap']==cap]
   require(all(same(r['endpoint'],refs[0]['endpoint']) for r in refs),'R cross-width stability '+task+'/'+str(cap))
 if (ROOT/'EXECUTION_FREEZE.json').exists():
  frozen=load(ROOT/'EXECUTION_FREEZE.json')
  if (ROOT/'CONTINUATION_FREEZE.json').exists():
   continuation=load(ROOT/'CONTINUATION_FREEZE.json')
   require(sha(ROOT/'efficiency.py')==continuation['efficiency_source_sha256'],'frozen efficiency controller source')
   require(continuation['inputs_sha256']==frozen['inputs_sha256'] and continuation['protocol_sha256']==frozen['protocol_sha256'],'continuation retains original frozen input/protocol bindings')
  require(sha(ROOT/'INPUTS.json')==frozen['inputs_sha256'],'frozen input bytes')
  require(sha(ROOT/'PROTOCOL.json')==frozen['protocol_sha256'],'frozen protocol bytes')
  for name,h in load(ROOT/'PROTOCOL.json')['sources'].items():
   f=load(ROOT/('CONTINUATION_FREEZE.json' if (ROOT/'CONTINUATION_FREEZE.json').exists() else 'DEVICE_RECOVERY_FREEZE.json')) if (ROOT/'DEVICE_RECOVERY_FREEZE.json').exists() else None
   require(sha(ROOT/name)==(f['current_sources'][name] if f else h),'frozen numerical/controller source '+name)
   if f and name in ['runner.py','campaign.py']:require(sha(ROOT/('engineering-device-enumeration-v1' if name=='runner.py' else 'engineering-continuation-v1')/name)==h,'original executor snapshot binding')
  for stage in ['B','C','C_ANCHOR_LONG','D_RESET','D_TIMING','E_CAPTURE','E_PILOT','E_CONFIRM','E_LONG','E_D_RESET','E_D_TIMING','MECHANISM']:
   require(all(r['source_commit'] in (load(ROOT/('CONTINUATION_FREEZE.json' if (ROOT/'CONTINUATION_FREEZE.json').exists() else 'DEVICE_RECOVERY_FREEZE.json'))['allowed_inference_commits'] if (ROOT/'DEVICE_RECOVERY_FREEZE.json').exists() else [frozen['source_commit']]) for r in records if r['unit_id'].startswith(stage+'/')),'formal source freeze '+stage)
 for stage in ['D_RESET','D_TIMING','E_D_RESET','E_D_TIMING']:
  filename=ROOT/(stage+'_SUMMARY.json')
  if stage not in summaries or not filename.exists():continue
  controller=load(filename);groups=summaries[stage]['groups']
  failed=sorted({u for g in groups for u in g['scientific_failed_unit_ids']})
  require(sorted(controller.get('failures',controller.get('failed',[])))==failed,'independent resident failed-unit list '+stage)
  require(controller['status']==('COMPLETED_SCIENTIFIC_FAIL' if failed else 'COMPLETED_PASS'),'independent resident status '+stage)
  if 'requests' in controller:require(controller['requests']==summaries[stage]['completed'],'independent resident count '+stage)
 if (ROOT/'E_PLAN.json').exists() and 'C' in summaries:
  eplan=load(ROOT/'E_PLAN.json');qualified_ubs=[]
  for kval,uval in [(1,2),(3,4),(5,6),(7,8)]:
   groups=[g for g in summaries['C']['groups'] if g['k_label']==kval]
   if len(groups)==6 and all(all(g['qualification'].get(label,False) for label in ['T_matched','N_candidate']) for g in groups):qualified_ubs.append(uval)
  independently_selected_ub=min(qualified_ubs) if qualified_ubs else 1
  require(eplan['selected_fixed_ub']==independently_selected_ub,'independent smallest qualified E UB')
  expected_pairs=sorted(set([(k,independently_selected_ub) for k in [1,2,3,5,7]]+[(2,1)]))
  require([(c['k'],c['ub']) for c in eplan['configs']]==expected_pairs,'independent fixed E configuration set and order')
  require(eplan['tasks']==[t['id'] for t in inputs['shared'][:8]+inputs['pilot_old']],'independent fixed E pilot input set and order')
  require(eplan['pilot_requests']==len(expected_pairs)*24 and eplan['capture_requests']==len(expected_pairs),'independent E planned denominators')
 if (ROOT/'E_PILOT_SUMMARY.json').exists():
  observations=load(ROOT/'E_PILOT_SUMMARY.json')['observations'];pilot=[r for r in records if r['unit_id'].startswith('E_PILOT/') and not r['warm']]
  base=[r for r in pilot if r['config']['label']=='N1_repaired']
  for item in observations:
   label=item['config']['label'];candidate=[r for r in pilot if r['config']['label']==label];tasks=sorted({r['task'] for r in candidate})
   ratios={t:{f:statistics.median(r['metrics'][f] for r in base if r['task']==t)/statistics.median(r['metrics'][f] for r in candidate if r['task']==t) for f in ['generation_ms','whole_request_ms']} for t in tasks}
   speed={f:math.exp(statistics.mean(math.log(x[f]) for x in ratios.values())) for f in ['generation_ms','whole_request_ms']}
   qualified=True
   for r in candidate:
    ref=[q for q in records if q['task']==r['task'] and not q['warm'] and (q['unit_id'].startswith('B/') and q['config']['label']=='R_reference' or q['unit_id'].startswith('G0/') and not q['config']['native'])]
    require(bool(ref),'pilot independently paid reference '+r['task']);qualified&=bool(ref) and same(r['endpoint'],ref[0]['endpoint'])
   directions=[]
   for rep in [1,2]:
    a={r['task']:r for r in base if r['config']['repetition']==rep};b={r['task']:r for r in candidate if r['config']['repetition']==rep}
    directions.append(math.exp(statistics.mean(math.log(a[t]['metrics']['generation_ms']/b[t]['metrics']['generation_ms']) for t in tasks)))
   eligible=qualified and label!='N1_repaired' and speed['generation_ms']>=1.03 and speed['whole_request_ms']>=1 and all(x>1 for x in directions)
   require(qualified==item['qualified'] and eligible==item['eligible'],'independent E pilot eligibility '+label)
   for f,value in speed.items():require(abs(value-item['costs'][f])<1e-12,'independent pilot cost '+label+'/'+f)
   for cohort,ids in [('shared_pilot',{t['id'] for t in inputs['shared'][:8]}),('old_diagnostics',{t['id'] for t in inputs['pilot_old']})]:
    independent={}
    for field in ['generation_ms','whole_request_ms']:
     values=[]
     for task in sorted(ids):
      aa=[r['metrics'][field] for r in base if r['task']==task];bb=[r['metrics'][field] for r in candidate if r['task']==task]
      require(len(aa)==len(bb)==2,'independent pilot cohort repeats '+label+'/'+cohort+'/'+task)
      if aa and bb:values.append(statistics.median(aa)/statistics.median(bb))
     independent[field]=math.exp(statistics.mean(math.log(x) for x in values)) if values else None
     require(independent[field] is not None and abs(independent[field]-item['costs']['cohorts'][cohort][field])<1e-12,'independent pilot cohort cost '+label+'/'+cohort+'/'+field)
    for direction in item['costs']['cohorts'][cohort]['directions']:
     rep=direction['repetition']
     for field in ['generation_ms','whole_request_ms']:
      aa={r['task']:r['metrics'][field] for r in base if r['config']['repetition']==rep and r['task'] in ids};bb={r['task']:r['metrics'][field] for r in candidate if r['config']['repetition']==rep and r['task'] in ids}
      value=math.exp(statistics.mean(math.log(aa[t]/bb[t]) for t in sorted(ids)))
      require(abs(value-direction[field])<1e-12,'independent pilot cohort direction '+label+'/'+cohort+'/'+str(rep)+'/'+field)
  eligible_items=[o for o in observations if o['eligible']]
  decision=load(ROOT/'E_DECISION.json') if (ROOT/'E_DECISION.json').exists() else {}
  if not eligible_items:
   require(decision.get('status')=='NO_GO_PILOT','independent no eligible pilot decision')
  elif (ROOT/'E_SELECTION.json').exists():
   best=sorted(eligible_items,key=lambda o:(-o['costs']['generation_ms'],-o['costs']['whole_request_ms'],o['config']['k'],o['config']['ub']))[0]
   selection=load(ROOT/'E_SELECTION.json')
   require(selection['selected']==best and selection['freeze_before_confirmation'] is True,'independent pilot winner and tie breaks')
   observed=[r for r in records if not r['warm'] and r['unit_id'].split('/')[0] in ['B','C'] and r['config']['native']]
   expected_eta=(4*len(inputs['shared']+inputs['unused'])*4+16+(load(ROOT/'PROTOCOL.json')['C_shared_count']+len(inputs['long']))*12+12+192+8)*max(statistics.mean(r['host_seconds'] for r in observed),1)*1.3
   require(abs(expected_eta-selection['confirmation_ETA_seconds'])<1e-8,'independent full E confirmation budget estimate')
   if selection['remaining_seconds']<expected_eta:
    require(decision.get('status')=='CONFIGURATION_PILOT' and decision.get('selected')==best and decision.get('not_deployment_qualified') is True,'independent time gated E decision')
    require(not any(r['unit_id'].startswith(('E_CONFIRM/','E_LONG/','E_D_RESET/','E_D_TIMING/')) for r in records),'no truncated E confirmation after budget gate')
  else:require(False,'eligible E pilot has a frozen selection receipt')
 if (ROOT/'MECHANISM.json').exists():
  mechanism=load(ROOT/'MECHANISM.json')
  if mechanism['status']=='GATED_BY_QUALIFICATION':
   require('C' in summaries and summaries['C']['completed']==summaries['C']['planned'],'mechanism gate uses a complete C matrix')
   require(all(g['qualification'].get('N_candidate',False) for g in summaries.get('C',{}).get('groups',[])),'independent absence of naturally failing C candidate')
   require(mechanism['plan']['selection']==[],'empty mechanism selection matches qualified C matrix')

if (ROOT/'WORK_ACCOUNTING.json').exists():
 work_public=load(ROOT/'WORK_ACCOUNTING.json');work_rows={w['unit_id']:w for w in work_public['records']}
 require(len(work_rows)==len(records)==work_public['records_checked'],'work accounting complete unique denominator')
 for record in records:
  unit=record['unit_id'];w=work_rows.get(unit);require(w is not None,'work accounting request '+unit)
  if w is None:continue
  raw=load(next(ROOT/name for name in record['files'] if name.endswith('/capture.json')))
  for name,value in raw['work'].items():require(w[name]==value,'recorded caller work '+unit+'/'+name)
  drafted=record['metrics'].get('drafted');accepted=record['metrics'].get('accepted')
  require(w['drafted']==drafted and w['accepted']==accepted,'recorded draft work '+unit)
  require(w['accepted_over_drafted']==(accepted/drafted if drafted else None),'independent acceptance ratio '+unit)
  require(w['authentic_state_transfer_count']==int(bool(raw['transfer'])),'observed transfer count '+unit)
  for role in ['target','draft']:
   observed=sum(graph['tensor']=='embd' for call in raw['trace'] if call['event']=='decode' and call['role']==role for graph in call['graphs']) if raw['trace'] else None
   require(w['observed_'+role+'_micrographs']==observed,'observed micrographs '+unit+'/'+role)
  require(w['synchronization_count'] is None and w['synchronization_count_status'].startswith('MISSING'),'honest missing synchronization count '+unit)

out=ROOT/'INDEPENDENT_VERIFICATION.json'
result={'status':'FAIL' if errors else 'PASS_STRUCTURAL_PARTIAL' if incomplete else 'PASS','checks':checks,'complete_records':len(records),'errors':errors,'incomplete_stages':incomplete,'historical_qualification_differences':historical_differences,'stages':summaries,'costs':costs,'model_forwards':0,'limitations':['CPU reparse authenticates recorded byte identities and observed graph metadata, not independent GPU reruns','No opaque sampler byte certification or unique backend dispatch claim']}
out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
print({'status':result['status'],'checks':checks,'complete_records':len(records),'errors':errors[:12],'stages':[(k,v['completed']) for k,v in summaries.items()]})
if errors:sys.exit(2)
