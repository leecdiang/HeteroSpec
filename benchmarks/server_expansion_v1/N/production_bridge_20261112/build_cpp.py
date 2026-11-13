"""Compile/inspect the fixed std-only CPU bridge pair; execute neither here."""
import argparse,hashlib,json,os,re,subprocess,time
from pathlib import Path

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reference-source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 if a.out.exists():raise SystemExit('Fresh build epoch required; do not overwrite')
 here=Path(__file__).resolve().parent;a.out.mkdir(parents=True);commands=[];start=time.monotonic();env=dict(os.environ,CUDA_VISIBLE_DEVICES='')
 def run(cmd,name):
  commands.append(cmd)
  with (a.out/name).open('w') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,env=env,timeout=120)
  if r.returncode:raise SystemExit('Compile/inspect failure retained: '+str(a.out/name))
 jsonheader=a.reference_source/'vendor/nlohmann/json.hpp'
 if not jsonheader.is_file():raise SystemExit('Pinned reference JSON header missing')
 flags=['-std=c++17','-O2','-Wall','-Wextra','-I'+str(a.reference_source/'vendor')]
 compiler='/usr/bin/g++';worker=a.out/'cpp_fixed_worker';launcher=a.out/'cpp_bridge_launcher'
 run([compiler]+flags+[str(here/'cpp_fixed_worker.cpp'),'-o',str(worker)],'worker-compile.log')
 worker_sha=sha(worker)
 run([compiler]+flags+['-DHS_FIXED_CPU_WORKER_SHA="'+worker_sha+'"',str(here/'cpp_bridge_launcher.cpp'),'-o',str(launcher)],'launcher-compile.log')
 artifacts=[]
 for role,exe in [('FIXED_STD_CPU_WORKER',worker),('FIXED_STD_CPU_LAUNCHER',launcher)]:
  run(['readelf','-d',str(exe)],role+'-readelf.log');dynamic=(a.out/(role+'-readelf.log')).read_text();needed=re.findall(r'Shared library: \[([^]]+)\]',dynamic)
  if not needed or set(needed)-{'libstdc++.so.6','libgcc_s.so.1','libc.so.6','libm.so.6'}:raise SystemExit('Untrusted native/model dependency; no execution permitted')
  run(['nm','-D','--undefined-only',str(exe)],role+'-imports.log');symbols=(a.out/(role+'-imports.log')).read_text()
  if re.search(r'\b(?:llama_|ggml_|cuda[A-Z]|cuInit\b|dlopen\b)',symbols):raise SystemExit('Native/loader import in fixed CPU artifact')
  artifacts.append({'role':role,'bytes':exe.stat().st_size,'sha256':sha(exe),'NEEDED':needed,'executed_by_builder':False})
 sources=[here/x for x in ['bridge_client.hpp','bridge_job.hpp','supervisor.hpp','cpp_fixed_worker.cpp','cpp_bridge_launcher.cpp','build_cpp.py']]
 receipt={'schema':'hs.production-bridge.fixed-CPU-build.v1','status':'COMPILED_LINKED_INSPECTED_NOT_EXECUTED','artifacts':artifacts,'fixed_worker_sha256_embedded_in_launcher':worker_sha,'source_files':[{'file':x.name,'bytes':x.stat().st_size,'sha256':sha(x)} for x in sources],'pinned_JSON_header':{'bytes':jsonheader.stat().st_size,'sha256':sha(jsonheader)},'commands':commands,'elapsed_s':time.monotonic()-start,'actual_model_backend_GPU_context_placement_forward_calls':0,'executables_started':0}
 (a.out/'BUILD.private.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items() if k in ('status','artifacts','elapsed_s','executables_started')}))

if __name__=='__main__':main()
