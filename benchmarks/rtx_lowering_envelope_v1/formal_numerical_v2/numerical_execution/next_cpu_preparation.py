"""Bounded CPU-only Case C preparation. Requires actual remote/fresh audit first.

No launcher, backend loading, timing/profile run or new execution F0 is produced.
The original24-coordinate selection is independent of the new numerical outcomes.
"""
import datetime,importlib.util,json,math,sys,time
from pathlib import Path
D=Path(__file__).resolve().parent;V=D.parent;B=V.parent
sys.path.insert(0,str(V))
from common import load,save,sha

def planning_full_panel(counts,stop):
    # This is only a preparation predicate, never a substitute raw auditor.
    return stop is None and all(counts.get(k)==720 for k in ('qualified','starts','returns','syncs')) and counts.get('missing')==counts.get('controls_failed')==0

def next_attempt_reservation(elapsed,wall,ready,native,receipt_reserve):
    values=(elapsed,wall,ready,native,receipt_reserve)
    if any(type(x) not in (int,float) or not math.isfinite(x) or x<0 for x in values):raise ValueError('finite nonnegative bounds required')
    return wall-elapsed>ready+native+receipt_reserve

def failure_owner(completed,started):
    return 'CONTROLLER_NEXT_START_GATE' if completed else 'STARTED_SLOT' if started else 'CONTROLLER_PRE_START_GATE'

