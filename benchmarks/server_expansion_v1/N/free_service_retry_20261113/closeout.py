"""No model/runtime imports. Audit and archive only after exact owned units exit."""
import argparse,datetime,fcntl,hashlib,json,os,subprocess,tarfile,time
from pathlib import Path

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def load(p):return json.loads(Path(p).read_text())
def put(p,j):
 with Path(p).open('x') as f:json.dump(j,f,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
def eq(a,b):
 n=0
 with Path(a).open('rb') as x,Path(b).open('rb') as y:
  while True:
   l=x.read(1048576);r=y.read(1048576)
   if l!=r:raise RuntimeError('raw bytes differ '+str(a)+' '+str(b)+' offset '+str(n))
   if not l:return n
   n+=len(l)
def unit(name):
 return subprocess.run(['systemctl','--user','show',name,'-p','ActiveState','-p','Result','-p','ExecMainStatus','-p','ControlGroup'],capture_output=True,text=True,check=True).stdout

def audit(a,b,out):
 s=load(b/'STATE.json') if (b/'STATE.json').exists() else load(a/'STATE.json');assert sha(a/'STATE.json')==load(b/'PARENT_LEDGER_IDENTITY.json')['sha256'];assert sum(q['rows'] for q in s['requests'].values())==s['consumed']['rows'];assert len(s['requests'])==s['consumed']['requests'];assert s['consumed']['requests']<=43 and s['consumed']['rows']<=40000 and s['consumed']['deployments']<=4
 episodes=[];jobs=[];pairs=[];totals={};resources=[];rawfiles=[];refs=load(b/'REFERENCES.json');oldcerts=set(load(a/'STATE.json')['passed_episodes'][i]['id'] for i in range(6))
 for role,base in [('R',a/'R'),('REFERENCE',a/'REFERENCE'),('CANDIDATE',b/'CANDIDATE')]:
  for f in sorted((base/'episodes').glob('*/EPISODE.json')):
   e=load(f);p=f.parent;cp=(a if role!='CANDIDATE' else b)/'certificates'/(e['episode']+'.json')
   if not cp.exists():continue
   cert=load(cp);assert cert['status']=='PASS'
   for x in cert['files']:
    q=p/x['file'];assert q.stat().st_size==x['bytes'] and sha(q)==x['sha256']
   for r in e['requests']:
    assert s['requests'][r['id']]['status']=='COMPLETED';assert s['requests'][r['id']]['rows']==r['rows'];assert r['pending']==r['consumer']['sampled_ids'][-1]
    for i,t in enumerate(r['consumer']['sampled_ids']):
     name='T%d-V%03d.f32'%(r['turn'],i);q=p/name;jobs.append(dict(path=str(q),name=str(q.relative_to(a.parent)),type='F32',bytes=607744,expected_greedy=t));rawfiles.append(q)
     if role!='R':pairs.append(eq(a/refs[e['case']]/name,q))
   kvs=list(p.glob('*.kv'))
   for q in kvs:
    m=load(q.with_suffix('.json'));assert q.stat().st_size==m['head']*147456;jobs.append(dict(path=str(q),name=str(q.relative_to(a.parent)),type='F16',bytes=q.stat().st_size));rawfiles.append(q)
    if role!='R':pairs.append(eq(a/refs[e['case']]/q.name,q))
   if e['stage'] not in ['COLD']:
    old=e['requests'][0]['native_head_after'];keep=e['requests'][1]['retained']
    if (p/'T1-retained.kv').exists():
     with (p/'T0-terminal.kv').open('rb') as x,(p/'T1-retained.kv').open('rb') as z:
      for i in range(576):
       x.seek(i*old*256);assert x.read(keep*256)==z.read(keep*256)
   timing=load((a if role!='CANDIDATE' else b)/'timings'/(e['episode']+'.json'))
   episodes.append(dict(episode=e['episode'],role=role,stage=e['stage'],arm=e['arm'],case=e['case'],round=e['round'],requests=[dict(id=r['id'],rows=r['rows'],input_tokens=len(r['prompt']['canonical_ids']),sampled=len(r['consumer']['sampled_ids']),retained=r['retained'],stop=r['consumer']['stop']) for r in e['requests']],timing=timing,phases=e['phases'],physical_calls=None if e['dispatch'] is None else e['dispatch']['physical_calls'],capture_depth=e['capture_depth']))
 # All failed first-turn artifacts remain in scope, but never counted as a passed episode.
 for q in sorted((a/'CANDIDATE/episodes').glob('*/*')):
  if q.suffix in ['.f32','.kv']:
   rawfiles.append(q);jobs.append(dict(path=str(q),name=str(q.relative_to(a.parent)),type='F32' if q.suffix=='.f32' else 'F16',bytes=q.stat().st_size))
 assert sum(q.stat().st_size for q in rawfiles)==s['raw_bytes']
 put(out/'RAW_JOBS.private.json',jobs)
 proc=subprocess.run([str(a/'raw-cpu-checker'),str(out/'RAW_JOBS.private.json')],capture_output=True,text=True,timeout=1800);(out/'RAW.stdout.json').write_text(proc.stdout);(out/'RAW.stderr.log').write_text(proc.stderr);assert proc.returncode==0;scan=json.loads(proc.stdout);assert len(scan['files'])==len(jobs)
 for j,x in zip(jobs,scan['files']):
  if 'expected_greedy' in j:assert x['greedy']==j['expected_greedy']
 data=[e for e in episodes if e['stage']=='MEASURE'];per_root=[]
 for case in ['C0','C1']:
  rows=[e for e in data if e['case']==case];vals={arm:[e['timing']['controller_service_plus_reset_s'] for e in rows if e['arm']==arm] for arm in ['W','L']}
  if all(len(vals[x])==2 for x in vals):per_root.append(dict(case=case,W_seconds=vals['W'],L_seconds=vals['L'],L_over_W=sum(vals['L'])/sum(vals['W']),reduction_percent=100*(1-sum(vals['L'])/sum(vals['W']))))
 w=sum(e['timing']['controller_service_plus_reset_s'] for e in data if e['arm']=='W');l=sum(e['timing']['controller_service_plus_reset_s'] for e in data if e['arm']=='L');summary=dict(status='COMPLETE_TWO_ROOT_DESCRIPTIVE' if len(data)==8 else 'PARTIAL_OR_NO_PANEL',measured_episodes=len(data),statistical_units='two preselected roots; repeats not independent roots',W_total_seconds=w,L_total_seconds=l,L_over_W=l/w if w else None,reduction_percent=100*(1-l/w) if w else None,per_root=per_root,population_CI=None)
 put(out/'STATISTICS.json',summary);put(out/'EPISODES.private.json',episodes);put(out/'FINAL_AUDIT.private.json',dict(status='PASS_RECOUNT_AND_ORIGINAL_BYTE_SCAN',consumed=s['consumed'],remaining=dict(requests=43-s['consumed']['requests'],rows=40000-s['consumed']['rows'],deployments=4-s['consumed']['deployments']),passed_episodes=len(episodes),full_vectors=sum(j['type']=='F32' for j in jobs),KV_files=sum(j['type']=='F16' for j in jobs),raw_bytes=sum(q.stat().st_size for q in rawfiles),full_byte_pairs=len(pairs),full_pair_bytes=sum(pairs),failed_requests=[dict(id=k,**v) for k,v in s['requests'].items() if v['status']!='COMPLETED'],universal_261_suite='NOT_RUN',GPU_requests_from_audit=0));return summary

def archive(a,b,out):
 dest=out/'PRIVATE_RAW.tar';index=[]
 with tarfile.open(dest,'w',format=tarfile.PAX_FORMAT) as t:
  for label,r in [('original',a),('successor',b)]:
   for p in sorted(r.rglob('*')):
    if p.is_socket() or p.is_symlink() or not p.is_file() or out in p.parents:continue
    arc=label+'/'+str(p.relative_to(r));t.add(p,arcname=arc,recursive=False);index.append(dict(name=arc,bytes=p.stat().st_size,sha256=sha(p)))
 put(out/'ARCHIVE_INDEX.private.json',index);expected={x['name']:x for x in index};read=0
 with tarfile.open(dest,'r:') as t:
  for m in t:
   assert m.isfile() and m.name in expected;f=t.extractfile(m);h=hashlib.sha256();n=0
   for x in iter(lambda:f.read(1048576),b''):h.update(x);n+=len(x)
   assert h.hexdigest()==expected[m.name]['sha256'] and n==expected[m.name]['bytes'];read+=1
 assert read==len(index);put(out/'ARCHIVE_READBACK.private.json',dict(status='PASS_ALL_ARCHIVE_MEMBERS_FULL_READBACK',archive_bytes=dest.stat().st_size,sha256=sha(dest),files=read,payload_bytes=sum(x['bytes'] for x in index),scope='private raw tensors/builds/logs/source/failures; absolute config paths private; symlink references restored using original/R and original/REFERENCE',GPU_requests=0))

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--parent',required=True);a=p.parse_args();r=Path(a.root);old=Path(a.parent);out=r/'CLOSEOUT01';out.mkdir(mode=0o700);fd=os.open(out/'OWNER.LOCK',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
 end=load(r/'WINDOW.json')['deadline_wall']+120
 while True:
  statuses={n:unit('hs-'+r.name+'-'+n+'.service') for n in ['controller','candidate']}
  if all('ActiveState=active' not in s and 'ActiveState=activating' not in s and 'ControlGroup=\n' in s for s in statuses.values()):break
  if time.time()>end:put(out/'BLOCKED.json',dict(reason='owned domain not verified empty; no model action or archive of changing files'));return
  time.sleep(10)
 put(out/'TERMINAL_UNITS.private.json',statuses)
 try:
  print(json.dumps(audit(old,r,out)),flush=True)
 except BaseException as e:put(out/'FAILED.json',dict(reason=str(e),GPU_requests=0))
 archive(old,r,out);put(out/'RESULT.json',dict(status='ARCHIVE_PASS_AUDIT_FAILED' if (out/'FAILED.json').exists() else 'AUDIT_AND_PRIVATE_ARCHIVE_PASS',finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),actual_GPU_requests=0))
if __name__=='__main__':main()
