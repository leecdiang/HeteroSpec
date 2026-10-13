"""Independent CPU parser. Does not import executor endpoint/qualification/cost code."""
from pathlib import Path
import json,hashlib,statistics,math,sys,copy
R=Path(sys.argv[2]) if len(sys.argv)>2 else Path('C:/hs/jsa-b570-run-v1')
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(n,x):(R/n).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def endpoint(raw,meta):
 ids=raw['ids'];flags=raw['eog'];assert len(ids)==len(flags)>0
 assert all(type(i)==int and 0<=i<meta['vocab_tokens'] for i in ids) and all(type(b)==bool for b in flags)
 assert flags==[i in meta['runtime_eog_ids'] for i in ids]
 last=min(128,next((k+1 for k,i in enumerate(ids) if i in meta['runtime_eog_ids']),len(ids)))
 assert last==128 or flags[last-1]
 return dict(ids=ids[:last],eog=flags[:last],reason='EOG' if flags[last-1] else 'CAP',raw_suffix=len(ids)-last)
def same(a,b):return all(a[k]==b[k] for k in ['ids','eog','reason'])
def rawsame(a,b):return a['ids']==b['ids'] and a['eog']==b['eog']
def verify(stage):
 errors=[];checks=0;records=[];details=[];missing=[]
 def ck(ok,msg):
  nonlocal checks;checks+=1
  if not ok:errors.append(msg)
 specs=load(R/'REQUEST_SCHEDULE.json')[stage];meta=load(R/('QWEN_RUNTIME.json' if stage=='A' else 'TOKENIZATION_BINDINGS.json'));history=load(R/'HISTORICAL_OWN_PATH.json') if stage=='A' else {}
 for spec in specs:
  session=R/'sessions'/spec['session'];ck((session/'SESSION_CLOSE.json').exists(),'unclosed '+spec['session'])
  if not (session/'MODULES.json').exists():ck(False,'missing actual modules '+spec['session']);continue
  mods=load(session/'MODULES.json');ck(mods['all_layers_on_B570'],'offload '+spec['session'])
  for module in mods['actual']:ck(sha(module['FileName'])==module['sha256'],'actual module '+module['FileName'])
  for q in spec['requests']:
   u=q['unit'];p=R/'raw'/hashlib.sha256(u.encode()).hexdigest()[:24]/'RESULT.json'
   if not p.exists():missing.append(u);continue
   r=load(p);inp=load(R/q['input_file'])[q['input_index']];ck(r['unit']==u and r['task']==inp['id'] and r['session']==spec['session'] and r['arm']==spec['arm'] and r['warm']==q['warm'],'schedule '+u)
   for f,h in r['files'].items():ck(sha(R/f)==h,'file '+f)
   raw=load(p.parent/'capture.json');metrics=load(p.parent/'capture.json.metrics.json');ck(raw['prompt_ids']==inp['prompt_ids'],'input '+u)
   ck(metrics==r['metrics'] and metrics['raw_count']==len(raw['ids']),'payload '+u)
   try:ep=endpoint(raw,meta)
   except (AssertionError,KeyError,TypeError):ck(False,'invalid independent raw '+u);continue
   ck(ep==r['endpoint'] and raw['ids']==r['raw_ids'] and raw['eog']==r['raw_eog'],'independent endpoint '+u)
   ck(type(r['host_seconds']) in [int,float] and math.isfinite(r['host_seconds']) and r['host_seconds']>0,'positive paid timer '+u)
   ck(metrics['threads']==metrics['batch_threads']==10,'threads '+u)
   ck(metrics['reset_target']['min']==metrics['reset_target']['max']==-1,'reset '+u)
   transfer=raw.get('transfer')
   if transfer:
    ck(transfer['kv_equal'] and transfer['source_unchanged'] and transfer['state_bytes']==transfer['consumed_bytes'],'transfer '+u)
    paths=[p.parent/('capture.json'+s) for s in ['.before.kv','.restored.kv','.source_after.kv']]
    if spec['capture']:
     ck(all(f.exists() for f in paths),'captured transfer files '+u)
     if all(f.exists() for f in paths):ck(len({sha(f) for f in paths})==1,'actual raw KV transfer '+u)
   if spec['arm'] in ['M','C']:
    phase=metrics['phase_binding'];ck(phase['source_ub']==128 and phase['destination_ub']==1 and not phase['state_transfer'],'inplace recipe '+u)
    if spec['capture']:
     before=p.parent/'capture.json.phase_before.kv';after=p.parent/'capture.json.phase_after.kv';ck(before.exists() and after.exists() and sha(before)==sha(after),'actual phase raw KV '+u)
   old=history.get(r['task']+'/'+r['arm']) if stage=='A' else None
   if stage=='A' and not q['warm']:
    ck(old is not None,'historical own path missing '+u)
    if old:ck(raw['ids']==old['ids'] and raw['eog']==old['eog'] and same(ep,old['endpoint']),'own historical arrays '+u)
   if not q['warm']:records.append((r,raw));details.append(dict(unit=u,task=r['task'],arm=r['arm'],round=r['round'],capture=r['capture'],endpoint_length=len(ep['ids']),raw_length=len(raw['ids']),suffix=ep['raw_suffix'],reason=ep['reason'],host_seconds=r['host_seconds']))
 expected=32 if stage=='A' else 128 if stage=='B' else 384
 ck(len(records)==expected,'complete declared nonwarm matrix '+str(expected));ck(not missing,'missing requests '+str(len(missing)))
 if stage in ['A','B']:
  tasks=load(R/'QWEN_INPUTS.json' if stage=='A' else R/'SMOL_DISCOVERY_INPUTS.json');probes=[x['id'] for x in tasks[:4]]
  for task in probes:
   for arm in ['R','N','M','C']:
    xs=[x for r,x in records if r['task']==task and r['arm']==arm];ck(len(xs)==(2 if stage=='A' else 4),'capture count '+task+arm)
    ck(all(rawsame(xs[0],x) for x in xs[1:]),'observer same raw '+task+arm)
  if stage=='B':
   for task in [x['id'] for x in tasks]:
    xs=[r['endpoint'] for r,x in records if r['task']==task and r['arm']=='R'];ck(all(same(xs[0],x) for x in xs[1:]),'ordinary R stability '+task)
 result=dict(status='PASS' if not errors else 'PARTIAL_OR_ENGINEERING_FAILURE',checks=checks,errors=errors,missing=missing,complete=len(records),expected=expected,details=details)
 if stage=='D':
  tasks=[x['id'] for x in load(R/'SMOL_CONFIRMATION_INPUTS.json')];index={(r['task'],r['arm'],r['round']):(r,x) for r,x in records};ck(len(index)==len(records),'duplicate formal tuple')
  qualification={}
  for arm in ['R','N','M','C']:
   complete=all((t,arm,k) in index for t in tasks for k in range(4));equal=complete;stable=complete;raw_equal=complete;raw_stable=complete;bad=[]
   for t in tasks:
    xs=[index[(t,arm,k)] for k in range(4) if (t,arm,k) in index]
    stable &= len(xs)==4 and all(same(xs[0][0]['endpoint'],r['endpoint']) for r,x in xs[1:])
    raw_stable &= len(xs)==4 and all(rawsame(xs[0][1],x) for r,x in xs[1:])
    for k in range(4):
     if (t,arm,k) not in index or (t,'R',k) not in index:equal=False;raw_equal=False;continue
     a,raw=index[(t,arm,k)];b,ref=index[(t,'R',k)];eq=same(a['endpoint'],b['endpoint']);equal &=eq;raw_equal &=rawsame(raw,ref)
     if not eq:bad.append(dict(task=t,round=k,arm=arm,first_divergence=next((i for i,(u,v) in enumerate(zip(a['endpoint']['ids'],b['endpoint']['ids'])) if u!=v),min(len(a['endpoint']['ids']),len(b['endpoint']['ids']))),observed_length=len(a['endpoint']['ids']),R_length=len(b['endpoint']['ids'])))
   qualification[arm]=dict(complete=complete,endpoint_equal_to_R=bool(equal),endpoint_stable=bool(stable),endpoint_qualified=bool(complete and equal and stable),raw_equal_to_R=bool(raw_equal),raw_stable=bool(raw_stable),mismatches=bad)
  costs={}
  for baseline in ['R','M','N']:
   ratios=[];taskrows=[];rounds=[];complete=qualification[baseline]['complete'] and qualification['C']['complete']
   if complete:
    for t in tasks:
     bs=[index[(t,baseline,k)][0]['host_seconds'] for k in range(4)];cs=[index[(t,'C',k)][0]['host_seconds'] for k in range(4)];ratio=statistics.median(bs)/statistics.median(cs);ratios.append(ratio);taskrows.append(dict(task=t,baseline_median_seconds=statistics.median(bs),C_median_seconds=statistics.median(cs),baseline_over_C=ratio,round_ratios=[a/b for a,b in zip(bs,cs)]))
    for k in range(4):
     rs=[index[(t,baseline,k)][0]['host_seconds']/index[(t,'C',k)][0]['host_seconds'] for t in tasks];rounds.append(dict(round=k,GM=math.exp(statistics.mean(map(math.log,rs))),faster=sum(x>1 for x in rs),slower=sum(x<1 for x in rs)))
   qualified=complete and qualification['R']['endpoint_qualified'] and qualification[baseline]['endpoint_qualified'] and qualification['C']['endpoint_qualified']
   gm=math.exp(statistics.mean(map(math.log,ratios))) if ratios else None
   costs[baseline+'/C']=dict(complete_comparator_pair=complete,qualified_speedup=gm if qualified else None,diagnostic_host_GM=gm,diagnostic_denominator_tasks=len(ratios),all_24_no_subset_selection=True,taskrows=taskrows,rounds=rounds,ratio_definition='baseline/C',cross_date_CI=None)
  result.update(qualification=qualification,costs=costs,distinct_process_sessions=len(specs),dates=sorted({load(R/'sessions'/s['session']/'SESSION.json')['utc'][:10] for s in specs if (R/'sessions'/s['session']/'SESSION.json').exists()}));result['status']='PASS' if not errors else 'PARTIAL_OR_ENGINEERING_FAILURE';result['checks']=checks;result['errors']=errors
 save(stage+'_VERIFICATION.json',result);print(stage,result['status'],len(records),'checks',checks,'errors',errors[:8],flush=True)
 return result
if __name__=='__main__':verify(sys.argv[1])
