"""Privacy-reviewed text/index export; never publishes private tensor bytes."""
import argparse,gzip,hashlib,io,json,re,tarfile,os
from pathlib import Path
def sha(b):return hashlib.sha256(b).hexdigest()
def main(first,retry):
 first=Path(first);retry=Path(retry);out=retry/'PUBLIC_EXPORT';out.mkdir(mode=0o700);host=str(first.parent)
 def redact(b):
  s=b.decode('utf8').replace(host,'${HS_ROOT}').replace(str(Path.home()),'${USER_HOME}').replace('/user.slice/user-'+str(os.getuid())+'.slice/user@'+str(os.getuid())+'.service','${DELEGATED_USER_DOMAIN}')
  s=re.sub(r'GPU-[0-9a-fA-F-]{30,}','${ALLOCATED_GPU_UUID}',s)
  if re.search(re.escape(str(Path.home()))+r'|192\.168\.|GPU-[0-9a-fA-F-]{30,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}',s):raise RuntimeError('privacy scan')
  return s.encode()
 entries=[];texts=[]
 def add(p,n):
  original=p.read_bytes();b=redact(original);texts.append((n,b));entries.append(dict(file=n,original_sha256=sha(original),published_sha256=sha(b),original_bytes=len(original),published_bytes=len(b),redacted=b!=original))
 for label,base,roles in [('initial',first,['R','REPEAT','COLD','STRONG']),('retry01',retry,['STRONG','LOCAL'])]:
  for role in roles:
   for p in sorted((base/role).iterdir()):
    if p.is_file() and (p.name.endswith(('.op.json','.caller.json')) or p.name.endswith('-state.json') or '-state-' in p.name and p.suffix=='.json' or p.name.endswith(('-frontier.json','-reconcile.json','-reset.json')) or p.name in ['CONFIG.json','RESULT.json','DISPATCH.json','UNIT_EXIT.json','RESOURCE_AFTER.json','FIRST_DIFFERENCE.json','STOP_NATIVE.json','stderr.log','stdout.log']):add(p,label+'/'+role+'/'+p.name)
  names=['STATE.json','MANIFEST.json','R-INDEPENDENT.json','REPEAT-INDEPENDENT.json','COLD-INDEPENDENT.json','STRONG-INDEPENDENT.json','LOCAL-INDEPENDENT.json','STRONG-INDEPENDENT.json.FAILED.json','R-VERIFY_PROCESS.json','REPEAT-VERIFY_PROCESS.json','COLD-VERIFY_PROCESS.json','STRONG-VERIFY_PROCESS.json','LOCAL-VERIFY_PROCESS.json','STOP_CONTROLLER.json','STOP_STRONG_CONTROLLER.json','QUALIFICATION_RESULT.json','STRONG_CPU_SOURCE_CHECK.json','RETRY_CPU_CHECK.json','HISTORICAL_PRESERVATION.private.json','FINAL_AUDIT.json','ARCHIVE_READBACK.json']
  for n in names:
   p=base/n
   if p.exists():add(p,label+'/root/'+n)
 for n in ['real-kernel-cpu01/RESULT.json','bridge-cpu01/RESULT.json','bridge-cpu01/worker/CPU_RESULT.json','bridge-cpu01/UNIT_EXIT.json']:
  p=first/n
  if p.exists():add(p,'CPU/'+n)
 for n,p in [('RETRY_MANIFEST.json',retry/'MANIFEST.json'),('FINAL_AUDIT.json',retry/'FINAL_AUDIT.json'),('ARCHIVE_READBACK.json',retry/'ARCHIVE_READBACK.json'),('HISTORICAL_PRESERVATION.json',retry/'HISTORICAL_PRESERVATION.private.json')]:
  (out/n).write_bytes(redact(p.read_bytes()))
 index=json.loads((retry/'ARCHIVE_MANIFEST.private.json').read_text());public_index=[{k:x[k] for k in ['member','bytes','sha256']} for x in index['items']]
 (out/'RAW_ARCHIVE_INDEX.json').write_text(json.dumps(dict(scope='private original archive member hashes and sizes; unavailable tensors are not revalidated by public text',members=public_index),sort_keys=True,indent=2)+'\n')
 with (out/'PUBLIC_TEXT_PACKET.tar.gz').open('xb') as f:
  with gzip.GzipFile(fileobj=f,mode='wb',mtime=0,filename='') as gz:
   with tarfile.open(fileobj=gz,mode='w|') as tar:
    for n,b in texts:
     info=tarfile.TarInfo(n);info.size=len(b);info.mtime=0;info.mode=0o600;tar.addfile(info,io.BytesIO(b))
 packet=(out/'PUBLIC_TEXT_PACKET.tar.gz').read_bytes();(out/'PUBLIC_TEXT_INDEX.json').write_text(json.dumps(dict(schema='hs.public-text-projection.v1',members=entries,packet_bytes=len(packet),packet_sha256=sha(packet),private_raw_archive_published=False,GPU_reexecution=False,numerical_replay_requires_original_raw=True),sort_keys=True,indent=2)+'\n')
 print(json.dumps(dict(status='EXPORTED_PRIVACY_SCANNED_TEXT_ONLY',members=len(entries),packet_bytes=len(packet),packet_sha256=sha(packet))))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--first',required=True);p.add_argument('--retry',required=True);a=p.parse_args();main(a.first,a.retry)
