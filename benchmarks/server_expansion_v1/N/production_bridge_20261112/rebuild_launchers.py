"""Rebuild only launcher artifacts after host supervisor changes. Never native exec."""
import argparse,hashlib,json,os,re,subprocess
from pathlib import Path
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--worker',type=Path,required=True);p.add_argument('--reference-source',type=Path,required=True);p.add_argument('--native-receipt',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out=a.out.resolve();here=Path(__file__).resolve().parent
 if a.out.exists():raise SystemExit('Fresh launcher-only build epoch required')
 if sha(a.worker)!='8ea68312efbdcf00fbf0c5d58354055a741ea91c4ddb3d9406af18538f2f1295':raise SystemExit('Fixed reviewed CPU worker changed')
 a.out.mkdir(parents=True);env=dict(os.environ,CUDA_VISIBLE_DEVICES='');commands=[]
 def run(cmd,name):
  commands.append(cmd)
  with (a.out/name).open('w') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,env=env,timeout=120)
  if r.returncode:raise SystemExit('Launcher-only compile/test failure retained: '+name)
 base=['/usr/bin/g++','-std=c++17','-Wall','-Wextra','-I'+str(a.reference_source/'vendor')];cpu=a.out/'cpp_bridge_launcher';native=a.out/'native_bridge_launcher_NOT_ADMITTED'
 run(base+['-O2','-DHS_FIXED_CPU_WORKER_SHA="'+sha(a.worker)+'"',str(here/'cpp_bridge_launcher.cpp'),'-o',str(cpu)],'cpu-launcher-compile.log')
 old=json.loads(a.native_receipt.read_text());images={x['role']:x['executable_sha256'] for x in old['artifacts']}
 run(base+['-O0','-g','-fno-inline','-fno-lto','-DHS_NATIVE_R_SHA="'+images['R']+'"','-DHS_NATIVE_LOOP4_SHA="'+images['loop4']+'"',str(here/'cpp_bridge_launcher.cpp'),'-o',str(native)],'native-launcher-compile.log')
 test=a.out/'cpu_supervisor_boundary';run(base+['-O2',str(here/'test_supervisor_boundary.cpp'),'-o',str(test)],'boundary-compile.log');needed={}
 for name,exe in [('CPU',cpu),('NATIVE',native),('BOUNDARY',test)]:
  run(['readelf','-d',str(exe)],name+'-readelf.log');libs=re.findall(r'Shared library: \[([^]]+)\]',(a.out/(name+'-readelf.log')).read_text());needed[name]=libs
  if not libs or set(libs)-{'libstdc++.so.6','libgcc_s.so.1','libc.so.6','libm.so.6'}:raise SystemExit('Unexpected dynamic dependency; no executable run')
 # All three dependency checks precede the only execution: a fixed CPU test.
 run([str(test),str(a.out/'boundary-fixture')],'BOUNDARY-test.log')
 summary=json.loads((a.out/'BOUNDARY-test.log').read_text().strip().splitlines()[-1])
 if summary.get('status')!='CPU_SUPERVISOR_BOUNDARY_PASS' or summary.get('tests')!=4:raise SystemExit('Boundary test mismatch')
 receipt={'schema':'hs.production-bridge.launcher-only-rebuild.v1','status':'COMPILED_INSPECTED_BOUNDARY_CPU_TEST_PASS','fixed_worker':{'path':str(a.worker),'sha256':sha(a.worker),'rebuilt':False},'CPU_launcher':{'bytes':cpu.stat().st_size,'sha256':sha(cpu),'executed_by_builder':False},'native_launcher':{'bytes':native.stat().st_size,'sha256':sha(native),'executed':False},'unchanged_native_worker_pins':images,'NEEDED':needed,'boundary_tests':summary,'commands':commands,'sources':[{'file':n,'bytes':(here/n).stat().st_size,'sha256':sha(here/n)} for n in ['cpp_bridge_launcher.cpp','supervisor.hpp','bridge_job.hpp','bridge_client.hpp','test_supervisor_boundary.cpp','rebuild_launchers.py']],'native_model_backend_context_placement_forward_calls':0}
 (a.out/'BUILD.private.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:receipt[k] for k in ['status','CPU_launcher','native_launcher','boundary_tests']}))
if __name__=='__main__':main()
