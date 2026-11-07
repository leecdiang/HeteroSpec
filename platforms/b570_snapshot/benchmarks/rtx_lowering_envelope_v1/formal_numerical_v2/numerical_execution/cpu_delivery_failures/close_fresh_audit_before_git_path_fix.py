"""Verify actual remote-byte fresh restoration, unchanged frozen CPU reanalysis and storage."""
import datetime,json,subprocess,sys
from pathlib import Path
D=Path(__file__).resolve().parent;V=D.parent
sys.path.insert(0,str(V))
from common import load,save,sha
auth=load(D/'AUTHENTICATED_FORMAL.json');manifest=load(V/'formal_delivery/MANIFEST.json')
fresh=Path('D:/hs113-formal-numerical-v2-fresh-v1');root=Path(load(V/'F0.json')['execution_root'])
assert auth['authenticated_remote_bytes'] and auth['archive_sha256']==manifest['sha256']
assert sha(auth['actual_downloaded_archive_for_frozen_restore'])==manifest['sha256']
assert sha(auth['original_local_archive_retained'])==manifest['sha256']
assert load(V/'formal_delivery/FRESH_RESTORE.json')['status']=='PASS'
assert load(fresh/'CPU_REANALYSIS.json')['exit_code']==0
assert (fresh/'RECOMPUTED.json').read_bytes()==(D/'RECONSTRUCTED.json').read_bytes()==(fresh/'raw/POST_STOP_FROZEN_CPU_ANALYSIS.json').read_bytes()
assert not (fresh/'raw/NUMERICAL_ENDED.json').exists() and not (fresh/'raw/ANALYSIS.json').exists()
assert (fresh/'raw/ACTIVE_CONTROLLER.lock').exists() and (fresh/'raw/numerical/473/FAILED.json').exists() and (fresh/'raw/numerical/473/COMPLETED.json').exists()
for member in manifest['members']:
    p=fresh/member['path'];assert p.stat().st_size==member['bytes'] and sha(p)==member['sha256']
recomputed=load(fresh/'RECOMPUTED.json');assert recomputed['completed_qualified']==474 and recomputed['control_failure'] is None
assert recomputed['counts']==dict(native_process_started=474,graph_started=474,graph_call_return_recorded=474,synchronization_return_recorded=474)
assert sum(r['status']=='NOT_STARTED_PROTOCOL_STOP' for r in recomputed['slots'])==246
def size(p):return sum(x.stat().st_size for x in p.rglob('*') if x.is_file())
object_lines=subprocess.check_output(['git','rev-list','--objects','d4df9f1abaec3b5de4e7331c8ca9820432bc0bcf..HEAD','--','benchmarks/rtx_lowering_envelope_v1/formal_numerical_v2'],cwd=V).decode().splitlines()
ids=list(dict.fromkeys(x.split()[0] for x in object_lines));object_sizes=subprocess.check_output(['git','cat-file','--batch-check=%(objectsize)'],input=('\n'.join(ids)+'\n').encode(),cwd=V).decode().splitlines()
git_bound=2*sum(map(int,object_sizes))+64*1024**2
components=dict(prior_all_preparation_conservative_bound=513177521,current_entire_formal_worktree_files=size(V),original_actual_raw_root=size(root),fresh_authenticated_raw_and_frozen_files=size(fresh),new_formal_Git_objects_doubled_plus64MiB_metadata=git_bound,remaining_small_CPU_delivery_reserve=16*1024**2)
total=sum(components.values());assert total<4*1024**3
receipt=dict(recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),data_commit=auth['data_commit'],archive_sha256=manifest['sha256'],members_verified=len(manifest['members']),all_raw_member_hashes_verified=True,actual_remote_archive_used_for_fresh_restore=True,frozen_analysis_byte_identical=True,recomputed_analysis_sha256=sha(fresh/'RECOMPUTED.json'),fresh_directory=str(fresh),qualified=474,unstarted=246,new_GPU_native_model_query_starts=0,independent_reanalysis='Unchanged archived frozen analyzer over fully authenticated raw bytes; no source/audit standard changed and no online-unqualified outputs promoted.',artifact_accounting=dict(components=components,conservative_total_bytes=total,limit_bytes=4*1024**3,semantics='Deliberately overcounts prior preparation plus current whole formal dir and doubled Git objects; logical file bytes, not claimed NTFS allocation. Exactly two complete archives and two actual raw copies, no sharding or third full archive.'),original_stop_and_missing_receipts_preserved=True,next_GPU_authorization='NOT_GRANTED')
save(D/'FRESH_AUDIT.json',receipt)
print(json.dumps(dict(members=len(manifest['members']),frozen_analysis_byte_identical=True,conservative_derived_bytes=total,limit=4*1024**3,new_GPU_starts=0),indent=2))
