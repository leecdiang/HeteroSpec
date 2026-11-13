"""Fresh private archive and full indexed readback; no model/GPU calls."""
import argparse,hashlib,json,os,tarfile,time
from pathlib import Path
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main(first,retry):
 first=Path(first);retry=Path(retry);out=retry/'QUALIFICATION_RAW.tar';index=retry/'ARCHIVE_MANIFEST.private.json';report=retry/'ARCHIVE_READBACK.json'
 if any(p.exists() for p in [out,index,report]):raise RuntimeError('fresh archive only')
 if json.loads((retry/'FINAL_AUDIT.json').read_text())['status']!='PASS_ORIGINAL_GPU_RAW_LIFECYCLE_AND_COMPLETE_BUDGET_RECOUNT':raise RuntimeError('no complete original-raw audit')
 items=[];seen=set()
 def add(p,n):
  if n in seen:raise RuntimeError('duplicate archive member')
  seen.add(n);items.append(dict(member=n,source=str(p),bytes=p.stat().st_size,sha256=sha(p)))
 for label,base,roles in [('initial',first,['R','REPEAT','COLD','STRONG']),('retry01',retry,['STRONG','LOCAL'])]:
  for role in roles:
   for p in sorted((base/role).iterdir()):
    if p.is_file():add(p,label+'/'+role+'/'+p.name)
  for p in sorted(base.iterdir()):
   if p.is_file() and p.suffix in ['.json','.log','.py']:add(p,label+'/root/'+p.name)
  for p in sorted((base/'source/benchmarks/server_expansion_v1/N').rglob('*')):
   if p.is_file() and '__pycache__' not in p.parts:add(p,label+'/source/'+str(p.relative_to(base/'source')))
  for build in sorted(base.glob('*build*')):
   if not build.is_dir():continue
   for p in sorted(build.iterdir()):
    if p.is_file() and (p.suffix in ['.json','.log','.inc','.hpp','.cpp'] or p.name in ['bounded-reference','bounded-strong']):add(p,label+'/'+build.name+'/'+p.name)
 if sum(x['bytes'] for x in items)>105*1024**3:raise RuntimeError('archive selected bytes exceed retained footprint bound')
 with index.open('x') as f:json.dump(dict(schema='hs.private-original-capture-index.v1',items=items,total_bytes=sum(x['bytes'] for x in items)),f,sort_keys=True,indent=2)
 start=time.monotonic();fd=os.open(out,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'wb') as f:
  with tarfile.open(fileobj=f,mode='w') as tar:
   for x in items:tar.add(x['source'],arcname=x['member'],recursive=False)
  f.flush();os.fsync(f.fileno())
 wanted={x['member']:x for x in items};read=[]
 with tarfile.open(out,'r:') as tar:
  for member in tar:
   if not member.isfile() or member.name not in wanted:raise RuntimeError('unexpected archive member')
   x=wanted.pop(member.name);h=hashlib.sha256();n=0
   with tar.extractfile(member) as f:
    for b in iter(lambda:f.read(1048576),b''):h.update(b);n+=len(b)
   if n!=x['bytes'] or h.hexdigest()!=x['sha256']:raise RuntimeError('full readback differs '+member.name)
   read.append(member.name)
 if wanted:raise RuntimeError('archive members missing')
 with report.open('x') as f:json.dump(dict(status='PASS_FULL_PRIVATE_ARCHIVE_INDEX_READBACK',archive_file=out.name,archive_bytes=out.stat().st_size,archive_sha256=sha(out),members=len(read),indexed_source_bytes=sum(x['bytes'] for x in items),elapsed_s=time.monotonic()-start,new_model_calls=0,limitation='archive integrity/readback; numerical comparisons separately consume original raw captures; private archive is not anonymously available'),f,sort_keys=True,indent=2)
 print(report.read_text())
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--first',required=True);p.add_argument('--retry',required=True);a=p.parse_args();main(a.first,a.retry)
