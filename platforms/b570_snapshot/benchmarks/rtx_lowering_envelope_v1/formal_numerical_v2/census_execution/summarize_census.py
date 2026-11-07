"""CPU-only reconstruction/reporting of this actual census; never starts a child backend."""
import csv, datetime, hashlib, json, shutil, sys
from pathlib import Path

D = Path(__file__).resolve().parent
V = D.parent
sys.path.insert(0, str(V))
import analyzer
from common import load, save, sha

f0, plan = load(V/'F0.json'), load(V/'PLAN.json')
root = Path(f0['execution_root'])
native = root/'census/native'
census = load(native/'CENSUS.json')
expected = {(r['descriptor_id'],r['layout']):r for r in load(V/'CPU_GRAPH_EXPECTED.json')}
decision = analyzer.census_decision(census, expected, plan)
assert decision == load(root/'CENSUS_DECISION.json')
core = analyzer.verify_modules(native,census,f0,load(root/'census/MODULE_FILES.json'))
ended = load(root/'CENSUS_ENDED.json')
assert ended['error'] is None and load(root/'CENSUS_SUCCESS.json')['completed_census']
assert census['graph_computes'] == 0 and census['GPU_initializations'] == 1
assert not (root/'numerical').exists()
assert not (V/'execution_ledger/NUMERICAL_CONTROLLER_STARTED.json').exists()

descriptors = {d['id']:d for d in plan['descriptors']}
rows = []
unsupported_nodes = []
for r in census['records']:
    desc = descriptors[r['descriptor_id']]
    rows.append(dict(descriptor_id=r['descriptor_id'],family=desc['family'],layer=desc['layer'],phase=desc['phase'],q=desc['q'],layout=r['layout'],full_support=r['full_support'],node_queries=len(r['nodes']),node_supported=sum(n['CUDA_support'] for n in r['nodes']),actual_placement='NOT_OBSERVED',graph_computes=0))
    for n in r['nodes']:
        if not n['CUDA_support']:
            unsupported_nodes.append(dict(descriptor_id=r['descriptor_id'],layout=r['layout'],node_id=n['id'],op=n['op'],metadata_only=n['metadata_only']))
