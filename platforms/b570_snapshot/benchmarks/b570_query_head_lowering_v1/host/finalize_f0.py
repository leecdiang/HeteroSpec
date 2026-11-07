"""Prospectively complete transitive source locks before any author approval."""
import pathlib, subprocess
from common import ROOT, load, save, sha, modules

before=modules();f=ROOT/'host/S1_F0.json';old=load(f);assert old['status']=='AWAITING_EXPLICIT_AUTHOR_APPROVAL'
assert not (ROOT/'host_outputs/S1_RUN').exists()
f.rename(ROOT/'host/S1_F0_DRAFT_00.json')
for path in ['native/host/oracle.hpp','native/host/CMakeLists.txt','host/common.py','host/run_s0.py','host/prepare_s1.py']:
    old['sources'][path]=sha(ROOT/path)
old['supersedes_unapproved_draft_sha256']=sha(ROOT/'host/S1_F0_DRAFT_00.json')
old['source_lock_note']='Complete transitive executor/oracle/build-helper locks before first approval; input/plan/executable/dependency/limits unchanged.'
save(f,old)
save(ROOT/'host/S1_EXECUTION_READINESS.json',dict(F0_sha256=sha(f),unapproved_draft=old['supersedes_unapproved_draft_sha256'],
    operator_host_binary=old['executable'],input_count=16,actor_compiled=load(ROOT/'host/ACTOR_REPAIR_01.json')['success'],
    S1_executable_launched=False,operator_hosts_started=0,device_queries=0,GPU_operators=0,model_requests=0,
    modules_before=before,modules_after=modules()))
print(dict(final_F0_sha256=sha(f),operator_hosts_started=0))
