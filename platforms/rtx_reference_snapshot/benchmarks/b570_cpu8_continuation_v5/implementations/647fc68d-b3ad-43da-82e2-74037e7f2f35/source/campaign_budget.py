"""CPU campaign limits from retained raw evidence. Charges are not fabricated OS lifetimes."""
import json,datetime,math,os,shutil
from pathlib import Path
START_LIMIT=3000;LIFE_LIMIT=21600;STORAGE_LIMIT=1024**3;RESERVE=256*1024**2;EXPORT=64*1024**2
def need(v,m):
 if not v:raise ValueError(m)
def load(p):return json.loads(Path(p).read_bytes())
def config(root,read_only=False):
 root=Path(root).resolve();c=load(root/'CAMPAIGN.json')
 need(c['schema']==1 and c['first_preparation_utc']==load(root/'ACQUISITION.json')['first_preparation_utc'],'campaign origin')
 ext=Path(c['external_root']).resolve();original=Path(c['original_root']).resolve()
 need(ext!=original and original not in ext.parents and ext not in original.parents,'campaign external root')
 if root!=original:
  need(read_only and ext in root.parents and (root/'delivery/EVIDENCE_MANIFEST.json').is_file(),'campaign relocated read-only root')
 return c,ext
def previous(root,read_only=False):
 c,_=config(root,read_only);roots=[Path(root).resolve()];extras=0
 from evidence_contract import member,manifest_check
 for row in c.get('previous',[]):
  p=member(root,row['snapshot'],directory=True);manifest_check(p,row['manifest'])
  need(__import__('hashlib').sha256((p/row['manifest']).read_bytes()).hexdigest()==row['manifest_sha256'],'prior attempt binding')
  need(load(p/'ACQUISITION.json')['first_preparation_utc']==c['first_preparation_utc'],'prior clock reset')
  need(p not in roots,'duplicate prior attempt');roots.append(p);extras+=allocation(p)[0]
 return roots,extras
def rows(p):
 data=p.read_bytes()
 # Live journals can end in an incomplete write; complete-case auditors separately require final LF.
 return [json.loads(x) for x in data.split(b'\n')[:-1]]
def process_check(root,reserve_starts=0,now=None,read_only=False):
 roots,_=previous(root,read_only);known={};exits={};tool_charge=0;tool_life=0.;unknown=[]
 utcnow=now or datetime.datetime.now(datetime.timezone.utc)
 need(utcnow.tzinfo is not None,'campaign clock');ft=int(utcnow.timestamp()*10**7)+116444736000000000
 for r in roots:
  paths=set((r/'processes').glob('*/OS_EVENTS.jsonl'))
  for base in [r/'development',r/'formal']:
   paths.update(base.glob('*/WATCHDOG.jsonl'));paths.update(base.glob('*/SUPERVISOR.jsonl'));paths.update(base.glob('*/*/EVENTS.jsonl'))
  paths.update((r/'legacy/runs').glob('*/external/ROUND.jsonl'))
  for p in sorted(paths):
   for x in rows(p):
    pid=x.get('pid');born=x.get('created_filetime');end=x.get('exit_filetime')
    if x.get('event') in ('CHILD_SPAWNED','CHILD_CLOSED'):
     pid=x.get('pid_child');ts=x.get('os_times',{});born=ts.get('creation_FILETIME');end=ts.get('exit_FILETIME')
    if type(pid) is not int or pid<=0 or born is None:continue
    born=int(born);need(born>0,'campaign identity');k=(pid,born);known[k]=True
    if end is not None and int(end)>0:
     end=int(end);need(end>=born,'campaign OS lifetime');need(k not in exits or exits[k]==end,'campaign conflicting exit');exits[k]=end
  tool_paths=list((r/'tools').glob('*.intent.json'))
  if r==Path(root).resolve() and not read_only:
   _,ext=config(root);tool_paths+=list((ext/'tools').glob('*.intent.json'))
  for p in sorted(tool_paths):
   intent=load(p);cmd=intent['request']['cmd'];charge=6 if 'startup_preflight.py' in cmd else 3 if 'review_entry.py' in cmd else 2
   declared=intent.get('unobserved_start_reserve',charge);need(type(declared) is int and declared>=charge,'under-reserved infrastructure')
   tool_charge+=declared
   t=datetime.datetime.fromisoformat(intent['registered_utc'].replace('Z','+00:00'));end=utcnow
   finals=[p.with_name(p.name.replace('.intent.json','.initial.json')),*p.parent.glob(p.name.replace('.intent.json','.poll*.json')),*p.parent.glob(p.name.replace('.intent.json','.final*.json'))]
   terminal=[]
   for f in finals:
    if not f.exists():continue
    z=load(f)
    if z.get('response',{}).get('exit_code') is not None and z.get('observed_utc'):terminal.append(datetime.datetime.fromisoformat(z['observed_utc'].replace('Z','+00:00')))
   if not terminal:
    bound=p.with_name(p.name.replace('.intent.json','.terminal-bound.json'))
    if bound.exists():
     b=load(bound);from evidence_contract import member
     q=member(r,b['target']);data=q.read_bytes();need(len(data)==b['bytes'] and __import__('hashlib').sha256(data).hexdigest()==b['sha256'],'terminal bound bytes')
     z=json.loads(data);initial=load(p.with_name(p.name.replace('.intent.json','.initial.json')))
     need(z['request']['session_id']==initial['response']['session_id']==b['session_id'] and z['response']['exit_code']==0,'terminal bound session')
     need(b['api_observed_utc'] is None and b['os_exit_filetime'] is None,'no fabricated lifecycle')
     upper=datetime.datetime.fromisoformat(b['terminal_upper_bound_utc'].replace('Z','+00:00'));captured=datetime.datetime.fromisoformat(b['metadata_observed_utc'].replace('Z','+00:00'))
     born=datetime.datetime.fromisoformat(b['file_birth_utc'].replace('Z','+00:00'));written=datetime.datetime.fromisoformat(b['file_last_write_utc'].replace('Z','+00:00'))
     need(t<=born<=upper<=captured and t<=written<=upper,'terminal metadata bound order')
     if not read_only:
      s=q.stat();need(abs(s.st_ctime-born.timestamp())<.002 and abs(s.st_mtime-written.timestamp())<.002,'terminal metadata changed')
     terminal.append(upper)
   if terminal:end=max(terminal)
   life=(end-t).total_seconds();need(math.isfinite(life) and life>=0,'campaign tool clock')
   tool_life+=declared*life;unknown.append(str(p))
 actual_life=sum((e-k[1])/1e7 for k,e in exits.items());open_charge=0.
 for k in set(known)-set(exits):
  need(ft>=k[1],'campaign clock regression');open_charge+=(ft-k[1])/1e7
 charged_starts=len(known)+tool_charge;charged_life=actual_life+open_charge+tool_life
 need(type(reserve_starts) is int and reserve_starts>=0,'campaign reservation')
 need(charged_starts+reserve_starts<=START_LIMIT,'CAMPAIGN_PROCESS_START_LIMIT')
 need(charged_life<=LIFE_LIMIT,'CAMPAIGN_LIFETIME_LIMIT')
 return dict(known_identities=len(known),known_closed=len(exits),actual_covered_lifetime_seconds=actual_life,unresolved_identity_duration_charge_seconds=open_charge,
  infrastructure_start_charge=tool_charge,infrastructure_lifetime_upper_charge_seconds=tool_life,charged_starts=charged_starts,charged_lifetime_seconds=charged_life,
  reserved_next_starts=reserve_starts,task_total_os_ledger='UNKNOWN',scope='Raw PID+creation identities plus conservative tool-root charges; unknown exits never fabricated')
