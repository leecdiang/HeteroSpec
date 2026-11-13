"""curl transport epoch for the same immutable, exact-hash public model objects.

Reuses verified-size completed ranges and validated partial prefixes from the
earlier transport. All attempts remain. Final whole-file SHA256 is mandatory.
"""
from pathlib import Path
import argparse, concurrent.futures, hashlib, ipaddress, json, os, re, shutil, subprocess, time
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"shared"))
from experiment import sha as digest
_spec=json.loads(Path(__file__).with_name("models.json").read_text())["target"]
_transport=json.loads(Path(__file__).with_name("transport_modelscope.json").read_text())
if _spec["sha256"]!=_transport["sha256"] or _spec["bytes"]!=_transport["bytes"]:raise ValueError("Pinned publisher transport identity mismatch")
MODELS={"Qwen14B":(_spec["repo"],_spec["revision"],_spec["filename"],_spec["bytes"],_spec["sha256"])}
MIRROR_REVISIONS={"Qwen14B":_transport["distribution_revision"]}

def headers(path):
 status=None;fields={}
 if path.exists():
  for line in path.read_text(encoding='latin1').splitlines():
   m=re.match(r'HTTP/[\d.]+\s+(\d+)',line)
   if m:status=int(m[1]);fields={}
   elif ':' in line:
    k,v=line.split(':',1);fields[k.lower()]=v.strip()
 return status,fields

def main():
 p=argparse.ArgumentParser();p.add_argument('key',choices=MODELS);p.add_argument('--out',type=Path,required=True);p.add_argument('--workers',type=int,default=8)
 p.add_argument('--epoch',default='curl04');p.add_argument('--dns-map',type=Path);a=p.parse_args()
 if not 1<=a.workers<=8:raise ValueError('network concurrency bound')
 if not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_-]{0,24}',a.epoch):raise ValueError('safe acquisition epoch')
 dns=json.loads(a.dns_map.read_text()) if a.dns_map else {}
 for host,ips in dns.items():
  if not (host=='modelscope.cn' or host.endswith('.modelscope.cn')) or not ips:raise ValueError('download-domain DNS snapshot only')
  for ip in ips:ipaddress.IPv4Address(ip)
 repo,original_revision,name,total,expected=MODELS[a.key];revision=MIRROR_REVISIONS[a.key]
 a.out.mkdir(parents=True,exist_ok=True)
 if shutil.disk_usage(a.out).free<3*total+20*1024**3:raise RuntimeError("Preserve20GiB after bounded acquisition scratch")
 parts=a.out/(a.key+'-parts');parts.mkdir(exist_ok=True);chunk=16*1024*1024
 def fetch(i):
  start=i*chunk;end=min(total,(i+1)*chunk)-1;size=end-start+1;final=parts/f'{i:04d}.part'
  if final.exists():
   if final.stat().st_size!=size:raise RuntimeError('range size changed')
   return i
  for attempt in range(8):
   stem=parts/f'{i:04d}-{a.epoch}-{attempt}';tmp=stem.with_suffix('.partial');log=stem.with_suffix('.json');tail=stem.with_suffix('.tail');head=stem.with_suffix('.headers.private');err=stem.with_suffix('.stderr.private')
   if log.exists() or tmp.exists():continue
   seeds=[]
   for prior in parts.glob(f'{i:04d}-*.json'):
    record=json.loads(prior.read_text());data=prior.with_suffix('.partial')
    valid=record.get('prefix_validated_by_range') or (record.get('http_status')==206 and record.get('content_range')==f'bytes {start}-{end}/{total}')
    if valid and data.exists() and 0<data.stat().st_size<=size:seeds.append(data)
   seed=max(seeds,key=lambda x:x.stat().st_size) if seeds else None;offset=seed.stat().st_size if seed else 0
   record={'part':i,'attempt':attempt,'transport':'curl-IPv4','status':'FAILED','start':start,'end':end,'resume_bytes':offset,'prefix_validated_by_range':bool(offset)};began=time.monotonic()
   try:
    with tmp.open('xb') as f:
     if seed:
      with seed.open('rb') as g:shutil.copyfileobj(g,f)
    if offset<size:
     url=f'https://modelscope.cn/models/{repo}/resolve/{revision}/{name}?transport=curl&part={i}&attempt={attempt}&offset={offset}'
     args=['curl','-4','-fsSL','--connect-timeout','10','--max-time','300','--retry','0','--range',f'{start+offset}-{end}',
           '--dump-header',str(head),'--output',str(tail),'--write-out','%{http_code} %{size_download} %{time_total}']
     for host,ips in dns.items():args+=['--resolve',host+':443:'+ips[(i+attempt)%len(ips)]]
     args.append(url)
     with err.open('xb') as stderr:r=subprocess.run(args,stdout=subprocess.PIPE,stderr=stderr)
     status,field=headers(head);observed=field.get('content-range');record.update(network_returncode=r.returncode,http_status=status,content_range=observed)
     if status!=206 or observed!=f'bytes {start+offset}-{end}/{total}':raise RuntimeError('exact Content-Range required')
     if not tail.exists() or tail.stat().st_size>size-offset:raise RuntimeError('range response length')
     record['prefix_validated_by_range']=True
     with tmp.open('ab') as f,tail.open('rb') as g:shutil.copyfileobj(g,f);f.flush();os.fsync(f.fileno())
    count=tmp.stat().st_size;record['bytes']=count
    if count!=size:raise RuntimeError('partial transfer retained for resume')
    record.update(status='COMPLETE',sha256=digest(tmp));os.rename(tmp,final)
   except Exception as e:record.update(error_type=type(e).__name__,bytes=tmp.stat().st_size if tmp.exists() else 0)
   finally:
    record['wall_s']=time.monotonic()-began
    with log.open('x') as f:json.dump(record,f,indent=2);f.write('\n')
   if record['status']=='COMPLETE':print(json.dumps({'key':a.key,'part':i,'bytes':size,'transport':'curl','status':'COMPLETE'}),flush=True);return i
  raise RuntimeError('bounded curl range attempts exhausted: '+str(i))
 count=(total+chunk-1)//chunk
 with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:list(pool.map(fetch,range(count)))
 path=a.out/name;partial=a.out/(name+'.assembled-partial')
 if not path.exists():
  if partial.exists():raise RuntimeError('retain previous assembled failure')
  with partial.open('xb') as f:
   for i in range(count):
    with (parts/f'{i:04d}.part').open('rb') as g:shutil.copyfileobj(g,f,8*1024*1024)
   f.flush();os.fsync(f.fileno())
  if partial.stat().st_size!=total or digest(partial)!=expected:raise RuntimeError('full model identity mismatch; retained assembled failure')
  os.rename(partial,path)
 if path.stat().st_size!=total or digest(path)!=expected:raise RuntimeError('actual model changed')
 receipt=a.out/(a.key+'-VERIFIED.json');record={'repo':repo,'revision':original_revision,'distribution':'modelscope','distribution_revision':revision,
      'file':name,'bytes':total,'sha256':expected,'verified':True,'acquisition':'validated exact ranges; curl resume epoch; final complete-file SHA256','parts':count,
      'process_local_DNS_snapshot_sha256':digest(a.dns_map) if a.dns_map else None,'TLS_verification_disabled':False}
 if not receipt.exists():
  with receipt.open('x') as f:json.dump(record,f,indent=2);f.write('\n')
 print(json.dumps(record),flush=True)

if __name__=='__main__':main()