def main():
    began=time.perf_counter();auth=load(D/'AUTHENTICATED_FORMAL.json');fresh=load(D/'FRESH_AUDIT.json')
    assert auth['authenticated_remote_bytes'] and fresh['all_raw_member_hashes_verified'] and fresh['frozen_analysis_byte_identical']
    actual=load(D/'RECONSTRUCTED.json');ledger=load(D/'LEDGER_AUDIT.json');plan=load(V/'PLAN.json')
    tests=[]
    def check(name,condition):assert condition,name;tests.append(name)
    full=dict(qualified=720,starts=720,returns=720,syncs=720,missing=0,controls_failed=0)
    check('synthetic_complete_technical_only',planning_full_panel(full,None))
    check('actual474_cannot_be_full',not planning_full_panel(dict(full,qualified=474,starts=474,returns=474,syncs=474,missing=246),ledger['stop']))
    for k in ('qualified','starts','returns','syncs'):
        check('synthetic_missing_'+k,not planning_full_panel(dict(full,**{k:719}),None))
    check('missing_coordinate_not_deleted',not planning_full_panel(dict(full,missing=1),None))
    check('control_failure_not_waived',not planning_full_panel(dict(full,controls_failed=1),None))
    check('stop_receipt_not_erased',not planning_full_panel(full,{'budget_stop':True}))
    check('enough_pre_attempt_reserve',next_attempt_reservation(100,1800,10,60,5))
    check('boundary_no_free_start',not next_attempt_reservation(1725,1800,10,60,5))
    check('insufficient_reserve_no_start',not next_attempt_reservation(1732,1800,10,60,5))
    for bad in (float('nan'),float('inf'),-1,True):
        rejected=False
        try:next_attempt_reservation(bad,1800,10,60,5)
        except ValueError:rejected=True
        check('reject_invalid_bound_'+repr(bad),rejected)
    check('completed_slot_never_receives_new_start_failure',failure_owner(True,True)=='CONTROLLER_NEXT_START_GATE')
    check('started_unqualified_failure_retains_slot',failure_owner(False,True)=='STARTED_SLOT')
    check('no_native_start_failure_is_controller',failure_owner(False,False)=='CONTROLLER_PRE_START_GATE')

    design=V.parents[2]/'docs/experiments/rtx_lowering_envelope_20261015/design_checks.py'
    spec=importlib.util.spec_from_file_location('original_design_checks',design);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    coordinates=mod.profile_coordinates();assert len(coordinates)==len(set(coordinates))==24
    by_coord={(c['family'],c['phase'],c['q'],c['layer']):c for c in actual['contexts']}
    selected=[]
    for family,phase,q,layer in coordinates:
        c=by_coord[family,phase,q,layer]
        missing=[dict(layout=l,repeat=r) for l in ('PQ','QB','QH_C') for r,e in enumerate(c['layouts'][l]) if e is None]
        selected.append(dict(descriptor=c['descriptor'],family=family,phase=phase,q=q,layer=layer,all_PQ_QB_QH_C_repeats_qualified=not missing,missing=missing))
    ready=sum(x['all_PQ_QB_QH_C_repeats_qualified'] for x in selected)
    assert ready==15
    source=B/'native/source';ninja=B/'native/build/build.ninja'
    link=next((i,line) for i,line in enumerate(ninja.read_text(encoding='utf-8').splitlines(),1) if line.startswith('build bin/llama-server.exe:'))
    assert 'ggml-base.a' in link[1] and 'ggml.a' in link[1]
    paths=[source/'src/hs_scope.h',source/'src/llama-graph.cpp',source/'src/llama-graph.h',source/'src/llama-context.cpp',B/'native_cache113.cpp',ninja]
    pinlist=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in paths]
    active=ledger['cost']['pre_no_next_start_controller_epoch_seconds'];per=active/474
    projection=per*720;cpu=float((datetime.datetime.fromisoformat(load(D/'RECONSTRUCTION_LIFETIME.json')['ended_utc'].replace('Z','+00:00'))-datetime.datetime.fromisoformat(load(D/'RECONSTRUCTION_LIFETIME.json')['started_utc'].replace('Z','+00:00'))).total_seconds())*720/474
    receipt=dict(recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),branch='CASE_C_BUDGET_STOP',scope='CPU planning/source review only; no production patch, native start, device query, numerical slot, timing/profile or execution F0',actual_cpu_tests=tests,test_count=len(tests),seconds=time.perf_counter()-began,original24_selector_sha256=sha(design),S1B_fixed_coordinates=selected,S1B_ready_coordinates=ready,S1B_planned_coordinates=24,S1B_technical_GO=False,S1B_GPU_authorization=False,full_formal_panel_GO=False,primary_QH='QH_C',source_review=pinlist,actor_link_line=dict(path=str(ninja),line=link[0],text=link[1]),actor_shared_core_admission='NOT_ESTABLISHED: inspected actor still lists static ggml/ggml-base archives; formal RouteA operator qualification is not actor qualification.',actor_phase_graph_cache_state='Source has target-role scope/layout graph-cache guards and QH nonflash/single-stream restrictions; actual natural reference endpoints/KV/rollback/phase transitions and cache lifecycle remain unexecuted.',future_budget_projection=dict(observed_active_envelope_seconds=active,observed_seconds_per_qualified_slot=per,linear_full720_active_projection_seconds=projection,linear_full720_offline_CPU_projection_seconds=cpu,possible_future_numeric_wall_seconds=4500,possible_future_owned_bound_seconds=13500,status='PROPOSAL_ONLY_NOT_FROZEN_NOT_AUTHORIZED',meaning='Observed extrapolation plus margin, not a worst-case guarantee. Requires new independent budget and run_id/F0/source review; no borrowing/reuse of current or old slots. Any required new census separately prospective.'),future_minimal_engineering=['Move expensive final raw reconstruction out of the GPU-owned controller after bounded end receipts and owned-job closure.','Preserve hard deadline, but write a bounded durable minimum stop/resource receipt before immediate exit; do not rely on finally after os._exit.','Separate controller next-start failure from current completed slot; prototype negative tests above cover this bookkeeping distinction.','Replace repeated whole-root rglob in the hot watcher with tested append-only byte accounting plus bounded reconciliation, only in a future reviewed implementation.','Account all helper/query/controller processes and explicitly freeze future CPU delivery budget; no hidden independent observer.'],untouched_frozen_v2=True,additional_GPU_starts=0)
    assert receipt['seconds']<30
    save(D/'NEXT_CPU_PREPARATION.json',receipt)
    text=f'''# Case C: bounded CPU preparation after authenticated v2 stop

Actual work:19pureCPU planning/negative tests; original fixed24selector instantiated
without outcome-based selection; actual module/phase/cache/actor-link source read
and pinned. No production controller,host,graph,F0,analyzer or old receipt changed.
The prototype is a CPU planner,not a native execution certificate or launcher.

Only15/24original S1B coordinates have both PQ/QB/QH_C fresh repeats qualified.
9/24lack required numerical observations; NEXT_CPU_PREPARATION.json lists each.
The all-family720panel is incomplete. S1B clean timing/profile remainsNO-GO;
there is no prepared executable S1B F0 or GPU authorization. No selective fast
subset is proposed. QH_C stays primary; QH_D is not substituted.

Observed active orchestration envelope perqualifiedslot={per:.6f}s. Linear720slot
projection={projection:.3f}s; full offlineCPU projection={cpu:.3f}s. These are
descriptive extrapolations,not runtime guarantees or operator costs. A possible
future independent numerical budget is4500wall/13500owned seconds,only a review
proposal; no allocation/run_id/newF0 or GPU run is created. Current v2 cannot
resume,and old/GPU14 results cannot furnish repeats for any fresh study.

Concrete future repair scope: bounded durable controller stop receipt; distinguish
controller next-start failure from an already completed slot; place expensive
post-stage analysis outside the GPU-owned controller; review hot watcher recursive
filesystem scans with append-only byte accounting and bounded reconciliation.
No timer/kernel/precision/QH arithmetic repair is suggested. Source-level hotspot
and envelope evidence do not identify an exclusive CPU/GPU bottleneck or warrant
hardware. These changes require separate implementation/testing/review before
any future F0; this file does not retroactively improve current admission.

Readonly S2 review found actor build.ninja line{link[0]} still lists static
ggml.a/ggml-base.a. That actor has not received the formal operator RouteA shared
core admission,so its module/IAT/init chain needs separate qualification before
natural requests. Source guards preserve target role/phase mask3,layout in graph
cache identity,nonflash/single-KV-stream restrictions and originalk3 transaction;
runtime phase transitions,graph reuse/reset,KV rollback,reconciliation,originalR
versusR_SHADOW endpoints and observation invariance remainUNKNOWN. No actor loaded.

For a later S1B,retain the fixed24coordinates and3software baselines,216clean+
72separate trace hosts;2088total graph calls including288warmups,if separately
frozen and authorized. Clean graph source must exclude stage-copy observers
while charging Q/mask packing,output restore and complete all-stream sync in each
evaluation; setup/build/allocation remain separate. Profile andclean channels
must not be pooled. Current formal numeric graph/host cannot simply be relabeled
as clean timing. Its full-support census covered stage-output graphs only,so
future source/clean-wire support impact must be prospectively reviewed.

Software decision: actual full-tensor QH representation remains a plausible
software alternative,with no observed extra numerical capability beyondPQ/QB.
No clean cost/resource trace,new natural input,full actor endpoint or residual
best-software bottleneck evidence exists. SOFTWARE_FIRST/HOLD on hardware.
No new simulator,RTL,model/operator/GPU query,profile,automation or researchPR.
'''
    with (D/'NEXT_STAGE.md').open('x',encoding='utf-8',newline='\n') as out:out.write(text)
    print(f'CPU-only CaseC preparation complete: {len(tests)} tests, {ready}/24fixed timing contexts ready; no GPU admission.')
if __name__=='__main__':main()
