from pathlib import Path
import json,hashlib,subprocess,datetime
R=Path(__file__).parent;G='C:/Users/DIANG/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
sources={}
for directory in ['candidate-src','candidate-front','candidate-common']:
 for p in (R/directory).rglob('*'):
  if p.is_file():sources[str(p.relative_to(R)).replace('\\','/')]=sha(p)
for name in ['candidate_runner.py','run_C.py','validate_C.py','C_MANIFEST.json','CANDIDATE_DECISION.json','implement_C.py','prepare_C_runner.py','C_PRIVATE_LIBRARY.patch','C_PRIVATE_SOURCE_MANIFEST.json','DEV_INPUTS.json','HISTORICAL_PARENTS.json','C_PRE_FORWARD_BINDING_AMENDMENT.json','repair_C_link_binding.py']:
 sources[name]=sha(R/name)
binaries={str(p.relative_to(R)).replace('\\','/'):sha(p) for p in (R/'candidate-build/Release').iterdir() if p.suffix in ['.exe','.dll']}
assert len([x for x in binaries if x.endswith('.exe')])==2 and any(x.endswith('llama-b570-pilot.dll') for x in binaries)
freeze=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sources=sources,binaries=binaries,candidate_decision_commit='415a503e4a378e596f970695ec2234d40745097b',forwards_before_freeze=0,one_family=True,private_backend_shader_changes=0,build_config='MSVC19.44 Release x64 C++17 /O2 /MD, isolated llama library, same old ggml/Vulkan DLLs',budget_nonwarm_max=12)
(R/'C_FREEZE.json').write_text(json.dumps(freeze,indent=2)+'\n',encoding='utf8')
subprocess.run([G,'add','candidate-src','candidate-front','candidate-common','candidate_runner.py','run_C.py','validate_C.py','C_MANIFEST.json','CANDIDATE_DECISION.json','implement_C.py','prepare_C_runner.py','C_PRIVATE_LIBRARY.patch','C_PRIVATE_SOURCE_MANIFEST.json','C_FREEZE.json','C_PRE_FORWARD_FREEZE_0.json','C_PRE_FORWARD_BINDING_AMENDMENT.json','repair_C_link_binding.py','freeze_C.py','CPU_TIMER_AUDIT.json','inspect_timers.py','independent_verify.py'],cwd=R,check=True)
subprocess.run([G,'commit','-m','Freeze canonical prefill single-context phase binding candidate and twelve-unit gate'],cwd=R,check=True)
print(subprocess.check_output([G,'rev-parse','HEAD'],cwd=R,text=True).strip())
