#!/usr/bin/env python3
import argparse,pathlib,subprocess,json,hashlib,time,sys
R=pathlib.Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=pathlib.Path,required=True);p.add_argument('--library-dir',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();a.output.mkdir(exist_ok=False,parents=True);s=a.source.resolve();l=a.library_dir.resolve();o=a.output.resolve()
 cmd=['g++','-std=c++17','-O2']+['-I'+str(s/x) for x in ['include','ggml/include','vendor']]+[str(R/'src/bridge.cpp'),'-L'+str(l),'-Wl,-rpath,'+str(l),'-lllama','-lggml','-lggml-base','-o',str(o/'bridge')]
 r={'command':cmd,'compiler':subprocess.check_output(['g++','--version'],text=True),'sources':{str(x.relative_to(R)):sha(x) for x in [R/'src/bridge.cpp',R/'src/pinned_fixture.cpp']},'libraries':{str(x.resolve()):sha(x) for x in l.glob('*.so')},'status':'STARTED'};(o/'build.json').write_text(json.dumps(r,indent=2));t=time.monotonic()
 with (o/'compile.log').open('w') as f:c=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 r.update(returncode=c.returncode,wall_seconds=time.monotonic()-t,status='PASS' if c.returncode==0 else 'FAILED')
 if c.returncode==0:r['binary_sha256']=sha(o/'bridge')
 (o/'build.json').write_text(json.dumps(r,indent=2)+'\n');sys.exit(c.returncode)
