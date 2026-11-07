"""Keep the failed unapproved lock; normalize Windows/POSIX manifest keys."""
from common import ROOT, load, save, sha, modules
before=modules();path=ROOT/'host/S1_F0.json';draft=load(path)
assert draft['status']=='AWAITING_EXPLICIT_AUTHOR_APPROVAL' and not (ROOT/'host_outputs/S1_RUN').exists()
path.rename(ROOT/'host/S1_F0_DRAFT_01.json')
draft['sources']={name.replace('\\','/'):sha(ROOT/name.replace('\\','/')) for name in draft['sources']}
draft['supersedes_unapproved_draft_sha256']=sha(ROOT/'host/S1_F0_DRAFT_01.json')
draft['source_lock_note']='Normalize all manifest keys to repository-relative POSIX paths; retain failed unapproved drafts and gate-test failure. No input/binary/graph/budget change.'
save(path,draft)
(ROOT/'host/S1_EXECUTION_READINESS.json').rename(ROOT/'host/S1_READINESS_DRAFT_01.json')
save(ROOT/'host/S1_EXECUTION_READINESS.json',dict(F0_sha256=sha(path),unapproved_draft=draft['supersedes_unapproved_draft_sha256'],
    operator_host_binary=draft['executable'],input_count=16,actor_compiled=load(ROOT/'host/ACTOR_REPAIR_01.json')['success'],
    S1_executable_launched=False,operator_hosts_started=0,device_queries=0,GPU_operators=0,model_requests=0,
    modules_before=before,modules_after=modules()))
print(dict(F0_sha256=sha(path),operator_hosts_started=0))
