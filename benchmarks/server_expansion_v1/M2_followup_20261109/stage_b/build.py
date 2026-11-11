"""Relink only a diagnostic frontend against the hash-bound M2 archives."""
from pathlib import Path
import argparse,json,hashlib,shutil,subprocess,time
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
def main():
 a=argparse.ArgumentParser();a.add_argument('--root',type=Path,required=True);a.add_argument('--out',type=Path,required=True);x=a.parse_args()
 old=x.root/'m2-build-01';x.out.mkdir();front=x.out/'frontend';shutil.copytree(old/'frontend',front)
 text=(front/'entry.cpp').read_text();assert text.count('int main(int argc,char**argv)')==1
 (front/'entry.cpp').write_text(text[:text.index('int main(int argc,char**argv)')]+Path(__file__).with_name('equalwork_main.cpp').read_text())
 verified=set()
 for core in ('loop4','packed'):
  src=old/core;dest=x.out/core;dest.mkdir();b=read(src/'BUILD.json');deps=read(src/'DEPENDENCIES.json')
  assert sha(b['executable'])==b['executable_sha256']
  for p,h in deps['files'].items():
   if p not in verified:assert sha(p)==h,p;verified.add(p)
  for phase in ('compile','link'):
   prior=read(src/phase/'command.json');args=[s.replace(str(old),str(x.out)) for s in prior['argv']]
   started=time.monotonic();r=subprocess.run(args,cwd=prior['cwd'],capture_output=True,text=True)
   d=dest/phase;d.mkdir();(d/'stdout.log').write_text(r.stdout);(d/'stderr.log').write_text(r.stderr)
   save(d/'command.json',dict(argv=args,cwd=prior['cwd'],returncode=r.returncode,wall_s=time.monotonic()-started));assert r.returncode==0,(phase,r.stderr)
  names={p:h for p,h in deps['files'].items() if not Path(p).is_relative_to(old)}
  for p in front.rglob('*'):
   if p.is_file():names[str(p)]=sha(p)
  for p in (dest/'frontend.d',dest/'frontend.o',dest/'transfer-worker.map'):names[str(p)]=sha(p)
  save(dest/'DEPENDENCIES.json',{**deps,'files':names,'read_only_parent_build_sha256':sha(src/'BUILD.json')})
  save(dest/'BUILD.json',{**b,'executable':str(dest/'transfer-worker'),'executable_sha256':sha(dest/'transfer-worker'),
       'dependency_closure_sha256':sha(dest/'DEPENDENCIES.json'),'status':'EQUALWORK_DIAGNOSTIC_NOT_YET_QUALIFIED','frontend':{str(p.relative_to(front)):sha(p)for p in front.rglob('*')if p.is_file()},'parent_build_sha256':sha(src/'BUILD.json')})
  print('BUILT',core,sha(dest/'transfer-worker'),flush=True)
 save(x.out/'COMPLETE.json',dict(passed=True,numerical_archives_changed=False,originals_modified=False))
if __name__=='__main__':main()
