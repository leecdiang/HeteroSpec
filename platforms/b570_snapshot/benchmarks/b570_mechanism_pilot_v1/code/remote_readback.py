"""Fresh remote fetch/checkout and every study Git blob + SHA256 check. No models."""
from pathlib import Path
import subprocess,json,time,hashlib,sys
R=Path(__file__).parent;W=Path('C:/Users/DIANG/.codex/worktrees/b570-mechanism-pilot-v1/HeteroSpec');G='C:/Users/DIANG/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe';DIR='benchmarks/b570_mechanism_pilot_v1'
def git(args,cwd):return subprocess.check_output([G,*args],cwd=cwd,text=True,encoding='utf8',errors='strict').strip()
expected=git(['rev-parse','HEAD'],W);branch=git(['branch','--show-current'],W);assert branch=='codex/b570-mechanism-pilot-v1'
scope=git(['diff','--name-status','e87291d26df32f2cb9571e005ab173b1c7a6830b...HEAD'],W).splitlines();assert scope and all(line.startswith('A\t'+DIR+'/') for line in scope)
files=[p for p in (W/DIR).rglob('*') if p.is_file()];max_blob=max(p.stat().st_size for p in files)+1
folder=R/'archive'/('remote-readback-'+str(time.time_ns()));folder.mkdir(parents=True)
subprocess.run([G,'init'],cwd=folder,check=True,stdout=subprocess.DEVNULL)
subprocess.run([G,'config','core.autocrlf','false'],cwd=folder,check=True)
subprocess.run([G,'remote','add','origin','https://github.com/leecdiang/HeteroSpec.git'],cwd=folder,check=True)
subprocess.run([G,'fetch','--depth=1','--filter=blob:limit='+str(max_blob),'origin',branch],cwd=folder,check=True)
actual=git(['rev-parse','FETCH_HEAD'],folder);assert actual==expected
subprocess.run([G,'restore','--source=FETCH_HEAD','--staged','--worktree','--',DIR],cwd=folder,check=True)
tree=git(['ls-tree','-r','FETCH_HEAD','--',DIR],folder).splitlines();readback={}
for line in tree:
 meta,name=line.split('\t',1);mode,kind,blob=meta.split();assert kind=='blob';p=folder/name;b=p.read_bytes();intended=(W/name).read_bytes();assert b==intended
 actual_blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();assert actual_blob==blob
 readback[name]=dict(git_blob=blob,sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
assert len(readback)==len(files)
receipt=dict(status='PASS',head=actual,base='e87291d26df32f2cb9571e005ab173b1c7a6830b',branch=branch,files=len(readback),restored=str(folder),fresh_remote_fetch_checkout=True,all_git_blob_and_byte_SHA256_verified=True,only_additive_new_directory=True,source_scope=scope,readback=readback,no_model_requests=True)
(R/'REMOTE_READBACK.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8');print('REMOTE VERIFIED',actual,len(readback),flush=True)
