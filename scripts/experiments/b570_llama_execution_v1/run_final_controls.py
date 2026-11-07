"""Final-binary operator coverage, unchanged historical Qwen audit, and probes."""
from pathlib import Path
import importlib.util,subprocess,sys,shutil
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import read,write,need,sha
from operator_host import run as operators
from qwen_host import run as qwen

root=Path(sys.argv[1]);repo=Path(sys.argv[2]);epoch=Path(sys.argv[3]);code=Path(__file__).parent
operators(root/'projection-widths-build-00/BUILD.json',root/'projection-widths-plan-00/CONFIG.json',root/'projection-widths-replay-00',root/'research',Path('C:/hs/b570-llama-exclusive.lock'),1200)
subprocess.run([sys.executable,'-B',str(code/'audit_projection_widths.py'),str(root/'projection-widths-replay-00'),str(root/'FINAL_PROJECTION_WIDTHS_AUDIT-00.json')],check=True)
auditor=repo/'benchmarks/b570_native_reproduction_v1/audit_request.py';spec=importlib.util.spec_from_file_location('original_qwen_audit',auditor);original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
references=root/'qwen-original-reference';need(not references.exists(),'fresh original Qwen reference copy');references.mkdir();shutil.copyfile(auditor,references/'audit_request.py')
for i in range(4):shutil.copytree(Path(f'C:/hs/b570-native-reproduction-20261026/smoke-{i}-a1'),references/f'smoke-{i}-a1')
write(references/'REFERENCE_COPY.json',{'original_auditor_sha256':sha(auditor),'files':[{'path':p.relative_to(references).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(references.rglob('*')) if p.is_file()],'scope':'Immutable retained original Qwen reference copied for portable raw reconstruction; original host directories unchanged.'})
out=root/'qwen-combined-regression-00';build=root/'qwen-combined-adapter-build-01/BUILD.json';qwen(build,repo,root/'research',out/'admission','admit',0)
for i in range(4):
    qwen(build,repo,root/'research',out/f'input-{i}','qual',i)
    proof=original.audit(out/f'input-{i}/native',references/f'smoke-{i}-a1');proof['original_auditor_sha256']=sha(auditor);write(root/f'QWEN_FINAL_AUDIT-0{i}.json',proof)
subprocess.run([sys.executable,'-B',str(code/'run_combined_probes.py'),str(root),str(epoch)],check=True)
write(root/'FINAL_PREFREEZE_CONTROLS-00.json',{'status':'FINAL_NATIVE_CONTROLS_PASS','evidence':[{'path':str(root/name),'sha256':sha(root/name)} for name in ['FINAL_PROJECTION_WIDTHS_AUDIT-00.json','COMBINED_PROBE_AUDIT-00.json']+[f'QWEN_FINAL_AUDIT-0{i}.json' for i in range(4)]],'same_numerical_candidate_build_sha256':sha(root/'candidate-combined-02/BUILD.json')})
