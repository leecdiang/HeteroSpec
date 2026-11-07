"""CPU-only delivery closure; no new native, GPU, readiness or controller start."""
import datetime, hashlib, json, shutil, subprocess, zipfile
from pathlib import Path

D=Path(__file__).resolve().parent
V=D.parent
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def size(p):return sum(x.stat().st_size for x in p.rglob('*') if x.is_file())
f0=load(V/'F0.json');root=Path(f0['execution_root'])
auth=load(D/'AUTHENTICATED_CENSUS.json')
assert auth==load(root/'CENSUS_AUTHENTICATED.json')
assert auth['authenticated_remote_bytes'] and auth['numerical_authorization']=='NOT_GRANTED'
assert auth['data_commit']=='c96215d8856198ff99ab7228b31187d391a5a2fc'
assert auth['F0_sha256']==sha(V/'F0.json')
assert auth['census_sha256']==sha(root/'census/native/CENSUS.json')
assert auth['decision_sha256']==sha(root/'CENSUS_DECISION.json')
assert not (root/'numerical').exists() and not (root/'ACTIVE_CONTROLLER.lock').exists()
assert not (V/'execution_ledger/NUMERICAL_CONTROLLER_STARTED.json').exists()
assert load(D/'FINAL_OWNED_PROCESS_INVENTORY.json')==[]
manifest=load(V/'census_readback/MANIFEST.json')
with zipfile.ZipFile(V/'census_readback/CENSUS_RAW.zip') as z:
    assert {m['path'] for m in manifest['members']}==set(z.namelist())
    for m in manifest['members']:
        b=z.read(m['path']);assert len(b)==m['bytes'] and hashlib.sha256(b).hexdigest()==m['sha256']
assert sha(V/'census_readback/CENSUS_RAW.zip')==sha(V/'census_delivery/CENSUS_RAW.zip')==manifest['sha256']
for key,where in [('census_sha256','census/native/CENSUS.json'),('decision_sha256','CENSUS_DECISION.json')]:
    with zipfile.ZipFile(V/'census_readback/CENSUS_RAW.zip') as z:
        assert hashlib.sha256(z.read(where)).hexdigest()==auth[key]
changed=subprocess.check_output(['git','diff',auth['data_commit'],'--name-only'],cwd=V).decode().splitlines()
assert all(p.startswith('benchmarks/rtx_lowering_envelope_v1/formal_numerical_v2/') for p in changed)
since_review=subprocess.check_output(['git','diff','05912d0b10191b861af5cdb85333f1d963dba294','--name-only'],cwd=V.parent.parent.parent).decode().splitlines()
assert all(p.startswith('benchmarks/rtx_lowering_envelope_v1/formal_numerical_v2/') for p in since_review)
# Copy the failed transport receipt into its preserved (originally empty) target;
# this is not a reset of the scientific root/ledger or modification of old evidence.
shutil.copyfile(D/'READBACK_001_FAILED.json',D/'readback_001_wrong_commit/FAILURE.json')
receipt=dict(recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),data_commit=auth['data_commit'],authenticated=auth,remote_archive_verified_members=len(manifest['members']),all_member_hashes_and_actual_decision_reconstructed=True,scientific_reruns=0,CPU_readback_attempts=2,first_readback_failure='Mistyped commit, HTTP404, zero files received; preserved separately.',formal_numerical_slots_started=0,numerical_authorization='NOT_GRANTED',historical_old720='1failed/719unstarted/0completed; archive unchanged',historical_GPU14='14completed/0failed; archive unchanged',root_logical_bytes_at_closure=size(root),census_archive_local_bytes=(V/'census_delivery/CENSUS_RAW.zip').stat().st_size,census_archive_download_bytes=(V/'census_readback/CENSUS_RAW.zip').stat().st_size,no_active_owned_experimental_processes=True,scientific_execution_complete_for_approved_census_only=True,later_stages_not_started=True,line_endings_note='Original PowerShell controller/launch and CSV evidence uses CRLF. git diff --check reports CR as whitespace with this repo configuration; evidence bytes retained, not normalized. No execution/source failure.',delivery_cost_scope='CPU hashing, Git, authenticated HTTP/archive reconstruction and receipt tooling are delivery operations, separate from the already ended census owned-process envelope.')
with (D/'CLOSURE.json').open('x',encoding='utf-8',newline='\n') as out:json.dump(receipt,out,ensure_ascii=False,indent=2);out.write('\n')
print('Closure verified: authenticated census-only; no numerical/controller restart; no active owned experimental process.')
