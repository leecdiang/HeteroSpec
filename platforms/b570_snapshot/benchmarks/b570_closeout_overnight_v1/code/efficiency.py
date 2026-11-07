"""Finite fixed-UB/k pilot with independent confirmation and budget gates."""
import json,math,statistics,hashlib
from datetime import datetime,timezone
from pathlib import Path
from campaign import stage,cfg,R,T,N1,eq,panel,read,save
ROOT=Path(__file__).parent
def remaining():return (datetime.fromisoformat(read(ROOT/('CONTINUATION_AMENDMENT.json' if (ROOT/'CONTINUATION_AMENDMENT.json').exists() else 'RECOVERY_AMENDMENT.json'))['new_experiment_stop_utc'])-datetime.now(timezone.utc)).total_seconds()
def gm(xs):return math.exp(statistics.mean(math.log(x) for x in xs))
def rows(name):return [r for r in read(ROOT/(name+'_RESULTS.json')) if not r['warm']]
def ref(task):
 name='B' if task.startswith('MBPP/') else 'G0'
 rr=[r for r in rows(name) if r['task']==task and (r['config'].get('label')=='R_reference' if name=='B' else not r['config']['native'])]
 assert rr and all(eq(r['endpoint'],rr[0]['endpoint']) for r in rr)
 return rr[0]['endpoint']
def costs(rr,label,base='N1_repaired'):
 tasks=sorted({r['task'] for r in rr});ratios={};directions=[]
 for task in tasks:
  a=[r for r in rr if r['task']==task and r['config']['label']==base];b=[r for r in rr if r['task']==task and r['config']['label']==label]
  assert a and b
  ratios[task]={f:statistics.median(r['metrics'][f] for r in a)/statistics.median(r['metrics'][f] for r in b) for f in ['generation_ms','whole_request_ms']}
 for rep in sorted({r['config']['repetition'] for r in rr}):
  q=[r for r in rr if r['config']['repetition']==rep];a={r['task']:r for r in q if r['config']['label']==base};b={r['task']:r for r in q if r['config']['label']==label}
  directions.append({'repetition':rep,**{f:gm(a[t]['metrics'][f]/b[t]['metrics'][f] for t in tasks) for f in ['generation_ms','whole_request_ms']}})
 return {'task_ratios':ratios,**{f:gm(v[f] for v in ratios.values()) for f in ['generation_ms','whole_request_ms']},'directions':directions}
