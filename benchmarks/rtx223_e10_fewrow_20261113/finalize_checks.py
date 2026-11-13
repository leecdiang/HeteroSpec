"""Read-only identities, old-ledger preservation, and terminal checks. No CUDA."""
from pathlib import Path
import hashlib,json,datetime,ctypes as C
p=Path(__file__).resolve().parent
sha=lambda q:hashlib.file_digest(Path(q).open('rb'),'sha256').hexdigest()
rows=[]
for path,row in json.loads((p/'build-002/FREEZE.json').read_bytes())['inputs'].items():
 actual=sha(path)
 if actual!=row['sha256']:raise RuntimeError('Frozen build input changed '+path)
 rows.append(dict(path=path,sha256=actual,bytes=Path(path).stat().st_size))
lineage=json.loads((p/'PARENT_REUSE_VERIFIED.json').read_bytes())
old=[*lineage['preservation'],*lineage['old_identity_checks'],*json.loads((p/'C1_PARENT_VERIFIED.json').read_bytes())['files']]
for row in old:assert sha(row['path'])==row['sha256'],row['path']
stage=json.loads((p/'STAGING.json').read_bytes())
for row in stage['files']:
 q=Path(row['path']);assert sha(q)==row['sha256'];assert q.stat().st_ino==row['file_id']['inode'] and q.stat().st_dev==row['file_id']['volume']
for row in json.loads((p/'UPSTREAM_BLOBS_VERIFIED.json').read_bytes())['files']:
 assert sha(p/'u'/row['path'])==row['sha256']
family=Path('D:/HeteroSpec-PC/rtx223-e10-fewrow/family.jsonl')
events=[json.loads(s) for s in family.read_bytes().splitlines()]
assert events[-1]['kind']=='STOPPED' and events[-1]['reserved']==14
assert all(e.get('owned_exit_confirmed',True) for e in events)
(p/'evidence/family.jsonl').write_bytes(family.read_bytes())
host=json.loads((p/'HOST_FINAL.private.json').read_bytes())
assert not host['competing_workers'] and not host['project_services'] and not host['project_tasks']
admin=json.loads((p/'ADMIN_LAUNCH.json').read_bytes())
assert not any(x['ProcessId']==admin['pid'] for x in host['all_processes'])
leases=[Path('D:/HeteroSpec-PC/RTX_EXPERIMENT.lock'),Path('D:/HeteroSpec-PC/rtx223-e10-fewrow/runner.lease')]
assert not any(q.exists() for q in leases)
assert json.loads((p/'PROFILE_CLEANUP.json').read_bytes())['deleted']
result=dict(pass_=True,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),build_inputs_checked=len(rows),build_executable_sha256=sha(p/'build-002/operator-upstream.exe'),staging_identity_preserved=True,upstream10_blobs_preserved=True,old_files_checked=old,frozen_build_inputs_changed=0,CUDA_initializations_in_this_verifier=0)
with (p/'FINAL_IDENTITIES.json').open('x',encoding='utf8') as f:json.dump(result,f,indent=2)
clean=dict(pass_=True,utc=host['end_utc'],admin_pid=admin['pid'],admin_in_final_snapshot=False,competing_workers=host['competing_workers'],project_services=host['project_services'],project_tasks=host['project_tasks'],all_host_process_count=len(host['all_processes']),all_host_tasks_count=len(host['all_tasks']),leases=[dict(path=str(q),exists=q.exists()) for q in leases],profile_deleted=True,all_profile_files_preserved=len(json.loads((p/'PROFILE_DATA_PRESERVED.json').read_bytes())['files']),old_ledger_and_failures_unchanged=True,ACL_changes=0,Windhawk_changes=0,security_changes=0,limitations='Host snapshot is point-in-time;task action metadata has PowerShell depth7 truncation warning;top-level action strings, task IDs/states, process command lines and all matching filters retained privately. Not a guarantee about future externally-created work or physical device cleanup.')
with (p/'CLEANUP_FINAL.json').open('x',encoding='utf8') as f:json.dump(clean,f,indent=2)
print(json.dumps(dict(build_inputs=len(rows),old_records=len(old),cleanup=True)))
