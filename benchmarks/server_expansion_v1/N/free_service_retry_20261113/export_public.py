"""Privacy-reviewed text/index export; zero tensor bytes and no runtime imports."""
import argparse,gzip,hashlib,io,json,os,re,tarfile
from pathlib import Path

def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--parent',required=True);args=p.parse_args();b=Path(args.root);a=Path(args.parent);out=b/'PUBLIC01';out.mkdir(mode=0o700);close=b/'CLOSEOUT01';cfg=load(b/'CONFIG.private.json');text={};mapping=[]
 replacements=[(str(b),'${SUCCESSOR_RUN}'),(str(a),'${ORIGINAL_RUN}'),(cfg['producer_build'],'${PINNED_PRODUCER_BUILD}'),(cfg['host_root'],'${HS_ROOT}'),(cfg['gpu_uuid'],'${ALLOCATED_GPU_UUID}'),(str(Path(cfg['producer_build']).parents[1]),'${CPU_WORKSPACE}')]
 def scrub(raw):
  s=raw.decode('utf8')
  for old,new in replacements:s=s.replace(old,new)
  if str(Path.home()) in s or '192.168.' in s or re.search(r'GPU-[a-f0-9]{8}-',s):raise RuntimeError('unredacted private identity')
  return s.encode()
 def add(name,path):
  raw=Path(path).read_bytes();clean=scrub(raw);text[name]=clean;mapping.append(dict(file=name,original_bytes=len(raw),original_sha256=sha(raw),published_bytes=len(clean),published_sha256=sha(clean),tensor_bytes_in_public_file=0))
 for label,r in [('original',a),('successor',b)]:
  for n in ['STATE.json','WINDOW.json','MANIFEST.json','REFERENCES.json','PARENT_LEDGER_IDENTITY.json','RESULT.json','ACTUAL_GEOMETRY_GATE.json','ALL_LIGHT_WARM_GATES_PASS.json','PERFORMANCE_ADMISSION.json','ABI_DIAGNOSIS02.json','CPU_CHECK_RESULT.json','ENVIRONMENT_PREFLIGHT.private.json','PRELAUNCH.private.json','ACTUAL_PREFIX_ANALYSIS.json','SOURCE_PUBLICATION_MAP.json','TERMINAL_RESOURCES.private.json']:
   if (r/n).exists():add(label+'/'+n.replace('.private',''),r/n)
  for d in ['certificates','timings']:
   for f in sorted((r/d).glob('*.json')):add(label+'/'+str(f.relative_to(r)),f)
  roles=['R','REFERENCE','CANDIDATE'] if label=='original' else ['CANDIDATE']
  for role in roles:
   base=r/role
   for n in ['CONFIG.json','RESULT.json','STOP_CONTROLLER.json','UNIT_EXIT.json','ACTUAL_PEER.json','PREEXEC_KERNEL.json']:
    if (base/n).exists():add(label+'/'+role+'/'+n,base/n)
   for ep in sorted((base/'episodes').glob('*')):
    for f in sorted(ep.iterdir()):
     if f.suffix in ['.json','.log'] and f.is_file():add(label+'/'+str(f.relative_to(r)),f)
  for n in ['controller.stderr.log']:
   if (r/n).exists():add(label+'/'+n,r/n)
  for build in sorted(r.glob('build[0-9]*')):
   if (build/'BUILD.private.json').exists():add(label+'/'+build.name+'/BUILD.json',build/'BUILD.private.json')
 for n in ['consumer-cpu03/RESULT.json','real-kernel-cpu01/RESULT.json','validator-cpu01/RESULT.json']:
  if (a/n).exists():add('original/'+n,a/n)
 for n in ['STATISTICS.json','FINAL_AUDIT.private.json','EPISODES.private.json','ARCHIVE_INDEX.private.json','ARCHIVE_READBACK.private.json','TERMINAL_UNITS.private.json','FAILED.json','RESULT.json']:
  if (close/n).exists():add('closeout/'+n.replace('.private',''),close/n)
 # Raw resource traces retain only the admitted target's own workload and aggregate host counters.
 for label,r in [('original',a),('successor',b)]:
  for f in r.glob('*/RESOURCE_TRACE.jsonl'):
   raw=f.read_bytes();add(label+'/'+str(f.relative_to(r)),f)
 packet=out/'PUBLIC_TEXT_PACKET.tar.gz'
 with packet.open('xb') as file:
  with gzip.GzipFile(fileobj=file,mode='wb',mtime=0) as gz:
   with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tar:
    for name,raw in sorted(text.items()):
     info=tarfile.TarInfo(name);info.size=len(raw);info.mode=0o600;info.mtime=0;tar.addfile(info,io.BytesIO(raw))
 index=[dict(file=n,bytes=len(v),sha256=sha(v)) for n,v in sorted(text.items())]
 (out/'PUBLIC_TEXT_INDEX.json').write_text(json.dumps(index,indent=2)+'\n');(out/'PRIVACY_TRANSFORM.json').write_text(json.dumps(mapping,indent=2)+'\n')
 checked=0
 with tarfile.open(packet,'r:gz') as tar:
  for member in tar:
   expected=text[member.name];assert tar.extractfile(member).read()==expected;checked+=1
 (out/'PUBLIC_TEXT_READBACK.json').write_text(json.dumps(dict(status='PASS_ALL_SANITIZED_TEXT_BYTES',members=checked,packet_bytes=packet.stat().st_size,packet_sha256=sha(packet.read_bytes()),raw_tensor_bytes_read_by_public_replay=0,original_raw_validation='separate private archive and original-byte audit; public index is not independent tensor validation',actual_model_requests=0),indent=2)+'\n');print('PUBLIC_TEXT_EXPORT_AND_FULL_READBACK_PASS',checked)
if __name__=='__main__':main()
