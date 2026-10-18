"""Prospective tool-observer correction before any qualification/formal block."""
import shutil
from pathlib import Path
from common import V,load,save,sha
from prepare_rtx import root
from runner import git,utc
r=root();assert not (r/'qualification_STARTED.json').exists();assert not (r/'WORKER.lock').exists()
assert not git('status','--porcelain','--untracked-files=no','--',str(V))
original=load(r/'FREEZE.json');dest=r/'SOURCE_REPAIR1';dest.mkdir()
files=[p for p in V.iterdir() if p.suffix in ['.py','.h','.cpp','.txt']]+[V/'build/collector.exe',V/'build/address_cpu.exe']
for p in files:shutil.copyfile(p,dest/p.name)
f=dict(original,commit=git('rev-parse','HEAD'),utc=utc(),files={p.name:sha(p) for p in files},source_subdir=dest.name,native_sha256=sha(V/'build/collector.exe'),previous_freeze_sha256=sha(r/'FREEZE.json'),scope='CUPTI observer invalid symbolName field access removed;no numerical/graph/input/runtime change;references and OFF capability retained with original identities;no formal work existed')
save(r/'FREEZE_REPAIR1.json',f)
save(r/'TOOL_REPAIR1.json',dict(reason='First ON capability host access violation during CUDA initialization before GRAPH/INITIALIZED;no graph_compute reached. Observer read symbolName outside documented launch callbacks. Candidate correction removes this unsupported field access;causality still pending actual verification.',old_failure='attempts/capability-ON-QB',old_failure_receipt_sha256=sha(r/'attempts/capability-ON-QB/ENDED.json'),old_freeze_sha256=sha(r/'FREEZE.json'),new_freeze_sha256=sha(r/'FREEZE_REPAIR1.json'),formal_hosts_before_repair=0,confirmed_graph_calls_in_failed_host=0,not_a_scientific_retry=True))
print('TOOL REPAIR FREEZE',sha(r/'FREEZE_REPAIR1.json'))
