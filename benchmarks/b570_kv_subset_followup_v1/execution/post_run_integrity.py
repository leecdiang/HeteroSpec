"""Read-only post-run actor/module/accounting verification; no inference."""
import argparse,json,hashlib,collections
from pathlib import Path

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--dest',type=Path,required=True);a=ap.parse_args();f=read(a.out/'FREEZE.json');pre=read(a.dest/'execution/HOST_PREFLIGHT.json')
 actors=[]
 for pin in f['runtime']+f['inputs']:
  p=Path(pin['path']);h=sha(p);assert h==pin['sha256'] and p.stat().st_size==pin['bytes'],str(p)
  actors.append({'path':str(p),'bytes':p.stat().st_size,'sha256':h,'unchanged':True})
 driver=[]
 for pin in pre['driver_pins']:
  p=Path(pin['path']);h=sha(p);assert h==pin['sha256'],str(p);driver.append({'path':str(p),'sha256':h,'unchanged':True})
 frozen_modules={str(Path(p['path']).resolve()).lower():p['sha256'] for p in f['runtime']}
 known_driver_paths={str(Path(p['path']).resolve()).lower() for p in pre['driver_pins'] if Path(p['path']).name.lower()=='igvk64.dll'}
 slots=[];loaded_igvk=set()
 for receipt_path in sorted((a.out/'receipts').glob('*.json')):
  r=read(receipt_path)
  if r['status']!='COMPLETED':continue
  rec=r['record'];identity=a.out/rec['identity_path'];assert sha(identity)==rec['identity_sha256']
  ident=read(identity);assert ident['status']=='PASS' and ident['owned_pid']==rec['owned_pid'] and not ident['api_layer_loaded']
  for mod in ident['modules']:
   key=str(Path(mod['path']).resolve()).lower();assert key in frozen_modules and mod['sha256']==frozen_modules[key]
  modules=read(identity.parent/'MODULES.stdout');modules=modules if isinstance(modules,list) else [modules]
  paths={str(Path(p).resolve()).lower() for p in modules if Path(p).name.lower()=='igvk64.dll'}
  assert paths and paths<=known_driver_paths,paths;loaded_igvk.update(paths)
  life=read(identity.parent/'LIFECYCLE.json');assert life['pid']==rec['owned_pid'] and life['returncode']==0 and not life['failed']
  slots.append({'slot':r['slot']['id'],'pid':rec['owned_pid'],'loaded_igvk':sorted(paths),'identity_and_lifecycle_pass':True})
 ledger=[json.loads(s) for s in (a.out/'LEDGER.jsonl').read_text().splitlines()]
 counts=dict(collections.Counter(x['event'] for x in ledger));starts=[x['slot'] for x in ledger if x['event']=='REQUEST_STARTED'];assert len(starts)==len(set(starts))<=192
 owned=sum(x['owned_seconds'] for x in ledger if x['event']=='WORKER_CLOSED');assert owned<=21600
 result={'status':'PASS_READ_ONLY_POST_RUN_INTEGRITY','actors_and_inputs':actors,'driver_pins':driver,'loaded_igvk_paths':sorted(loaded_igvk),'validated_worker_lifecycles':len(slots),'slots':slots,'ledger_event_counts':counts,'unique_request_starts':len(starts),'owned_gpu_process_seconds':owned,'native_forward_requests_added_by_this_check':0}
 with (a.dest/'execution/POST_RUN_INTEGRITY.json').open('x',encoding='utf8') as stream:json.dump(result,stream,ensure_ascii=False,sort_keys=True,indent=2);stream.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ('actors_and_inputs','driver_pins','slots')}))
if __name__=='__main__':main()
