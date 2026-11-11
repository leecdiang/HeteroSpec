"""Final file/budget audit only. Never imports or starts the diagnostic runner."""
import datetime
import hashlib
import pathlib
import subprocess
import sys
import zipfile
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'host'))
from common import load,save,sha,modules

before=modules()
review=ROOT/'host/alignment_review_v1'
f0=load(review/'DIAGNOSTIC_F0.json')
assert sha(review/'DIAGNOSTIC_F0.json')=='7a99f5b8e1c06051a6c916e5999201304bd6724ba0a49228f95d765e1b45ce3e'
for name,digest in f0['sources'].items():assert sha(ROOT/name)==digest
for x in [f0['executable']]+f0['dependencies']+f0['driver_files']:assert sha(x['path'])==x['sha256']
old=load(ROOT/'host/S1_RAW_MANIFEST.json')
assert sha(ROOT/'host/S1_RAW.zip')==old['archive_sha256']
for x in old['files']:assert sha(ROOT/'host_outputs/S1_RUN'/x['path'])==x['sha256']
assert sha(ROOT/'host/S1_F0.json')==f0['original_S1_F0_sha256']
assert sha(ROOT/'host/S1_RESULT.json')==f0['original_S1_result_sha256']
for x in load(ROOT/'host/S1_INPUTS.json'):assert sha(x['path'])==x['sha256']
new=load(HERE/'RAW_MANIFEST.json')
assert sha(HERE/'DIAGNOSTIC_RAW.zip')==new['archive_sha256']
run=ROOT/'host_outputs/alignment_review_v1/DIAGNOSTIC_RUN'
for x in new['files']:assert sha(run/x['path'])==x['sha256']
assert sum(p.stat().st_size for p in run.rglob('*') if p.is_file())==new['raw_bytes']
result=load(HERE/'RESULT.json')
assert (result['attempts'],result['completed_numerical_graphs'],result['failed_graphs'],result['unstarted'])==(7,5,2,0)
assert result['owned_wall_s']<=420
git='C:/hs/pr108-tools/git/cmd/git.exe'
assert not subprocess.check_output([git,'-C',str(ROOT),'diff','--name-only','HEAD'],text=True).strip()
bytes_before=sum(p.stat().st_size for p in HERE.rglob('*') if p.is_file())+new['raw_bytes']
# A conservative <=64KiB allowance for this last receipt avoids a self-referential
# file-size total. Both the run and its copied archive/derived evidence are counted.
conservative_total=bytes_before+65536
assert conservative_total<128*1024**2
save(HERE/'FINAL_VALIDATION.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    approved_source_runtime_driver_plan_environment_preflight_preserved=True,
    original_S1_raw_files_byte_rechecked=len(old['files']),original_S1_F0_result_inputs_runtime_unchanged=True,
    diagnostic_raw_files_byte_rechecked=len(new['files']),new_output_budget_bytes=128*1024**2,
    measured_run_and_all_result_files_before_receipt_bytes=bytes_before,
    conservative_including_receipt_bytes=conservative_total,
    exact_frozen_executor_unchanged=True,no_candidate_changes=True,
    diagnostic_attempts=7,graph_calls=7,expected_failures=2,completed_graphs=5,unstarted=0,
    new_graph_host_launches_by_validation=0,model_requests=0,retries=0,warmups=0,extra_probes=0,
    S2_S3='NOT_ADMITTED_UNSTARTED',modules_before=before,modules_after=modules()))
actual=sum(p.stat().st_size for p in HERE.rglob('*') if p.is_file())+new['raw_bytes']
assert actual<=conservative_total
print(dict(validated=True,old_files=len(old['files']),new_files=len(new['files']),new_output_bytes=actual,
           budget_bytes=128*1024**2,attempts=7))
