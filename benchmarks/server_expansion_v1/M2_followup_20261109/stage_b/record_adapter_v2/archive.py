"""After terminal status only: retain raw commitments and sanitized text.

Never import a numerical library, execute a model, or alter a run. Binary
captures stay private on the authorized host. Public readback checks bytes,
not numerical equivalence. Foreign-job identifiers are omitted from export.
"""
from pathlib import Path
import argparse,gzip,hashlib,json,re,time
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_text())
def save(p,x):
 with p.open('x')as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--work',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 assert (a.work/'COMPLETE.json').exists()or list(a.work.glob('STOPPED-*')),'Only archive terminal runs'
 assert (a.work/'GUARD_STOPPED.private.json').exists()or(a.work/'PAUSE.json').exists(),'Close observer before freezing its evidence'
 a.out.mkdir();start=time.monotonic();texts=[];binary=[];records=[]
 groups={}
 for prefix in ('pr210-stage-b-source-','pr210-stage-b-build-','pr210-stage-b-20261109-'):
  for directory in a.root.glob(prefix+'*'):
   if directory.is_dir():groups[directory.name]=directory
 def sanitize(s):
  s=s.replace(str(a.root),'$HS_ROOT').replace(str(Path.home()),'$HOME')
  s=re.sub(r'GPU-[0-9a-fA-F-]{36}', '<allocated-or-redacted-GPU>',s)
  s=re.sub(r'\b(?:10|192\.168)\.\d+(?:\.\d+){1,2}\b','<private-network>',s)
  return s
 for alias,directory in sorted(groups.items()):
  for f in sorted(directory.rglob('*')):
   if not f.is_file():continue
   rel=f.relative_to(directory);name=alias+'/'+str(rel)
   if f.suffix in ('.bin','.f32'):
    binary.append(dict(path=name,bytes=f.stat().st_size,sha256=sha(f)));continue
   if f.suffix not in ('.json','.jsonl','.log','.py','.hpp','.cpp','.inc','.h','.md','.d','.map'):continue
   if any(x in f.name for x in ('GUARD_BASELINE','RESOURCE_GUARD','GUARD_PID','COORDINATOR_LAUNCH','SUPERVISOR')):continue
   if f.name.startswith(('supervisor.','archive.py.','replay_archive.py.')):continue
   if '__pycache__'in f.parts:continue
   raw=f.read_bytes()
   try:source=raw.decode('utf8')
   except UnicodeDecodeError:continue
   text=sanitize(source);b=text.encode()
   assert not re.search(r'192\.168\.\d|GPU-[a-fA-F0-9]{8}|/home/[a-z]',text),'Privacy export gate: '+name
   texts.append(dict(path=name,raw_bytes=len(raw),raw_sha256=hashlib.sha256(raw).hexdigest(),public_bytes=len(b),public_sha256=hashlib.sha256(b).hexdigest()))
   records.append(dict(path=name,text=text))
 # Resource evidence includes only experiment-relevant fields, never the other
 # devices' process IDs, user names, UUIDs or command names.
 resource=[]
 for f in sorted(a.root.glob('pr210-stage-b-20261109-*/RESOURCE_GUARD.private.jsonl')):
  cfg=read(f.parent/'config.private.json');samples=[]
  for line in f.read_text().splitlines():
   x=json.loads(line);selected=[g for g in x['gpu']if g['device']==cfg['gpu_uuid']]
   samples.append(dict(epoch=x['epoch'],selected_GPU_owned_processes=sum(g['own']for g in selected),selected_GPU_foreign_processes=sum(not g['own']for g in selected),foreign_cpu_on_assigned_cores=x['foreign_cpu_on_assigned_cores'],event_kinds=[e['kind']for e in x['events']]))
  resource.append(dict(epoch=f.parent.name,raw_bytes=f.stat().st_size,raw_sha256=sha(f),samples=samples))
 save(a.out/'RESOURCE_CHECKED.json',dict(only_experiment_relevant_fields=True,records=resource,sampling_seconds=5,limitations='No proof against all short events, existing-service requests, shared interconnect traffic or unobserved interference. GPU host guards separately sample every2s.'))
 payload=a.out/'TEXT_RECORDS.jsonl.gz'
 with payload.open('xb')as fo:
  with gzip.GzipFile(filename='',mode='wb',fileobj=fo,mtime=0)as z:
   for row in records:z.write((json.dumps(row,ensure_ascii=True,separators=(',',':'))+'\n').encode())
 save(a.out/'TEXT_INDEX.json',dict(files=texts,record_count=len(texts)))
 save(a.out/'BINARY_CAPTURE_INDEX.json',dict(files=binary,scope='Raw vectors and native sequence payloads retained privately; hashes do not independently verify numerical equivalence'))
 save(a.out/'BUNDLE.json',dict(file=payload.name,bytes=payload.stat().st_size,sha256=sha(payload),records=len(records),schema='heterospec.pr210.stage-B.text-records.v1'))
 ledgers=[];total_requests=total_rows=0
 for name in ('run-01','m1-run-01','m2-run-01','m2-run-02','m2-run-03',*[x.name for x in a.root.glob('pr210-stage-b-20261109-*')if(x/'ledger.jsonl').exists()]):
  f=a.root/name/'ledger.jsonl';xs=[json.loads(s)for s in f.read_text().splitlines()];res=[x for x in xs if x['event']=='RESERVE'];req=sum(x['requests']for x in res);rows=sum(x['rows']for x in res);total_requests+=req;total_rows+=rows
  ledgers.append(dict(name=name,sha256=sha(f),requests=req,conservative_rows=rows,complete_events=sum(x['event']=='COMPLETE'for x in xs),failed_events=sum(x['event']=='FAILED'for x in xs)))
 save(a.out/'COSTS.json',dict(cumulative_requests=total_requests,request_ceiling=2048,remaining_requests=2048-total_requests,cumulative_conservative_rows=total_rows,row_ceiling=8000000,remaining_rows=8000000-total_rows,ledgers=ledgers,
  Stage_B_worker_records=[dict(epoch=f.parent.parent.name,**read(f))for f in a.root.glob('pr210-stage-b-20261109-*/worker-records/*.json')],raw_binary_files=len(binary),raw_binary_bytes=sum(x['bytes']for x in binary),archive_wall_s=time.monotonic()-start,
  scope='Reservations include failures and are never refunded. Actual physical rows, model load, restore and operation clocks remain separate in native receipts. CPU preparation and all source epochs retained; no isolated total CPU or GPU-kernel-time estimate.'))
 save(a.out/'EXPORT_COMPLETE.json',dict(passed=True,raw_binary_files=len(binary),public_text_records=len(records),weights_or_executables_published=False,foreign_job_identifiers_published=False))
 print(json.dumps(dict(passed=True,records=len(records),gzip_bytes=payload.stat().st_size,binary_bytes=sum(x['bytes']for x in binary))),flush=True)
if __name__=='__main__':main()
