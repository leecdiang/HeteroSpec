"""Serial request-budget campaign. Uses existing owned Job helper, no ETW/CUDA hooks."""
from pathlib import Path
import os,sys,json,time,datetime,ctypes as C,importlib.util,hashlib,shutil,re
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p))
e=p/'evidence';e.mkdir(exist_ok=True)
prior=(e/'ledger.jsonl').read_bytes()
old=[json.loads(x) for x in prior.splitlines()]
if not old or old[-1]['kind']!='CLOSED' or any(x.get('kind')=='RESERVED_BEFORE_CREATE' for x in old) or old[-1]['deployments']!=0 or old[-1]['requests_reserved']!=0 or old[-1]['rows_reserved']!=0:raise RuntimeError('Only proven zero-spend pre-model stop may be adopted')
if (e/'EXECUTION_MANIFEST_PRELOAD_002.json').exists():raise RuntimeError('This continuation was already attempted;preserve it')
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
w=module('winjob',p.parent/'rtx223-e08/attempt-006/winjob.py');ob=module('ob',p.parent/'rtx223-e11-u-contract/observation_v3.py')
model=Path('D:/HeteroSpec-PC/models/gguf/Qwen3-8B-Q8_0.gguf');sha=lambda q:hashlib.file_digest(Path(q).open('rb'),'sha256').hexdigest()
def put(q,data):
 with q.open('x',encoding='utf8') as f:json.dump(data,f,indent=2)
def events(q):
 if not q.exists():return []
 return [json.loads(x) for x in q.read_bytes().split(b'\n')[:-1] if x.strip()]
journal=(e/'ledger.jsonl').open('ab',buffering=0);reserved=0;loads=0;first=None;monitor=None;lease=None
def log(kind,**kw):
 row=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),kind=kind,**kw);raw=(json.dumps(row)+'\n').encode();written=journal.write(raw)
 if written!=len(raw):raise OSError('short ledger write')
 os.fsync(journal.fileno());print(json.dumps(row),flush=True)
def space():return sum(q.stat().st_size for q in e.rglob('*') if q.is_file())
def sample(owner=0):
 total,free,used,disk,ids=monitor.sample(p);util=monitor.utilization();foreign=[i for i in ids if i!=owner]
 if foreign:raise RuntimeError('foreign GPU compute processes '+str(foreign))
 if monitor.temperature>=85:raise RuntimeError('GPU temperature>=85C')
 if disk<15*1024**3 or space()>int(9.5*1024**3):raise RuntimeError('disk/evidence pressure')
 return dict(compute_pids=ids,util=util,temperature=monitor.temperature,free_bytes=free,used_bytes=used,disk_free=disk)
def idle():
 for _ in range(3):
  row=sample();
  if row['free_bytes']<10*1024**3 or row['util']>5:raise RuntimeError('device not idle or insufficient free VRAM')
  time.sleep(1)
 log('IDLE_PREFLIGHT',**row)
