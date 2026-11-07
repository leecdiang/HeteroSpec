"""CPU-only full ledger/cost reconstruction. Never repairs or resumes the frozen run."""
import collections,datetime,json,shutil,sys
from pathlib import Path
D=Path(__file__).resolve().parent;V=D.parent
sys.path.insert(0,str(V))
from common import load,save,sha
f0=load(V/'F0.json');plan=load(V/'PLAN.json');root=Path(f0['execution_root'])
a=load(D/'RECONSTRUCTED.json');rows=[];processes=[];all_ids=[];queries=owners=0;families={}
for s,r in zip(plan['numerical_slots'],a['slots']):
    d=root/'numerical'/f"{s['index']:03d}"
    online=(d/'COMPLETED.json').exists()
    assert online==(r['status']=='COMPLETED_QUALIFIED'),'No posthoc promotion of an unqualified return'
    row=dict(index=s['index'],**r,online_COMPLETED=online,FAILED_receipt_exists=(d/'FAILED.json').exists())
    rows.append(row)
    for name in ('native','readiness'):
        if not (d/(name+'.PROCESS.json')).exists():continue
        p=load(d/(name+'.PROCESS.json'));life=load(d/(name+'.LIFETIME.json'));e=load(d/(name+'.JOB_EVENTS.json'))
        assert life['exit_code']==0 and life['error'] is None and not e['errors']
        assert p['pid']==life['pid']==e['registered_PID'] and p['creation_filetime_100ns']==life['creation_filetime_100ns']
        starts=[x for x in e['events'] if x['message']==6]
        assert len(starts)==life['job_total_processes']==len(e['started_unique_PIDs'])
        assert len([x for x in starts if x['pid']==p['pid']])==1
        helpers=[x for x in starts if x['pid']!=p['pid']]
        assert len(helpers)<=1 and all(str(Path(x['image'])).lower()==str(Path(f0['console_helper']['path'])).lower() for x in helpers)
        all_ids.append((p['pid'],p['creation_filetime_100ns']))
        processes.append(dict(slot=s['id'],index=s['index'],kind=name,pid=p['pid'],creation=p['creation_filetime_100ns'],seconds=life['seconds'],helpers=helpers,**{k:life[k] for k in ('peak_process_commit_bytes','peak_job_commit_bytes','job_total_processes')}))
    if (d/'native/RECORD.json').exists():
        n=load(d/'native/RECORD.json');queries+=len(n['nodes']['nodes']);owners+=len(n['nodes']['ownership'])
    families.setdefault(s['family'],collections.Counter())[r['status']]+=1