def allocation(root):
 root=Path(root);used=logical=files=dirs=0;copies=0
 if not root.exists():return 0,0,0,0,0
 for parent,ds,fs in os.walk(root,followlinks=False):
  dirs+=len(ds);used+=4096*len(ds)
  for n in ds:
   p=Path(parent)/n;need(not p.is_symlink() and not p.is_junction(),'campaign storage alias')
  for n in fs:
   p=Path(parent)/n;s=p.stat();need(not p.is_symlink() and s.st_nlink==1,'campaign storage alias')
   logical+=s.st_size;used+=((s.st_size+4095)//4096)*4096+1024;files+=1;copies+=n=='RAW_EVIDENCE.zip'
 return used,logical,files,dirs,copies
def storage_check(root,projected_bytes=0):
 root=Path(root).resolve();_,ext=config(root);_,prior_charge=previous(root)
 a=allocation(root);b=allocation(ext);need(type(projected_bytes) is int and projected_bytes>=0,'storage projection')
 used=a[0]+b[0]+prior_charge;copies=a[4]+b[4]
 need(copies<=2,'CAMPAIGN_ARCHIVE_COPY_LIMIT');need(used+projected_bytes+RESERVE+EXPORT<=STORAGE_LIMIT,'CAMPAIGN_STORAGE_RESERVE')
 free=shutil.disk_usage(root).free;need(free>=10*1024**3,'CAMPAIGN_DISK_FREE')
 return dict(allocation_upper_bytes=used,projected_bytes=projected_bytes,reserve_bytes=RESERVE,export_reserve_bytes=EXPORT,charged_upper_bytes=used+projected_bytes+RESERVE+EXPORT,archive_copies=copies,free_disk_bytes=free)
def archive_reservation(root,external,logical,members):
 root=Path(root).resolve();_,owned=config(root);external=Path(external).resolve()
 need(external==owned or owned in external.parents,'unregistered external archive root')
 # Deflate/header allowance, second downloaded archive, encoded transport, complete restored tree.
 bound=logical+(logical//16383+1)*16+members*1024+1024**2
 projected=bound*2+(bound*4+2)//3+allocation(root)[0]+1024**2
 check=storage_check(root,projected);need(check['archive_copies']<2,'CAMPAIGN_ARCHIVE_COPY_LIMIT')
 return dict(**check,archive_bound_bytes=bound,projection_scope='new archive + downloaded archive + Base64 transport + restored allocation; reserve remains untouched')