def phase(name,arm,reference,n,tokenizer=False):
 global reserved,loads,first
 for row in runtime[arm]:
  if sha(row['path'])!=row['sha256']:raise RuntimeError('runtime identity drift '+row['path'])
 idle();start=time.time()
 if first is None:first=start
 if reserved+n>228 or (reserved+n)*896>204288 or loads+1>18 or start-first>=21600:raise RuntimeError('campaign cap')
 reserved+=n;loads+=1;log('RESERVED_BEFORE_CREATE',phase=name,arm=arm,requests=n,rows=n*896,total_requests=reserved,total_rows=reserved*896,total_deployments=loads,first_wall=first)
 directory=e/name;directory.mkdir();result=directory/'results.jsonl';capture=directory/'capture';exe=p/('build-R2' if arm=='R' else 'build-M')/'bin'/('rtx244_reference.exe' if reference else 'rtx244_worker.exe')
 if reference:cmd=[exe,model,p/'inputs/raw_candidates.jsonl',result,capture,e/'tokenized.jsonl' if tokenizer else '-']
 else:
  tsv=e/(name+'.tsv') if '-fresh' in name or '-repeat-reset' in name else e/'prepared'/(name+'.tsv')
  lines=tsv.read_text(encoding='utf8').splitlines()
  if len(lines)!=n:raise RuntimeError('input request count differs from reserved count')
  for line in lines:
   values=line.split();np=int(values[2]);nc=int(values[3])
   if not 1<=np<=768 or nc!=128 or len(values)!=4+np+128 or any(int(x)<0 for x in values[4:]):raise RuntimeError('invalid reserved request work')
  cmd=[exe,model,tsv,result,capture]
 job=w.AtomicJob();lim=w.EXTENDED_LIMIT();lim.BasicLimitInformation.LimitFlags=0x2000|0x100|0x8;lim.BasicLimitInformation.ActiveProcessLimit=1;lim.ProcessMemoryLimit=16*1024**3;w.checked(w.SetJob(job.job,9,C.byref(lim),C.sizeof(lim)),'campaign single child,16GiB process commit')
 env={k:v for k,v in os.environ.items() if not k.startswith(('GGML_','HS_','HSC_'))};env['PATH']=str(exe.parent)+';'+env.get('PATH','')
 if reference or '-fresh' in name or '-repeat-reset' in name:env['GGML_CUDA_GRAPH_DEBUG']='1'
 # No graph/PDL disabling or global settings changes. One model per phase.
 seen=0;last=time.monotonic();sent=False;phase_start=time.monotonic();ok=False
 with (directory/'native.stdout.log').open('xb') as out,(directory/'native.stderr.log').open('xb') as err:
  try:
   job.create(cmd,p,env);job.resume();log('CHILD',phase=name,pid=job.pid,creation=job.creation,exe_sha256=sha(exe))
   while job.exit_code() is None:
    for fd,f in [(job.output,out),(job.error,err)]:
     chunk=job.read(fd)
     if chunk:f.write(chunk);f.flush()
    rows=events(result)
    if len(rows)>seen:last=time.monotonic();seen=len(rows)
    if reference and not sent and any(x.get('event')==('tokenizer_done' if tokenizer else 'loaded') for x in rows):
     if tokenizer:
      import prepare_selected
      info=prepare_selected.prepare();log('PANEL_FROZEN',bin_tops=info['actual_bin_tops'],roots=info['roots'])
     spec=e/(arm+'-reference.jsonl');os.write(job.input,(str(spec)+'\n').encode());sent=True
    if time.monotonic()-last>600 or time.time()-first>21600:raise TimeoutError('request/load600s or total6h')
    observed=sample(job.pid)
    if int(time.monotonic()-phase_start)%10==0:log('RESOURCE_SAMPLE',phase=name,**observed)
    time.sleep(.3)
   for fd,f in [(job.output,out),(job.error,err)]:
    while True:
     chunk=job.read(fd)
     if not chunk:break
     f.write(chunk)
   code=job.exit_code();rows=events(result)
   if code!=0 or not rows or rows[-1].get('event')!='done':raise RuntimeError(name+' failed exit='+str(code))
   req=[x for x in rows if x.get('event')=='request']
   if len(req)!=n or any(x['rows']>896 or x['kv_last_position']!=x['rows']-1 for x in req):raise RuntimeError('incomplete/request accounting')
   text=(directory/'native.stderr.log').read_text(encoding='utf8',errors='replace')
   offload=re.findall(r'offloaded (\d+)/(\d+) layers',text)
   if not offload or any(a!=b for a,b in offload):raise RuntimeError('full GPU layer offload unconfirmed')
   ok=True;log('PHASE_PASS',phase=name,actual_requests=len(req),actual_rows=sum(x['rows'] for x in req),wall_seconds=time.monotonic()-phase_start,exit=code,offload=offload)
   return req
  except BaseException as ex:
   job.kill();w.Wait(job.process,1000) if job.process else None
   log('PHASE_FAIL',phase=name,error=str(ex),owned_exit_confirmed=job.active()==0,actual_receipts=events(result));raise
  finally:job.close()
def qualify(arm):
 reference=events(e/(arm+'-reference')/'results.jsonl');ref={x['id']:x for x in reference if x.get('event')=='request'};offset=9000 if arm=='R' else 9100;comparisons=[]
 for passname,base in [('fresh',10),('repeat-reset',20),('repeat-reset',30)]:
  folder=e/(arm+'-'+passname);rows={x['id']:x for x in events(folder/'results.jsonl') if x.get('event')=='request'}
  for i in range(2):
   rid=offset+i+1;aid=offset+base+i+1;r=ref[rid];a=rows[aid]
   for key in ['rows','calls','capture_floats','kv_last_position','tokens','eog']:
    if a[key]!=r[key]:raise RuntimeError(f'{arm} qualification metadata {key}')
   x=e/(arm+'-reference')/('capture-'+str(rid)+'.f32');y=folder/('capture-'+str(aid)+'.f32');xb=x.read_bytes();yb=y.read_bytes()
   match=xb==yb
   comparisons.append(dict(native_id=rid,adapter_id=aid,bytes=len(xb),bitwise_equal=match,native_sha256=hashlib.sha256(xb).hexdigest(),adapter_sha256=hashlib.sha256(yb).hexdigest()))
   if not match:
    import array
    aa=array.array('f');aa.frombytes(xb);bb=array.array('f');bb.frombytes(yb);diff=[j for j,(u,v) in enumerate(zip(aa,bb)) if u!=v]
    put(e/(arm+'-DIFFERENCES.json'),dict(comparisons=comparisons,different_float_values=len(diff),first_indices=diff[:100],max_abs=max(abs(aa[j]-bb[j]) for j in diff) if diff else 0));raise RuntimeError(arm+' native/adapter full vector mismatch')
 if arm=='R':
  q=e/'R-reference/capture-9002.f32';raw=q.read_bytes();vocab=151936;frontier=raw[23*vocab*4:24*vocab*4];old=Path('D:/rtx192-review-v2/runs/Qwen-v2-matrix-R/native/q4-inside/captures/764/frontier.f32').read_bytes()
  equal=frontier==old;put(e/'R-HISTORICAL_FIXTURE.json',dict(bitwise_equal=equal,bytes=len(frontier),actual_sha256=hashlib.sha256(frontier).hexdigest(),historical_sha256=hashlib.sha256(old).hexdigest(),native_reference_threads=24,adapter_threads=2,native_batch=1024,adapter_batch=32,reference_ubatch=1))
  if not equal:raise RuntimeError('R historical fixture not reproduced')
 put(e/(arm+'-QUALIFICATION.json'),dict(pass_=True,comparisons=comparisons,scope='independently exercised complete native API vs adapter,all requested full vocabulary rows;short greedy and near-boundary forced continuation;not all-input math proof'))
 log('QUALIFICATION_PASS',arm=arm)
