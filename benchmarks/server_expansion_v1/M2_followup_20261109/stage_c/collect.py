"""C terminal-only text export, exact original/derived commitments, no GPU."""
from pathlib import Path
import argparse,gzip,hashlib,json,os,re
def read(p):return json.loads(p.read_text())
def save(p,x):
 with p.open('x')as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def h(b):return hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--work',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();w=a.work
 assert(w/'NATIVE_COMPLETE.json').exists()or(w/'FAILURE.json').exists();a.out.mkdir();items=[];records=[]
 files=[('work/'+str(p.relative_to(w)),p)for p in sorted(w.rglob('*'))if p.is_file()and p.suffix in('.json','.jsonl','.log','.py')and not p.is_relative_to(w/'closeout')and not p.is_relative_to(w/'export-01')and not p.is_relative_to(w/'control')]
 files += [('source/'+p.name,p)for p in sorted(a.source.iterdir())if p.is_file()]
 for name,p in files:
  if any(s in p.name for s in ('RESOURCE_GUARD','GUARD_BASELINE','LAUNCH.private')):continue
  raw=p.read_bytes();text=raw.decode('utf8').replace(str(a.root),'$HS_ROOT').replace(str(Path.home()),'$HOME');text=re.sub(r'GPU-[0-9a-fA-F-]{36}','<allocated-or-redacted-GPU>',text);text=re.sub(r'\b192\.168\.\d+\.\d+\b','<private-network>',text);data=text.encode()
  assert not re.search(r'GPU-[a-fA-F0-9]{8}|/home/[a-z]|192\.168\.\d',text),name
  items.append(dict(path=name,raw_bytes=len(raw),raw_sha256=h(raw),public_bytes=len(data),public_sha256=h(data)));records.append(dict(path=name,text=text))
 with(a.out/'TEXT_RECORDS.jsonl.gz').open('xb')as fo:
  with gzip.GzipFile(filename='',mode='wb',fileobj=fo,mtime=0)as z:
   for x in records:z.write((json.dumps(x,separators=(',',':'))+'\n').encode())
 b=(a.out/'TEXT_RECORDS.jsonl.gz').read_bytes();save(a.out/'BUNDLE.json',dict(schema='heterospec.pr210.stage-C.text-records.v1',file='TEXT_RECORDS.jsonl.gz',records=len(records),bytes=len(b),sha256=h(b)))
 save(a.out/'TEXT_INDEX.json',dict(files=items))
 inherited=read(w/'INHERITED_ACCOUNTING.json');xs=[json.loads(s)for s in(w/'ledger.jsonl').read_text().splitlines()]if(w/'ledger.jsonl').exists()else[];res=[x for x in xs if x['event']=='RESERVE'];req=sum(x['requests']for x in res);rows=sum(x['rows']for x in res)
 save(a.out/'COSTS.json',dict(Stage_C_requests=req,Stage_C_reserved_rows=rows,cumulative_requests=inherited['requests']+req,cumulative_reserved_rows=inherited['rows']+rows,remaining_requests=2048-inherited['requests']-req,remaining_rows=8000000-inherited['rows']-rows,reference_GPU_requests=0,failed_native_events=sum(x['event']=='FAILED'for x in xs),workers=[read(p)for p in sorted(w.glob('worker-records/*.json'))],scope='Host/process/operation clocks overlap; no energy or kernel-time measurement'))
 cfg=read(w/'config.private.json');resources=[]
 f=w/'RESOURCE_GUARD.private.jsonl'
 if f.exists():
  for line in f.read_text().splitlines():
   x=json.loads(line);g=[g for g in x['gpu']if g['device']==cfg['gpu_uuid']];resources.append(dict(epoch=x['epoch'],selected_GPU_foreign_processes=sum(not p['own']for p in g),foreign_cpu_on_assigned_cores=x['foreign_cpu_on_assigned_cores'],event_kinds=[e['kind']for e in x['events']]))
 save(a.out/'RESOURCE_CHECKED.json',dict(samples=resources,scope='5s observed interference gate only; short/shared-interconnect effects are not excluded'))
 # Local byte consistency; original private numerical eligibility remains B.
 with gzip.open(a.out/'TEXT_RECORDS.jsonl.gz','rt')as z:
  loaded=[json.loads(s)for s in z]
 assert len(loaded)==len(items)
 for x,item in zip(loaded,items):assert x['path']==item['path']and h(x['text'].encode())==item['public_sha256']
 save(a.out/'LOCAL_READBACK.json',dict(passed=True,records=len(loaded),native_requests=0,scope='Exported byte consistency; no new numerical qualification'))
 print(json.dumps(dict(passed=True,records=len(records),bytes=len(b),requests=req)),flush=True)
if __name__=='__main__':main()