def run():
 inputs=read(ROOT/'INPUTS.json');protocol=read(ROOT/'PROTOCOL.json');c=read(ROOT/'C_SUMMARY.json');qualified=[]
 for k,ub in [(1,2),(3,4),(5,6),(7,8)]:
  q=[r for r in c if r['k']==k]
  if len(q)==3 and all(all(r[cohort]['qualification'].get(m,False) for cohort in ['shared','long'] for m in ['T_matched','N_candidate']) for r in q):qualified.append(ub)
 ub=min(qualified) if qualified else 1
 pairs=sorted(set([(k,ub) for k in [1,2,3,5,7]]+[(2,1)]))
 configs=[cfg('N1_repaired' if (k,u)==(2,1) else f'E_k{k}_ub{u}',True,k,u) for k,u in pairs]
 tasks=inputs['shared'][:8]+inputs['pilot_old']
 observed=rows('B')+rows('C');native=[r['host_seconds'] for r in observed if r['config']['native']]
 mean=statistics.mean(native);pilot_eta=(len(configs)*2*(len(tasks)+1))*max(mean,1)*1.2
 plan={'utc':datetime.now(timezone.utc).isoformat(),'selected_fixed_ub':ub,'selection_criterion':'smallest >1 UB whose own C T/native pass both cohorts at all caps/repetitions; otherwise UB1; no speed-based UB choice','configs':configs,'tasks':[t['id'] for t in tasks],'pilot_requests':len(configs)*2*len(tasks),'pilot_warmups':len(configs)*2,'capture_requests':len(configs),'capture_warmups':len(configs),'remaining_seconds':remaining(),'pilot_ETA_seconds':pilot_eta,'ordinary_control':'target prefill and continuation UB=candidate UB, no prefill repair/state transfer; draft1, same k; caller grouping stays native; not a one-switch scope ablation','prototype':'NOT_IMPLEMENTED: published Vulkan runtime ABI retained; no arithmetic/shader or kernel replacement','reference':'stable paid B ordinary R for shared; stable paid G0 ordinary R for four old diagnostics; IDs are never sent as a continuation oracle'}
 save(ROOT/'E_PLAN.json',plan)
 if remaining()<pilot_eta+900:
  save(ROOT/'E_DECISION.json',{'status':'NOT_RUN_TIME','reason':'Insufficient measured remaining budget for complete fixed pilot while preserving core archive reserve','plan':plan});return
 proof=stage('E_CAPTURE',[{'config':dict(c,capture=True,cap=128),'inputs':[inputs['pilot_old'][0]]} for c in configs])
 captures=[read(next(ROOT/f for f in r['files'] if f.endswith('/capture.json'))) for r in proof]
 query_ranges={r['config']['label']:sorted({g['ne1'] for call in raw['trace'] if call['event']=='decode' and call['role']=='target' and call['phase']=='continuation' for g in call['graphs'] if g['tensor']=='embd'}) for r,raw in zip(proof,captures)}
 save(ROOT/'E_CAPTURE_SUMMARY.json',{'requests':len(proof),'actual_target_query_widths':query_ranges,'reference_qualified':{r['config']['label']:eq(r['endpoint'],ref(r['task'])) for r in proof},'timing':'Excluded capture-on engineering costs'})
 sessions=[]
 for rep in range(2):
  for config in configs if rep==0 else configs[::-1]:sessions.append({'config':dict(config,repetition=rep+1,cap=128,capture=False),'inputs':tasks if rep==0 else tasks[::-1]})
 pilot=stage('E_PILOT',sessions);summaries=[]
 for config in configs:
  label=config['label'];obs=[r for r in pilot if r['config']['label']==label]
  passing=all(eq(r['endpoint'],ref(r['task'])) for r in obs)
  stats=costs(pilot,label)
  stats['cohorts']={name:costs([r for r in pilot if r['task'] in ids],label) for name,ids in [('shared_pilot',{t['id'] for t in inputs['shared'][:8]}),('old_diagnostics',{t['id'] for t in inputs['pilot_old']})]}
  summaries.append({'config':config,'qualified':passing,'costs':stats,'eligible':passing and label!='N1_repaired' and stats['generation_ms']>=1.03 and stats['whole_request_ms']>=1 and all(d['generation_ms']>1 for d in stats['directions'])})
 save(ROOT/'E_PILOT_SUMMARY.json',{'scope':'exploratory exposed selection panel; no prospective speed claim','observations':summaries})
 eligible=[s for s in summaries if s['eligible']]
 if not eligible:
  save(ROOT/'E_DECISION.json',{'status':'NO_GO_PILOT','reason':'No complete-reference candidate passed all preregistered generation/wall/direction thresholds; keep original anchor','pilot':summaries,'prototype':'NOT_IMPLEMENTED'});return
 selected=sorted(eligible,key=lambda s:(-s['costs']['generation_ms'],-s['costs']['whole_request_ms'],s['config']['k'],s['config']['ub']))[0]
 candidate=selected['config'];candidate=dict(candidate,label='E_candidate');matched=cfg('E_matched',k=candidate['k'],ub=candidate['ub'],matched=True)
 ordinary=cfg('E_ordinary',True,candidate['k'],candidate['ub'],prefill=candidate['ub'],plain=True)
 modes=[N1,candidate,matched,ordinary];allB=inputs['shared']+inputs['unused'];ctasks=inputs['shared'][:protocol['C_shared_count']]+inputs['long']
 confirm_eta=(4*len(allB)*4+16+len(ctasks)*12+12+192+8)*max(mean,1)*1.3
 save(ROOT/'E_SELECTION.json',{'selected':selected,'confirmation_ETA_seconds':confirm_eta,'remaining_seconds':remaining(),'freeze_before_confirmation':True})
 if remaining()<confirm_eta:
  save(ROOT/'E_DECISION.json',{'status':'CONFIGURATION_PILOT','reason':'Complete independent confirmation/long/resident estimated cost exceeds remaining window','selected':selected,'not_deployment_qualified':True});return
 sessions=[]
 for rep in range(4):
  for mode in modes[rep:]+modes[:rep]:sessions.append({'config':dict(mode,cap=128,capture=False,repetition=rep+1),'inputs':allB[rep:]+allB[:rep]})
 confirmed=stage('E_CONFIRM',sessions);passed={m['label']:all(eq(r['endpoint'],ref(r['task'])) for r in confirmed if r['config']['label']==m['label']) for m in modes}
 stats=costs(confirmed,'E_candidate');groups={name:costs([r for r in confirmed if r['task'] in ids],'E_candidate') for name,ids in [('shared_pilot',{t['id'] for t in inputs['shared'][:8]}),('shared_confirmation',{t['id'] for t in inputs['shared'][8:]}),('unused_previously_B_executed',{t['id'] for t in inputs['unused']})]}
 save(ROOT/'E_CONFIRM_SUMMARY.json',{'qualification':passed,'costs':stats,'cohorts':groups,'candidate_matched':costs(confirmed,'E_candidate','E_matched'),'ordinary_same_config':costs(confirmed,'E_candidate','E_ordinary')})
 if not passed['E_candidate'] or not passed['E_matched']:
  save(ROOT/'E_DECISION.json',{'status':'COMPLETED_SCIENTIFIC_FAIL','reason':'Independent full B candidate/matched reference qualification failed','qualification':passed});return
 longrows=stage('E_LONG',[{'config':dict(mode,cap=cap,repetition=rep+1),'inputs':ctasks} for rep in range(2) for cap in [256,512] for mode in [R,dict(matched,label='T_matched'),dict(candidate,label='N_candidate')]])
 longsummary={str(cap):panel([r for r in longrows if r['config']['cap']==cap]) for cap in [256,512]};save(ROOT/'E_LONG_SUMMARY.json',longsummary)
 if not all(all(s['qualification'].get(m,False) for m in ['T_matched','N_candidate']) for s in longsummary.values()):
  save(ROOT/'E_DECISION.json',{'status':'COMPLETED_SCIENTIFIC_FAIL','reason':'Independent long candidate qualification failed'});return
 resident_pass=True
 for name,capture in [('E_D_RESET',True),('E_D_TIMING',False)]:
  sessions=[]
  for cycle in [1,2]:
   order=sorted(inputs['shared'],key=lambda t:(hashlib.sha256((t['id']+'HeteroSpec-B570-Closeout-D-v1-cycle'+str(cycle)).encode()).hexdigest(),t['id']))
   for mode in [matched,candidate]:sessions.append({'config':dict(mode,cycle=cycle,cap=128,capture=capture),'inputs':order})
  rr=stage(name,sessions);bad=[r['unit_id'] for r in rr if not eq(r['endpoint'],ref(r['task']))];resident_pass&=not bad
  save(ROOT/(name+'_SUMMARY.json'),{'status':'COMPLETED_PASS' if not bad else 'COMPLETED_SCIENTIFIC_FAIL','failed':bad})
 gain=passed['N1_repaired'] and stats['generation_ms']>=1.03 and stats['whole_request_ms']>=1 and sum(d['generation_ms']>1 for d in stats['directions'])>=3
 save(ROOT/'E_DECISION.json',{'status':'ADOPT_INDEPENDENTLY_QUALIFIED_CANDIDATE' if gain and resident_pass else 'NO_ADDITIONAL_EFFICIENCY','candidate':candidate,'confirmation_costs':stats,'resident_pass':resident_pass,'qualification':passed,'claim_scope':'Tested finite B/C/resident scope only; ordinary control differs in target prefill and remains separately qualified'})
if __name__=='__main__':run()
