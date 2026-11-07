"""Before new inputs: remove accidental 512-row continuation reservation in T."""
from pathlib import Path
import json,subprocess,sys,shutil,hashlib
from datetime import datetime,timezone
ROOT=Path(__file__).parent
assert not (ROOT/'LOCK.json').exists(),'Wait for old width stage to close its GPU service'
assert not (ROOT/'INPUTS.json').exists(),'Repair must precede new-input freeze'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
backup=ROOT/'engineering-target-reservation-v1';backup.mkdir(exist_ok=False)
for name,path in [('target.cpp',ROOT/'src/target.cpp'),('b570-closeout-target.exe',ROOT/'build/Release/b570-closeout-target.exe'),('G0_WIDTH.json',ROOT/'G0_WIDTH.json')]:shutil.copy2(path,backup/name)
native_before=sha(ROOT/'build/Release/b570-closeout-native.exe')
p=ROOT/'derive_frontends.py';s=p.read_text(encoding='utf-8');marker="(OUT/'target.cpp').write_text(t,newline='\\n')"
assert s.count(marker)==1
insertion="t=rep(t,'    const auto continuation_cp=common_context_params_to_llama(params);','    auto continuation_cp=common_context_params_to_llama(params);\\n    if(std::getenv(\"HS_MATCHED_TARGET\")){continuation_cp.n_outputs_max=1;continuation_cp.n_outputs_max_per_seq=1;}')\n"
s=s.replace(marker,insertion+marker);p.write_text(s,encoding='utf-8',newline='\n')
subprocess.run([sys.executable,str(p)],check=True)
subprocess.run(['C:/Program Files/CMake/bin/cmake.exe','--build',str(ROOT/'build'),'--config','Release','--target','b570-closeout-target','--parallel','2'],check=True)
assert sha(ROOT/'build/Release/b570-closeout-native.exe')==native_before
old=(backup/'target.cpp').read_text(encoding='utf-8');new=(ROOT/'src/target.cpp').read_text(encoding='utf-8')
expected=old.replace('    const auto continuation_cp=common_context_params_to_llama(params);','    auto continuation_cp=common_context_params_to_llama(params);\n    if(std::getenv("HS_MATCHED_TARGET")){continuation_cp.n_outputs_max=1;continuation_cp.n_outputs_max_per_seq=1;}')
assert expected==new
amend={'utc':datetime.now(timezone.utc).isoformat(),'reason':'Matched target captured default continuation params before common initialization reduced per-sequence outputs. Default n_outputs_max=0 resolves to batch512, per_seq=0 resolves512 in a newly created context; a one-query continuation only needs one row. Set matched continuation max/per_seq=1. Ordinary R/source prefill and all native executables remain unchanged. Fresh target plain/sham, old reference and all width controls required before ETA/new inputs.','old_target_sha256':sha(backup/'b570-closeout-target.exe'),'new_target_sha256':sha(ROOT/'build/Release/b570-closeout-target.exe'),'native_unchanged_sha256':native_before,'new_target_source_sha256':sha(ROOT/'src/target.cpp'),'native_source_sha256':sha(ROOT/'src/native.cpp'),'native_binary_unchanged':True,'new_task_forwards':0,'scope':'Actual generation includes all remaining context/state creation costs. No subtraction from recorded times, arithmetic/driver/model change or output retry.'}
(ROOT/'MATCHED_RESERVATION_AMENDMENT.json').write_text(json.dumps(amend,indent=2)+'\n',encoding='utf-8',newline='\n')
subprocess.run(['git','add','derive_frontends.py','src/target.cpp','DERIVATION.json','MATCHED_RESERVATION_AMENDMENT.json','repair_matched_reservation.py','qualify_final_target.py','budget_probe.py'],cwd=ROOT,check=True)
subprocess.run(['git','commit','-m','Freeze one-output matched continuation and required fresh target controls'],cwd=ROOT,check=True)