with (D/'SUPPORT_COORDINATES.csv').open('x',encoding='utf-8',newline='') as out:
    w=csv.DictWriter(out,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
counts = {}
for layout in analyzer.LAYOUTS:
    group = [r for r in rows if r['layout']==layout]
    counts[layout] = dict(graphs=len(group),supported=sum(r['full_support'] for r in group),node_queries=sum(r['node_queries'] for r in group),node_supported=sum(r['node_supported'] for r in group))
assert len(rows)==360 and sum(r['node_queries'] for r in rows)==5418

processes = {}
helpers = []
for name in ('readiness','native'):
    events = load(root/('census/'+name+'.JOB_EVENTS.json'))
    life = load(root/('census/'+name+'.LIFETIME.json'))
    proc = load(root/('census/'+name+'.PROCESS.json'))
    assert events['errors']==[] and life['error'] is None and life['exit_code']==0
    assert len(events['started_unique_PIDs'])==life['job_total_processes']
    assert sha(events['console_helper_pin']['path'])==events['console_helper_pin']['sha256']
    extras=[e for e in events['events'] if e['message']==6 and e['pid']!=proc['pid']]
    helpers.extend(extras)
    processes[name]=dict(process=proc,lifetime=life,helper_events=extras)
assert len(helpers)<=2

# Immutable evidence: no implementation/graph/wire/runtime change after the census.
source_hashes=set(f0['source_roles'].values())
numeric_paths={str(Path(f0['runtime_directory'])/n).lower() for n in f0['numerical_DLLs']}
post_pins=[]
for p in f0['files']:
    if p['sha256'] in source_hashes or str(Path(p['path'])).lower() in numeric_paths or p['path'] in (f0['executable'],f0['plan_path']):
        assert sha(p['path'])==p['sha256'],p['path'];post_pins.append(p)
assert sha(V/'F0.json')=='73ef7106240be73ab914e4c6a36064a0d1fd6d41ce5d9c38bf65f38e8331f080'
assert (V/'F0.json').read_bytes()==(V/'REMOTE_F0_BYTES.json').read_bytes()
cas=list((root/'cas').glob('*.bin'))
assert {p.name for p in cas}=={p.name for p in (V/'reference_cas').glob('*.bin')}
assert all(sha(p)==p.stem for p in cas)
old_archive=V.parent/'S1_NUMERICAL/RAW_NUMERICAL_STOP.zip'
gpu14_archive=V.parent/'GPU14_EXECUTION/RAW_GPU14.zip'
assert sha(old_archive)=='9dcd5240662af7cc98bdca8a82316f42e062d158c7c03e50044d9238b8592c04'
assert sha(gpu14_archive)=='f1dc041ad50400b3c11c874d5a94db9fba960d17ec20361df21a2871d8c3102f'
save(D/'POST_RUN_IDENTITIES.json',dict(verified_pins=post_pins,reference_CAS_files=len(cas),reference_CAS_bytes=sum(p.stat().st_size for p in cas),reference_CAS_hashes_verified=True,old720_archive_sha256=sha(old_archive),GPU14_archive_sha256=sha(gpu14_archive),old720=dict(started_failed=1,unstarted=719,completed=0),GPU14=dict(started=14,completed=14,failed=0)))
shutil.copyfile(V/'execution_ledger/CENSUS_CONTROLLER_STARTED.json',D/'CENSUS_CONTROLLER_STARTED.json')

manifest=load(V/'census_delivery/MANIFEST.json')
summary=dict(recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),run_id=f0['run_id'],F0_sha256=sha(V/'F0.json'),census_sha256=sha(native/'CENSUS.json'),decision_sha256=sha(root/'CENSUS_DECISION.json'),archive_sha256=manifest['sha256'],archive_bytes=manifest['bytes'],archive_members=len(manifest['members']),layouts=counts,unsupported_graphs=[r for r in rows if not r['full_support']],unsupported_nodes=unsupported_nodes,node_support_API_queries=census['support_queries'],counts=dict(controllers=1,readiness_processes=1,native_support_hosts=1,console_helpers=len(helpers),owned_starts=3+len(helpers),numerical_hosts=0,graph_computes=0,model_requests=0,warmups=0,scientific_retries=0,explicit_nvidia_smi_queries=1,backend_loads=1,backend_initializations=1,explicit_graph_tensor_allocations=census['allocations']),controller=ended,processes=processes,admission=load(root/'census/ADMISSION.json'),core=core,plugin_shared_core_IAT_entries=41,numerical_admitted_technical_condition=decision['numerical_admitted'],numerical_authorization='NOT_GRANTED',raw_root_logical_bytes=sum(p.stat().st_size for p in root.rglob('*') if p.is_file()),census_nonCAS_bytes=sum(p.stat().st_size for p in (root/'census').rglob('*') if p.is_file()),scope='Backend support queries only. CUDA/context initialization occurred; no graph execution, actual tensor placement, numerical qualification, actor, timing/profile, S2 or S3 qualification. Internal driver queries/allocations/synchronization are UNKNOWN. Controller wall/child lifetimes are engineering cost, not clean timing.')
save(D/'SUMMARY.json',summary)
table='\n'.join('| '+l+' | '+str(x['supported'])+'/'+str(x['graphs'])+' | '+str(x['node_supported'])+'/'+str(x['node_queries'])+' |' for l,x in counts.items())
text=f'''# Formal v2 census: backend support queries passed

Only the actual census-only approval was used, at reviewed05912d0. The frozen
controller ended successfully; no implementation, F0, plan or execution flags
were changed. QH_C remains the primary candidate and QH_D the fixed control.

| Layout | Supported graphs | Supported node queries |
|---|---:|---:|
{table}

All360 planned graphs and5418 node support queries are present. Unsupported graph
coordinates: none. Unsupported nodes: none. The complete360-coordinate report is
SUPPORT_COORDINATES.csv. All graph identities/parameters match CPU_GRAPH_EXPECTED.
The frozen decision gives numerical_admitted=true as a technical condition only;
there is no numerical execution authorization and all720 v2 slots are unstarted.

Actual processes: controller{ended['pid']}; native support host{processes['native']['process']['pid']};
readiness query{processes['readiness']['process']['pid']}; pinned conhost helpers
{','.join(str(x['pid']) for x in helpers)}. Total{3+len(helpers)} owned starts,0 failures.
Native host{processes['native']['lifetime']['seconds']:.9f}s; readiness
{processes['readiness']['lifetime']['seconds']:.9f}s. Controller wall
{ended['seconds']:.9f}/600s, conservative owned bound
{ended['conservative_owned_bound_seconds']:.9f}/1800s (whole wall x3).
Controller sampled peak private commit{ended['sampled_controller_peak_private_commit_bytes']}B;
native peak process/job commit{processes['native']['lifetime']['peak_process_commit_bytes']}/{processes['native']['lifetime']['peak_job_commit_bytes']}B;
readiness peak process/job commit{processes['readiness']['lifetime']['peak_process_commit_bytes']}/{processes['readiness']['lifetime']['peak_job_commit_bytes']}B.
Census metadata/logs{summary['census_nonCAS_bytes']}B; raw root including the complete
immutable reference CAS{summary['raw_root_logical_bytes']}B; sealed census archive
{manifest['bytes']}B/{len(manifest['members'])}members. No budget was reset or borrowed.
Requested50ms observations do not certify a continuous sampling cadence.

The actual CUDA-loaded process passed core/registry/host identities and all41
plugin core-IAT ownership checks. One process-level initialization of the exact
ggml-base.dll completed before CUDA loading.21 numerical DLLs and frozen source
identities remain unchanged. This census loaded/initialized CUDA and constructed
metadata graphs; it is not zero device activity. Explicit graph-compute calls,
graph-tensor allocations, numerical hosts, model requests and warmups are0.
Internal CUDA/context allocations and driver query counts are UNKNOWN. Actual
graph tensor placement, successful execution/synchronization, QK/softmax/AV/output
values and numerical/repeatability controls remain unobserved for formal v2.
No clean timing, speed, actor, S1 profile, S2 or S3 qualification is established.

Old720 remains1 started-failed/719 unstarted/0 completed; GPU14 remains14 started/
14 completed/0 failed. Their original archive hashes were rechecked and no records
were reused. The census contains no numerical outputs to fill any old/new slot.

F0 SHA256: `{summary['F0_sha256']}`

Census SHA256: `{summary['census_sha256']}`

Decision SHA256: `{summary['decision_sha256']}`

Archive SHA256: `{manifest['sha256']}`

The existing seal_census.py sealed these bytes. Commit/push and authenticated
remote byte reconstruction are recorded separately in AUTHENTICATED_CENSUS.json
after delivery. Stop here: a later human approval must bind these actual F0,
census and decision hashes before the numerical entry can be used.
'''
with (D/'RESULT.md').open('x',encoding='utf-8',newline='\n') as out:out.write(text)
print(json.dumps({k:summary[k] for k in ('layouts','census_sha256','decision_sha256','counts','raw_root_logical_bytes')},indent=2))
