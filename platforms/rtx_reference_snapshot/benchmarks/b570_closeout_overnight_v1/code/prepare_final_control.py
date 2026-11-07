"""Run only after old G0 exits: freeze precise timers and durable controller tools."""
from pathlib import Path
import json,subprocess,sys,shutil,hashlib
ROOT=Path(__file__).parent
DEPS=ROOT/'dependencies/B570';DEPS.mkdir(parents=True,exist_ok=True)
shutil.copy2('C:/hs/b570-prefill-v1/artifacts/b570_prefill_diagnostic_v1/evaluation/HISTORICAL_EXPECTED.json',DEPS/'HISTORICAL_EXPECTED.json')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8',newline='\n')
assert not (ROOT/'LOCK.json').exists(),'Do not mutate or compile during G0'
assert json.loads((ROOT/'G0.json').read_text())['status']=='PASS'
snapshot=ROOT/'engineering-g0-build-v1';snapshot.mkdir(exist_ok=False)
for p in list((ROOT/'src').glob('*'))+list((ROOT/'build/Release').glob('*.exe')):shutil.copy2(p,snapshot/p.name)
save(snapshot/'BUILD_IDENTITY.json',{'files':{p.name:sha(p) for p in snapshot.iterdir() if p.is_file()},'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'stages':['G0','G0_BRIDGE'],'note':'Preserves the exact old G0 executable/source identity before timer/flush-only rebuild.'})
p=ROOT/'derive_frontends.py';s=p.read_text(encoding='utf-8')
anchor='    // target model sampling context (reuse the llama_context\'s sampling instance)'
insert="s=rep(s,'    const auto t_dec_start = ggml_time_us();','')\ns=rep(s,"+repr(anchor)+",'    const auto t_dec_start = ggml_time_us();\\n'+"+repr(anchor)+")\n"
assert s.count("(OUT/'native.cpp').write_text(s,newline='\\n')")==1
s=s.replace("(OUT/'native.cpp').write_text(s,newline='\\n')",insert+"(OUT/'native.cpp').write_text(s,newline='\\n')")
assert s.count("(OUT/'target.cpp').write_text(t,newline='\\n')")==1
s=s.replace("(OUT/'target.cpp').write_text(t,newline='\\n')","t=rep(t,'    if (!out) return 10;','    if (!out) return 10;\\n    out.close();')\n(OUT/'target.cpp').write_text(t,newline='\\n')")
# Initialization-only detail logs certify device and complete offload; restore level3 before requests.
marker="(OUT/'native.cpp').write_text(s,newline='\\n')"
s=s.replace(marker,"s=rep(s,'    // init llama.cpp','    common_log_set_verbosity_thold(4);\\n    // init llama.cpp')\ns=rep(s,'    std::cout << \"HS_READY\\\\n\" << std::flush;','    common_log_set_verbosity_thold(3);\\n    std::cout << \"HS_READY\\\\n\" << std::flush;')\n"+marker)
marker="(OUT/'target.cpp').write_text(t,newline='\\n')"
s=s.replace(marker,"t=rep(t,'#include <limits>','#include <limits>\\n#include \"log.h\"')\nt=rep(t,'    llama_backend_init();','    common_log_set_verbosity_thold(4);\\n    llama_backend_init();')\nt=rep(t,'    std::cout<<\"HS_READY\\\\n\"<<std::flush;','    common_log_set_verbosity_thold(3);\\n    std::cout<<\"HS_READY\\\\n\"<<std::flush;')\n"+marker)
p.write_text(s,encoding='utf-8',newline='\n')
subprocess.run([sys.executable,str(p)],check=True)
subprocess.run(['C:/Program Files/CMake/bin/cmake.exe','--build',str(ROOT/'build'),'--config','Release','--parallel','2'],check=True)
old=(snapshot/'native.cpp').read_text(encoding='utf-8');new=(ROOT/'src/native.cpp').read_text(encoding='utf-8')
def math_lines(s):return [l for l in s.splitlines() if l.strip() and 'const auto t_dec_start =' not in l and 'common_log_set_verbosity_thold' not in l and l!='#include "log.h"']
assert math_lines(old)==math_lines(new)
assert math_lines((snapshot/'target.cpp').read_text(encoding='utf-8').replace('    if (!out) return 10;','    if (!out) return 10;\n    out.close();'))==math_lines((ROOT/'src/target.cpp').read_text(encoding='utf-8'))
assert (snapshot/'observer.h').read_bytes()==(ROOT/'src/observer.h').read_bytes()
runner=ROOT/'runner.py';s=runner.read_text()
anchor='  self.load_seconds=time.monotonic()-start'
assert s.count(anchor)==1;s=s.replace(anchor,anchor+'\n  save(self.dir/\'SESSION_LOAD.json\',dict(utc=now(),model_and_context_load_seconds=self.load_seconds,scope="Excluded cold session initialization before HS_READY; explicit warm request follows"))')
s=s.replace(' def close(self):\n',' def close(self):\n  cleanup_start=time.monotonic()\n')
s=s.replace('  self.err.close();self.out.close()','  self.err.close();self.out.close()\n  save(self.dir/\'SESSION_CLOSE.json\',dict(utc=now(),process_exit_code=self.p.poll(),model_session_cleanup_seconds=time.monotonic()-cleanup_start,scope="Excluded session teardown after last complete request; continuation context cleanup is inside whole-request timer"))')
runner.write_text(s,encoding='utf-8',newline='\n')
save(ROOT/'TIMER_AMENDMENT.json',{'reason':'Before any new MBPP forward, include native sampler/batch initialization in generation timer; close target auxiliary evidence stream before exposing HS_RESULT. No math, model, sampler rules, state, backend or decode call changed. Exact source diff assertions passed. Fresh G0 sham/bridge/width controls run after rebuild.','generation_timer':'Before sampler/batch setup following prefill, through pending source sample+actual state transfer, native draft/verification/rollback and terminal real device synchronization','old_G0_build':str(snapshot),'new_assets':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in list((ROOT/'src').glob('*'))+list((ROOT/'build/Release').glob('*.exe'))}})
raw=[json.loads(p.read_text()) for p in (ROOT/'raw').glob('*/RESULT.json')]
save(ROOT/'G0_ACCOUNTING.json',{'planned_nonwarm':164,'complete_nonwarm':sum(not r['warm'] for r in raw if r['unit_id'].startswith(('G0/','G0_BRIDGE/'))),'planned_warm':10,'actual_complete_warm':sum(r['warm'] for r in raw if r['unit_id'].startswith(('G0/','G0_BRIDGE/'))),'extra_recovery_warm':'Resume created a new owned session; old warmups retained, never hidden. G0.json warm field is original planned count, this receipt accounts actual records.'})
subprocess.run(['git','add','*.py','src','DERIVATION.json','TIMER_AMENDMENT.json','G0_ACCOUNTING.json','.gitignore'],cwd=ROOT,check=True)
subprocess.run(['git','commit','-m','Freeze final timer-only wrapper and durable finite pipeline before new-input qualification'],cwd=ROOT,check=True)