assert len(all_ids)==len(set(all_ids))
native=[p for p in processes if p['kind']=='native'];ready=[p for p in processes if p['kind']=='readiness']
helpers=sum(len(p['helpers']) for p in processes)
start=load(V/'execution_ledger/NUMERICAL_CONTROLLER_STARTED.json');stop=load(root/'NUMERICAL_WATCHDOG_STOP.json');launch=load(D/'LAUNCH_ENDED.json')
parse=lambda x:datetime.datetime.fromisoformat(x.replace('Z','+00:00'))
wrapper_wall=(parse(launch['ended_utc'])-parse(launch['started_utc'])).total_seconds()
observed_to_watchdog=stop['epoch']-start['epoch']
native_seconds=sum(p['seconds'] for p in native);ready_seconds=sum(p['seconds'] for p in ready)
counts=dict(planned=720,online_qualified=sum(x['online_COMPLETED'] for x in rows),offline_qualified=a['completed_qualified'],native_processes=len(native),readiness_processes=len(ready),controllers=1,conhost_helpers=helpers,owned_process_starts=1+len(processes)+helpers,graph_starts=a['counts']['graph_started'],graph_returns=a['counts']['graph_call_return_recorded'],sync_returns=a['counts']['synchronization_return_recorded'],control_failed=sum(x['status']=='CONTROL_FAILED' for x in rows),started_failed_or_incomplete=sum(x['status']=='STARTED_FAILED_OR_INCOMPLETE' for x in rows),not_started=sum(not x['native_process_started'] for x in rows),not_supported=sum(x['status']=='NOT_SUPPORTED' for x in rows),model_requests=0,warmups=0,scientific_retries=0,support_API_queries=queries,explicit_readiness_GPU_queries=len(ready),backend_loads=len(native),backend_init_by_name=len(native),explicit_cudaDeviceSynchronize_calls=2*len(native),backend_get_device_identity_calls=owners,buft_get_device_identity_calls=owners,GetSystemPowerStatus=len(ready),PowerGetActiveScheme=len(ready),internal_driver_kernel_calls='UNKNOWN')
assert counts['online_qualified']==474 and counts['not_started']==246 and counts['graph_starts']==counts['graph_returns']==counts['sync_returns']==474
cost=dict(wrapper_wall_seconds=wrapper_wall,start_receipt_to_watchdog_epoch_seconds=observed_to_watchdog,wrapper_x3_conservative_owned_envelope_seconds=wrapper_wall*3,census_conservative_owned_seconds=load(root/'CENSUS_ENDED.json')['conservative_owned_bound_seconds'],combined_observed_conservative_envelope_seconds=wrapper_wall*3+load(root/'CENSUS_ENDED.json')['conservative_owned_bound_seconds'],numerical_owned_nominal_ceiling=5400,whole_v2_owned_ceiling=7200,deadline_semantics='The controller asserted a1800s wall ceiling. Watchdog observed it after the threshold; no NUMERICAL_ENDED receipt. Do not truncate the observed envelope to pretend exact5400s compliance.',native_lifetimes_sum_seconds=native_seconds,readiness_lifetimes_sum_seconds=ready_seconds,pre_no_next_start_controller_epoch_seconds=load(root/'NUMERICAL_FAILED.json')['epoch']-start['epoch'],outside_direct_child_lifetimes_to_no_next_start_seconds=(load(root/'NUMERICAL_FAILED.json')['epoch']-start['epoch'])-native_seconds-ready_seconds,outside_child_semantics='Descriptive process-envelope difference; includes Python checks, hashing, graph comparisons, monitoring, I/O and launch/closure intervals. Not exclusive CPU time, clean GPU time or a causal share.',controller_peak_private_commit='UNKNOWN: watchdog bypassed finally receipt',native_peak_process_commit_bytes=max(p['peak_process_commit_bytes'] for p in native),native_peak_job_commit_bytes=max(p['peak_job_commit_bytes'] for p in native),readiness_peak_process_commit_bytes=max(p['peak_process_commit_bytes'] for p in ready),readiness_peak_job_commit_bytes=max(p['peak_job_commit_bytes'] for p in ready))
save(D/'LEDGER_AUDIT.json',dict(counts=counts,cost=cost,families={k:dict(v) for k,v in families.items()},slots=rows,processes=processes,stop=load(root/'NUMERICAL_FAILED.json'),watchdog=stop,missing_NUMERICAL_ENDED=True,missing_in_controller_ANALYSIS=True,residual_lock_preserved=True,last_slot_receipt_collision=dict(index=473,online_completed=True,FAILED_receipt_reason=load(root/'numerical/473/FAILED.json')['error'],interpretation='Frozen controller kept current=473 when next-start reservation failed, then wrote FAILED there. Preserve both receipts; graph473 returned/synchronized and passed original online+frozen offline controls. The failure is the next-start controller budget gate, not a new graph473 numerical failure.')))
assert sha(V.parent/'S1_NUMERICAL/RAW_NUMERICAL_STOP.zip')=='9dcd5240662af7cc98bdca8a82316f42e062d158c7c03e50044d9238b8592c04'
assert sha(V.parent/'GPU14_EXECUTION/RAW_GPU14.zip')=='f1dc041ad50400b3c11c874d5a94db9fba960d17ec20361df21a2871d8c3102f'
for name,expected in f0['source_roles'].items():
    candidates=[p for p in f0['files'] if Path(p['path']).name==name and p['sha256']==expected]
    assert candidates and all(sha(p['path'])==expected for p in candidates)
for name,expected in f0['numerical_DLLs'].items():assert sha(Path(f0['runtime_directory'])/name)==expected
assert sha(f0['executable'])==f0['executable_sha256']
save(D/'POST_RUN_IDENTITIES.json',dict(F0_sha256=sha(V/'F0.json'),plan_sha256=sha(V/'PLAN.json'),EXE_sha256=sha(f0['executable']),source_roles_unchanged=True,numerical_DLLs_unchanged=21,old720_archive_unchanged=True,GPU14_archive_unchanged=True,old720='1failed/719unstarted/0completed',GPU14='14completed/0failed'))
provenance=root/'provenance/numerical';provenance.mkdir(parents=True,exist_ok=False)
for name in ('AUTHOR_MESSAGE.txt','AUTHOR_APPROVAL.json','PREFLIGHT.json','LAUNCH_ENDED.json','RECONSTRUCTED.json','RECONSTRUCTION_LIFETIME.json','LEDGER_AUDIT.json','POST_RUN_IDENTITIES.json','controller.stdout','controller.stderr','reconstruct.stdout','reconstruct.stderr'):
    shutil.copyfile(D/name,provenance/name)
shutil.copyfile(V/'execution_ledger/NUMERICAL_CONTROLLER_STARTED.json',provenance/'NUMERICAL_CONTROLLER_STARTED.json')
shutil.copyfile(V/'execution_ledger/CENSUS_CONTROLLER_STARTED.json',provenance/'CENSUS_CONTROLLER_STARTED.json')
shutil.copyfile(D/'RECONSTRUCTED.json',root/'POST_STOP_FROZEN_CPU_ANALYSIS.json')
save(provenance/'POST_STOP_PROVENANCE_APPEND.json',dict(recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),meaning='Append-only CPU provenance after sole controller exit70. All original records, FAILED/COMPLETED collision, residual lock and missing ENDED/ANALYSIS kept; no original slot or old archive changed.',new_GPU_starts=0))
print(json.dumps(dict(counts=counts,cost=cost,families={k:dict(v) for k,v in families.items()}),indent=2))
