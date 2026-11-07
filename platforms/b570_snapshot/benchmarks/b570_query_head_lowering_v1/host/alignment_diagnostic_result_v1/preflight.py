"""Read-only admission receipt for the exact approved diagnostic; no device APIs."""
import datetime
import json
import os
import pathlib
import subprocess
import sys
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'host'))
from common import load,save,sha,modules

COMMIT='47ea26a3f406372eb4956955e6b973ef6874b3ad'
APPROVED='7a99f5b8e1c06051a6c916e5999201304bd6724ba0a49228f95d765e1b45ce3e'
before=modules();review=ROOT/'host/alignment_review_v1'
git='C:/hs/pr108-tools/git/cmd/git.exe'
head=subprocess.check_output([git,'-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()
assert head==COMMIT,'reviewed checkout changed'
assert not subprocess.check_output([git,'-C',str(ROOT),'diff','--name-only','HEAD'],text=True).strip(),'tracked worktree changed'
assert sha(review/'DIAGNOSTIC_F0.json')==APPROVED
f0=load(review/'DIAGNOSTIC_F0.json')
source_rows=[]
for name,digest in f0['sources'].items():
    actual=sha(ROOT/name);assert actual==digest,'source drift '+name
    source_rows.append(dict(path=name,sha256=actual))
runtime_rows=[]
for item in [f0['executable']]+f0['dependencies']+f0['driver_files']:
    actual=sha(item['path']);assert actual==item['sha256'],'runtime/driver drift '+item['path']
    runtime_rows.append(dict(path=item['path'],sha256=actual))
environment={k:v for k,v in sorted(os.environ.items()) if k.startswith(('GGML_','VK_','LLAMA_'))}
assert environment==f0['environment'],'backend environment drift'
assert sha(review/'DIAGNOSTIC_PLAN.json')==f0['plan_sha256']
slots=load(review/'DIAGNOSTIC_PLAN.json')['slots'];assert len(slots)==7
for s in slots:assert sha(s['input'])==s['input_sha256'],'input drift'
assert not (ROOT/'host_outputs/alignment_review_v1/DIAGNOSTIC_RUN').exists(),'existing run; do not resume'
process_read=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',
    'Get-Process | Select-Object Id,ProcessName,Path | ConvertTo-Json -Depth 2 -Compress'],capture_output=True,text=True,timeout=20)
assert process_read.returncode==0,'OS process inventory unavailable'
processes=json.loads(process_read.stdout)
needles=('python','llama','b570','qh-vulkan','alignment-','ollama','llmster','lmstudio','comfy','blender','furmark','occt','vulkaninfo','vkcube','benchmark')
conflicts=[p for p in processes if p['Id']!=os.getpid() and any(n in p['ProcessName'].lower() for n in needles)]
receipt=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),approved_commit=COMMIT,F0_sha256=APPROVED,
    sources=source_rows,runtime_and_drivers=runtime_rows,environment=environment,
    plan_sha256=f0['plan_sha256'],input_files_checked=len({s['input'] for s in slots}),all_slots_unstarted=True,
    OS_process_inventory=processes,conflicting_compute_or_benchmark_processes=conflicts,
    conflict_check_scope='Read-only OS process inventory; no GPU utilization, device enumeration, or capability query.',
    original_S1_F0_sha256=sha(ROOT/'host/S1_F0.json'),original_S1_result_sha256=sha(ROOT/'host/S1_RESULT.json'),
    original_S1_raw_sha256=sha(ROOT/'host/S1_RAW.zip'),modules_before=before,modules_after=modules(),new_device_queries=0)
save(HERE/'PREFLIGHT.json',receipt)
assert not conflicts,'potential GPU job conflict; no diagnostic launch'
print(dict(admitted=True,source_files=len(source_rows),runtime_files=len(runtime_rows),new_slots_unstarted=7,conflicting_jobs=0))