try:
 lease=w.DeviceLock(Path('D:/HeteroSpec-PC/RTX_EXPERIMENT.lock'),'HeteroSpecRTX244FullMigration');lease.acquire()
 power=C.create_string_buffer(12);w.checked(C.windll.kernel32.GetSystemPowerStatus(power),'power status')
 if power.raw[0]!=1:raise RuntimeError('AC power required')
 if sha(model)!='408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6':raise RuntimeError('model identity')
 runtime={}
 for arm,build in [('R','build-R2'),('M','build-M')]:
  runtime[arm]=[dict(path=str(q),bytes=q.stat().st_size,sha256=sha(q)) for q in sorted((p/build/'bin').iterdir()) if q.suffix in ['.dll','.exe']]
  for name in ['native_worker.cpp','native_reference.cpp']:
   if (p/build/name).read_bytes()!=(p/name).read_bytes():raise RuntimeError('compiled source snapshot differs '+arm+name)
 put(e/'EXECUTION_MANIFEST_PRELOAD_002.json',dict(parent_PR244='939b0ee51bb096fd699a981f89bd9e2b49f6fe82',model=dict(path=str(model),sha256=sha(model),bytes=model.stat().st_size),M_commit='0fb8f157702702f33f4e018de8701b2569a1bc28',R_original_static_library_sha256=sha(p.parent/'repo/work/native-original-v4/core/src/libllama.a'),runtime=runtime,source={name:sha(p/name) for name in ['native_worker.cpp','native_reference.cpp','campaign_continue.py','IMPLEMENTATION_PROTOCOL_ZH.md','prepare_selected.py']},settings='AC;unchanged balanced power plan;R ubatch1/reserve1,M ubatch32;ctx1024,F16KV,FAoff,formal threads2;graphs/PDL not disabled',new_budget=dict(requests=228,rows=204288,deployments=18,hours=6,evidence_GiB=10)))
 nvml=json.loads((p.parent/'rtx223-e11-u-contract/DEPLOYMENT.json').read_bytes())['modules']['nvml.dll'];monitor=ob.Management(nvml['path']);monitor.start()
 log('ZERO_SPEND_PREFIX_ADOPTED',bytes=len(prior),sha256=hashlib.sha256(prior).hexdigest());log('CAMPAIGN_APPROVED',requests=228,rows=204288,deployments=18,hours=6,evidence_GiB=10,old_ledgers_touched=False,CPU_tests_normal=21,CPU_tests_optimized=21)
 phase('R-reference','R',True,2,tokenizer=True)
 phase('R-fresh','R',False,2);phase('R-repeat-reset','R',False,4);qualify('R')
 # Existing CPU build may finish while R qualifies; never start another GPU worker.
 while not (p/'M_READY.json').exists():
  if time.time()-first>21000:raise TimeoutError('M not ready inside window')
  if (p/'BUILD_STOP').exists():raise RuntimeError('M build failed')
  time.sleep(2)
 phase('M-reference','M',True,2);phase('M-fresh','M',False,2);phase('M-repeat-reset','M',False,4);qualify('M')
 prepared=e/'prepared'
 for q in sorted(prepared.glob('[0-9][0-9]_*.json')):
  specs=json.loads(q.read_bytes());arm=specs[0]['arm'];phase(q.stem,arm,False,len(specs))
  shutil.copy2(e/q.stem/'results.jsonl',q.with_suffix('.results.jsonl'))
 import experiment
 records=experiment.collect(prepared)
 for mode in ['P','G']:put(e/(mode+'_ANALYSIS.json'),experiment.analyze(records,mode))
 put(e/'ALL_RECORDS.json',records);log('CAMPAIGN_PASS',formal_requests=192)
except BaseException as ex:
 log('CAMPAIGN_STOP',error=str(ex));put(e/'STOP_002.json',dict(error=str(ex)))
finally:
 log('CLOSED',requests_reserved=reserved,rows_reserved=reserved*896,deployments=loads,evidence_bytes=space(),GPU_context_or_physical_launch_hard_bound='NOT_PROVEN')
 journal.close()
 if monitor:monitor.close()
 if lease:lease.close()
