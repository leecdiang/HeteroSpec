"""Derive verified prior compile driver; no native executable is ever run."""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--producer-build',type=Path,required=True);a=p.parse_args();here=Path(__file__).resolve().parent;old=here.parent/'admission_controller_20261112';source=old/'build_descendant.py'
 if sha(source)!='684a0724455ad8961cf8a6e477707f184910549035a7ec4521ccab444c1804ff':raise SystemExit('Complete previous native builder changed')
 if a.out.exists():raise SystemExit('Fresh complete bridge-native build epoch required')
 driver=a.out.parent/(a.out.name+'-bridge-driver');driver.mkdir(parents=True)
 text=source.read_text();replacements=[('from make_worker_descendant import derive','from generate_native_worker import derive'),('here = Path(__file__).resolve().parent','here = Path('+repr(str(here))+')'),("worker, worker_receipt = derive(pinned / 'native/worker.cpp')","worker, worker_receipt = derive(here.parent / 'admission_controller_20261112/native/worker.cpp')"),("'ControlledNativeClient','controller_io'","'BridgeClient','bridge_io'"),("here / 'native_client.hpp'","here / 'bridge_client.hpp'")]
 for oldtext,new in replacements:
  matches=text.count(oldtext)
  if matches!=(2 if oldtext=="here / 'native_client.hpp'" else 1):raise SystemExit('Exact native builder adaptation changed: '+oldtext)
  text=text.replace(oldtext,new)
 program=driver/'build_driver.py';program.write_text(text);env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONPATH=str(here));cmd=[sys.executable,'-B',str(program),'--host-root',str(a.host_root),'--out',str(a.out),'--producer-build',str(a.producer_build)]
 with (driver/'STDOUT_STDERR.log').open('w') as log:r=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=600)
 if r.returncode:raise SystemExit('Native bridge compile/link failed; complete epoch retained')
 receipt=json.loads((a.out/'CONTROLLER_BUILD.private.json').read_text());receipt['bridge_sources']=[{'file':name,'bytes':(here/name).stat().st_size,'sha256':sha(here/name)} for name in ['bridge_client.hpp','bridge_job.hpp','generate_native_worker.py','cpp_bridge_launcher.cpp','supervisor.hpp']]
 # Compile a separate genuine native launcher with the two exact compiled image
 # identities. Its permanent default gate precedes JSON/FD/fork/exec. Never run.
 artifacts={x['role']:x for x in receipt['artifacts']};exe=a.out/'native_bridge_launcher_NOT_ADMITTED';include=a.host_root/'run-01/stage-03/sources/reference/vendor';flags=['/usr/bin/g++','-std=c++17','-O0','-g','-fno-lto','-fno-inline','-I'+str(include),'-DHS_NATIVE_R_SHA="'+artifacts['R']['executable_sha256']+'"','-DHS_NATIVE_LOOP4_SHA="'+artifacts['loop4']['executable_sha256']+'"',str(here/'cpp_bridge_launcher.cpp'),'-o',str(exe)]
 commands=[flags,['readelf','-d',str(exe)],['nm','-C',str(exe)]]
 for cmd,name in zip(commands,['native-launcher-compile.log','native-launcher-readelf.log','native-launcher-symbols.log']):
  with (a.out/name).open('w') as log:r=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120)
  if r.returncode:raise SystemExit('Native launcher compile/static inspection failed; retained')
 receipt['genuine_native_launcher']={'bytes':exe.stat().st_size,'sha256':sha(exe),'executed':False,'CPU_bypass_compiled':False,'source_image_SHA_pins':{k:v['executable_sha256'] for k,v in artifacts.items()},'commands':commands};(a.out/'BRIDGE_BUILD.private.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':'GENUINE_NATIVE_BRIDGE_COMPILED_LINKED_NOT_EXECUTED','native_executables_started':0,'artifacts':[{'role':v['role'],'sha256':v['executable_sha256']} for v in receipt['artifacts']],'launcher_sha256':sha(exe)}))

if __name__=='__main__':main()
