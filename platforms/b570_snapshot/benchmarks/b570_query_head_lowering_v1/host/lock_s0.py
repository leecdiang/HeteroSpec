"""Freeze the unchanged real CPU executable before q3/q4 fixture outputs."""
import datetime
from common import ROOT, load, save, sha, modules

before=modules();r=load(ROOT/'host/S0_DEVELOPMENT_RECEIPT.json')
assert r['returncode']==0 and r['completed_fixtures']==216
bound=load(ROOT/'host/HOST_SOURCE_BINDINGS.json')
for name,digest in bound['harness_sources'].items():assert sha(ROOT/name)==digest
assert sha(ROOT/'build/Release/qh-real.exe')==bound['numerical_harness_sha256']==r['exe_sha256']
save(ROOT/'host/HOST_RULE_LOCK.json',dict(timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),development_commit=r['commit'],development_complete=216,
    executable_sha256=r['exe_sha256'],harness_sources=bound['harness_sources'],
    inputs_source_sha256=sha(ROOT/'host/inputs.py'),candidate_sha256=sha(ROOT/'native/query_head.h'),
    fixture_plan_sha256=sha(ROOT/'plan.py'),integration_revisions=0,
    validation_scope='q3/q4 fixture outputs after lock; shapes already exposed by delivered toy tests. Same real CPU executable as development.',
    transport_note='Preserve original CRLF bytes of three reused source files via -text; no arithmetic/source/binary rebuild.',
    modules_before=before,modules_after=modules(),GPU_starts=0))
print(dict(development_complete=216,locked=True))
