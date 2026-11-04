"""Read-only native evidence validation; never launches GPU or edits a result."""
from pathlib import Path, PureWindowsPath
import array,hashlib,json,math,sys,collections
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def require(ok,msg):
 if not ok:raise ValueError(msg)
def endpoint(r):return {k:v for k,v in r['endpoint'].items() if k!='state_sha256'}
def hostpath(s):return PureWindowsPath(s) if '\\' in s or (len(s)>1 and s[1]==':') else Path(s)
def verify(root,verify_vectors=True):
 root=Path(root);units=[];counts=collections.Counter();vectors={};failures=[];owned=0.;producer=0.;loads=0.;service=0.;preload=0.;verified_states=set()
 for unit in sorted((root/'units').iterdir()):
  if not unit.is_dir():continue
  task=read(unit/'JOB.json');budget=read(unit/'BUDGET.json');planned=task['slots'];receipt=read(unit/'RECEIPT.json');sup=read(unit/'SUPERVISOR.json')
  require(sup['job_accounting']['active_processes']==0,'unclean process '+unit.name)
  require(sup['assigned_before_resume'] is True,'uncontained worker')
  command=read(unit/'COMMAND.json');mp=command[command.index('--manifest')+1];role=hostpath(mp).parent.name
  manifest=root/role/'FILES.json';require(sha(manifest)==receipt['manifest_sha256']==sup['manifest_sha256'],'manifest drift')
  frozen=read(manifest)['files'];loaded={hostpath(x['path']).name.lower():x for x in sup['loaded_module_hashes']}
  for x in frozen:
   p=root/role/'build/Release'/hostpath(x['path']).name
   require(p.stat().st_size==x['bytes'] and sha(p)==x['sha256'],'delivered runtime drift')
   if p.suffix.lower()=='.dll':require(loaded.get(p.name.lower(),{}).get('sha256')==x['sha256'],'loaded runtime drift')
  n=read(unit/'native/result.json');records=n.get('records',[])
  if n['status']!='COMPLETE' or not receipt['success']:failures.append(dict(unit=unit.name,native=n['status'],error=n.get('error'),completed=len(records),reserved=len(planned)))
  else:require(len(records)==len(planned),'completed unit missing slots')
  owned+=receipt['owned_seconds'];loads+=n.get('load_seconds',0);preload+=n.get('cache_preload_seconds',0)
  for i,r in enumerate(records):
   s=planned[i];kind=s['kind'];counts[budget['stage']]+=kind!='admit'
   if kind=='seed':
    producer+=r['prefix_construction_seconds']
    for z in r['states']:
     p=unit/'native'/('state-'+str(z['head'])+'.bin');require(p.stat().st_size==z['bytes'] and sha(p)==z['sha256'],'prefix bytes drift')
   elif kind=='service':
    require(r['slot']==s,'raw schedule drift');service+=r['seconds'];require(math.isfinite(r['seconds']) and r['seconds']>0,'native elapsed')
    require(r['endpoint']['pending_decoded'] is False,'pending ownership')
    require(r['endpoint']['generated']<=s['cap'],'cap overflow')
    require(r['endpoint']['committed_tokens']==r['greedy'],'endpoint commit')
    require(s['heavy']==bool(r['vectors']),'observer inventory')
    if s.get('audit_state'):
     h=r['endpoint']['state_sha256'];p=root/'states'/h[:2]/h
     if h not in verified_states:require(sha(p)==h,'owned final state bytes');verified_states.add(h)
    if s['heavy']:
     require(len(r['vectors'])==len(r['greedy']),'incomplete full vector coverage')
     for h,tok in zip(r['vectors'],r['greedy'],strict=True):
      if h in vectors:require(vectors[h]==tok,'same vector inconsistent argmax')
      else:vectors[h]=tok
    if s.get('phases'):
     calls=r['append_calls'];start=r['physical_head'];at=start
     for c in calls:require(c['head']==at and 1<=c['width']<=32,'noncontiguous append');at+=c['width']
     require(at==len(s['ids']),'append duplicate/missing tokens')
  units.append(dict(unit=unit.name,status=n['status'],completed=len(records),reserved_requests=budget['requests'],owned_seconds=receipt['owned_seconds']))
 if verify_vectors:
  for h,tok in vectors.items():
   p=root/'vectors'/h[:2]/h;require(sha(p)==h and p.stat().st_size==151936*4,'owned full vocabulary vector identity')
   v=array.array('f');v.frombytes(p.read_bytes());require(all(map(math.isfinite,v)),'nonfinite reference vector');require(max(range(len(v)),key=v.__getitem__)==tok,'saved vector argmax')
 # Recompute every completed ordinary calibration qualification from raw bytes.
 q=[]
 for family in ('cal','main','aligned'):
  for u in sorted((root/'units').glob(family+'-qualification-*')):
   i=u.name.rsplit('-',1)[-1];nr=read(root/'units'/(family+'-reference-'+i)/'native/result.json')['records']
   if family!='aligned':require(nr[0]['vectors']==nr[1]['vectors'] and nr[0]['endpoint']==nr[1]['endpoint'],'original repeat')
   original=nr[0];n=read(u/'native/result.json')['records']
   for j in range(0,len(n)-1,2):
    a,b=n[j:j+2];ok=original['vectors']==a['vectors'] and original['endpoint']['state_sha256']==a['endpoint']['state_sha256'] and endpoint(original)==endpoint(a)==endpoint(b)
    off_state=b['endpoint'].get('state_sha256')==a['endpoint']['state_sha256']
    q.append(dict(unit=u.name,arm=a['slot']['arm'],vectors_and_endpoint_equal=ok,off_state_recorded_and_equal=off_state,qualified=ok and off_state))
 def canonical(v):return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()
 for family,filename in [('cal','calibration.json'),('main','results.json')]:
  if not (root/filename).exists():continue
  normalized=read(root/filename);found={}
  for unit in sorted((root/'units').glob(family+'-timing-session-*')):
   for r in read(unit/'native/result.json')['records']:
    m=r['slot']['schedule'];key=(m['id'],m['session'],m['arm'],m['kind']);require(key not in found,'duplicate native timed slot');found[key]=r
  require(len(found)==len(normalized['records']),'normalized/native timing completeness')
  for r in normalized['records']:
   raw=found[(r['id'],r['session'],r['arm'],r['kind'])];require(raw['seconds']==r['seconds'],'changed native service boundary')
   require(not raw['slot']['heavy'] and not raw['slot'].get('audit_state',False) and not raw['slot'].get('trace',False),'observer in clean formal time')
   if family=='main':require(canonical(endpoint(raw))==r['actual_output_sha256'],'normalized endpoint differs from native')
 return dict(status='RAW_RECONSTRUCTION_COMPLETE' if not failures else 'RAW_FAILURES_PRESERVED',units=units,completed_requests_by_stage=dict(counts),completed_model_requests=sum(counts.values()),charged_failed_requests=len(failures),zero_forward_probes=sum(r['reserved_requests']==0 and r['unit'].startswith('admit-') for r in units),unique_full_vectors=len(vectors),unique_final_states_verified=len(verified_states),vectors_independently_rehashed_and_argmax_checked=verify_vectors,failures=failures,native_qualification=q,total_owned_process_seconds=owned,model_load_seconds=loads,cache_preload_seconds=preload,prefix_construction_seconds=producer,native_service_seconds_including_qualification=service,performance_claim='Requires complete frozen main schedule and native qualification; this audit alone makes no speed claim')
if __name__=='__main__':print(json.dumps(verify(sys.argv[1],'--metadata-only' not in sys.argv),indent=2))
