"""CPU audit of fixed selection, clean dependencies, static actor and budgets."""
import collections,datetime,json,shutil,re,hashlib
from pathlib import Path
from common import V,load,save,sha,pin
from pe_review import PE

OLD=Path('D:/hs113/benchmarks/rtx_lowering_envelope_v1')

def main():
    plan=load(V/'PLAN.json');rows=load(V/'CPU_CLEAN_REGISTRY.json')['records'];matrix=[]
    assert len(plan['descriptors'])==24 and len(plan['numerical_slots'])==240
    for d in plan['descriptors']:
        for layout in ('PQ','QB','QH_C'):
            pair={r['stage_outputs']:r for r in rows if r['descriptor_id']==d['id'] and r['layout']==layout}
            clean,numeric=pair[False],pair[True]
            # Ordinary dependency graph is constructed by the actual ggml DLL.
            # Graph(false) expands only ordinary; true additionally roots stage copies.
            assert clean['output']==numeric['output']
            cn={n['id']:n for n in clean['nodes']};nn={n['id']:n for n in numeric['nodes']}
            # Registry ids are assigned by traversal and can differ between the
            # two graphs. Compare node descriptors without positional ids/sources.
            def signature(n):
                d={k:v for k,v in n.items() if k not in ('id','src')}
                if re.fullmatch(r'node_\d+',d['name']):d['name']='AUTO_NODE_NAME'
                return d
            for n in cn.values():assert signature(n) in [signature(x) for x in nn.values()]
            def dependency_hash(nodes,index):
                if type(index)is int and index<0:return 'FULL_INPUT_ROLE_'+str(index)
                assert type(index)is int,'unresolved external leaf'
                node=nodes[index];body=dict(signature(node),sources=[dependency_hash(nodes,s) for s in node['src']])
                return hashlib.sha256(json.dumps(body,sort_keys=True).encode()).hexdigest()
            assert dependency_hash(cn,max(cn))==dependency_hash(nn,max(nn)),'ordinary arithmetic dependency identity'
            matrix.append(dict(descriptor=d['id'],layout=layout,clean_nodes=len(cn),numeric_nodes=len(nn),
                clean_ops=dict(collections.Counter(n['op'] for n in cn.values())),numeric_ops=dict(collections.Counter(n['op'] for n in nn.values())),
                clean_ordinary_dependency_graph=clean,numeric_diagnostic_graph=numeric))
    modules=load(V/'CPU_CLEAN_REGISTRY.json')['modules']
    assert not any(any(s in Path(p).name.lower() for s in ('cuda','cublas','vulkan')) for p in modules)
    save(V/'S1B_CPU_INTEGRATION.json',dict(status='CPU_GRAPH_AUDIT_COMPLETE_GPU_HOST_NOT_ADMITTED',actual_native_clean_graphs=72,actual_native_numeric_graphs=72,
        records=matrix,modules=modules,clean_graph_constructor='Graph(meta,layout,false): ordinary output is the sole expansion root; no numerical stage readback entry is executed in this CPU path',
        retained_costs='All Q packing, actual mask CONT/REPEAT, necessary CONT and ordinary output restoration remain ordinary dependencies; no arithmetic pruning or output crops',
        future_counts=dict(clean_hosts=216,trace_hosts=72,warmup_graphs=288,total_graph_calls=2088,clean_measured_evaluations=1728),
        measurement_contract=['CPU graph construction/allocation separately','input upload separately','complete clean evaluation and all-stream completion synchronization inside each evaluation','ordinary output readback and full correctness outside evaluation window','CUDA graph/caching mechanisms separately identified; inherited GGML_CUDA_DISABLE_GRAPHS=1 unchanged'],
        pending='No deployed clean timing loop, trace collector or S1B GPU F0 yet. Numerical host cannot be relabeled. Bridge stage-output census would not cover these clean graphs automatically.',
        GPU_queries=0,CUDA_loads=0,graph_computes=0))
    paths=[Path(x) for x in ('C:/Program Files/NVIDIA Corporation','C:/Program Files/NVIDIA GPU Computing Toolkit','C:/Program Files/NVIDIA Nsight Systems','C:/Program Files/NVIDIA Corporation/Nsight Systems')]
    found=[]
    for root in paths:
        if root.exists():
            for p in root.rglob('*'):
                if p.is_file() and (p.name.lower() in ('nsys.exe','ncu.exe') or 'cupti' in p.name.lower()):found.append(pin(p))
    save(V/'PROFILE_STATIC_REVIEW.json',dict(recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='PROFILE_UNAVAILABLE_NO_ADMITTED_COLLECTOR' if not found else 'TOOLS_PRESENT_COMPATIBILITY_UNESTABLISHED',
        PATH_tools={s:shutil.which(s) for s in ('nsys','ncu')},installation_files=found,profiler_invocations=0,CUDA_loads=0,
        compatibility='No admitted executable CUPTI/Nsight collector against frozen CUDA stack. Filesystem inspection alone cannot establish driver/runtime ABI or obtain kernel activities. No upgrade authorized.',hardware_decision='SOFTWARE_FIRST/HOLD'))
    source=OLD/'native/source';names=['src/hs_scope.h','src/llama-graph.cpp','src/llama-graph.h','src/llama-context.cpp','src/hsc_counter.h','common/hs_observer.h','tools/server/server-context.cpp']
    pins=[pin(source/n) for n in names]+[pin(OLD/'native/build/build.ninja')]
    ninja=(OLD/'native/build/build.ninja').read_text();line=next(s for s in ninja.splitlines() if s.startswith('build bin/llama-server.exe:'))
    assert 'ggml/src/ggml.a' in line and 'ggml/src/ggml-base.a' in line
    save(V/'ACTOR_STATIC_REVIEW.json',dict(status='NO_GO_FOR_NATURAL_REQUESTS',files=pins,actual_actor_link=line,
        shared_core='Operator Route A does not transfer to actor. Actual actor PE has no shared ggml core imports. Relinking actor plus transitive static llama/common/server references requires a separate bounded integration before any request.',
        phase='hs::decode uses actual hs_scope::guard(role,phase==prefill), mask3 targets both phases and excludes draft; real header/cache CPU checks separate',
        cache='Actual hs113_layout and hs_query_batch precede original ubatch/owner/sequence/sampler reuse checks. These source guards do not prove live cache invalidation.',
        q1='QH branch requires q->ne[2]>1; PQ/QB branches have width>1 restrictions. Actual q1 Bridge CPU graphs common; natural decoder q1 qualification unexecuted.',
        KV='llama_context owns memory; server slot.mem binds target/draft; reset clears request/speculative counters. verify path may restore target+draft checkpoints and sampler, then removes suffix beyond kept prompt position. Captured snapshot graph has no live KV transaction.',
        continuation='hs::move is conditional on inherited HS_TARGET_CONTINUATION_UB; it serializes/synchronizes source state, builds destination, clones sampler and carries a pending id without resampling. Source/clone ownership and failure cleanup need end-to-end testing; no producer policy added.',
        transaction='Original spec_draft/accepted.size-1, correction/bonus origin, common_speculative_accept, checkpoint restore and seq_rm rollback remain unchanged. k3 is a request/runtime contract, not enforced merely by these graph guards.',
        references='Original R retains PR104 original family-specific runtime. R_SHADOW would use rebuilt actor with original policy and requires independent endpoints/observer/state qualification. Neither new actor nor R_SHADOW was run.',
        risks=['duplicated static vs plugin core state','live KV ownership and reset/rollback','accepted/correction/bonus pending-token state','phase transition and stale graph reuse','nonflash single-KV-stream graph restrictions','observer invariance and original R endpoint identity'],
        model_loads=0,GPU_queries=0,CUDA_loads=0))
    # Validate the authenticated closure, without rerunning a scientific stage.
    e=OLD/'formal_numerical_v2/numerical_execution';fresh=load(e/'FRESH_AUDIT.json');assert fresh['members_verified']==19343 and fresh['actual_remote_archive_used_for_fresh_restore'] and fresh['frozen_analysis_byte_identical']
    assert sha(OLD/'formal_numerical_v2/formal_delivery/RAW_FORMAL_V2.zip')==fresh['archive_sha256']
    history=[]
    for d in (OLD/'S1_NUMERICAL',OLD/'GPU14_EXECUTION',OLD/'formal_numerical_v2'):
        for p in d.rglob('*'):
            if p.is_file():history.append(pin(p))
    # Includes old raw root: locks/failures/absence are a permanent witness.
    raw=Path('D:/hs113-formal-numerical-v2')
    for p in raw.rglob('*'):
        if p.is_file():history.append(pin(p))
    save(V/'HISTORY_BASELINE.json',dict(files=history,old720=dict(started_failed=1,unstarted=719,confirmed_complete=0),GPU14=dict(started=14,completed=14,failed=0),
        v2=dict(qualified=474,unstarted=246,repeats=237,contexts_complete=47,q_gt1_complete=29),closure=pin(e/'CLOSURE_REMOTE_VERIFIED.json'),fresh_audit=pin(e/'FRESH_AUDIT.json'),
        old_raw_root_absences={n:not (raw/n).exists() for n in ('NUMERICAL_ENDED.json','ANALYSIS.json')},
        old_raw_root_present={n:(raw/n).exists() for n in ('NUMERICAL_FAILED.json','NUMERICAL_WATCHDOG_STOP.json','ACTIVE_CONTROLLER.lock')}))
    budget=load(V/'BUDGET.json');limits=budget['limits']
    limits.update(controller_commit_bytes=512*1024**2,readiness_process_commit_bytes=256*1024**2,minimum_volume_free_before_start_bytes=4*1024**3,minimum_volume_free_during_stage_bytes=512*1024**2,
        finalization_reserve_seconds=5,qualification_reserve_seconds=5,numeric_producer_reservation_bytes=limits['numeric_nonCAS_bytes_per_slot']+budget['storage']['first_mutant_input_readback_reserve_bytes']+max(sum(d['stage_bytes'].values()) for d in plan['descriptors']))
    executable_nodes=sum(sum(not n['metadata_only'] for n in r['nodes']) for r in load(V/'CPU_GRAPH_EXPECTED.json'))*2
    budget['counts'].update(maximum_conhost_helpers=482,maximum_all_controlled_and_helper_process_starts=966,explicit_device_completion_sync_calls=480,
        explicit_backend_device_identity_calls=executable_nodes,explicit_buffer_type_calls=executable_nodes,explicit_buffer_type_device_identity_calls=executable_nodes,
        explicit_buffer_is_host_calls=executable_nodes,explicit_node_buffer_name_calls_upper_bound=3612,explicit_node_buffer_device_identity_checks=executable_nodes)
    budget['stages']['census'].update(console_helpers_max=2,all_processes_max=5)
    budget['stages']['numerical'].update(console_helpers_max=480,all_processes_max=961)
    budget['offline_CPU_delivery']=dict(wall_seconds=900,conservative_owned_seconds=2700,max_concurrent_processes=3,process_commit_bytes=2*1024**3,
        includes='separate final reanalysis, raw manifest/archive, one fresh restoration/reanalysis and authenticated transport/readback; no device activity; no full old archive duplication')
    budget['all_new_execution_and_delivery_owned_seconds']=9900
    budget['monitoring']='Stage wall includes actual in-controller identity hashing, readiness, child/console processes, native work, online full-byte controls and accounting. Conservative stage wall x3 charges controller+one child+one conhost. Independent25ms-requested deadline/memory/free-volume watcher performs no tree scan or analysis. Exclusive immutable files, pre-producer byte reservations, append-only fsynced byte journal, per-slot actual file reconciliation; full sizes+hashes every30 completed slots and at stage boundaries. Sampling/reconciliation gaps are not claimed zero. Child hard Job limits remain active2/commit; pipes capped32KiB.5s bounded finalization reserve; hard-exit capsule before approved wall ceiling. All raw evidence retained on stop.'
    budget['storage']['all_input_before_after_actual_read_bytes']=sum(sum(d['metadata'][k]['bytes'] for k in ('Q','K','V','mask')) for d in plan['descriptors'])*20
    budget['basis']=dict(old_observed_active_envelope_seconds_per_qualified_slot=3.6535017208711005,linear240_active_seconds=876.8404130090641,numerical_wall_margin_ratio=1800/876.8404130090641,
        limitation='Descriptive extrapolation, no guarantee240 complete within budget; no reset/continuation if exhausted. Full slot worst-case deadlines exceed stage cap. Independent new budget, no leftover reuse.',
        all_CPU_delivery_and_GPU_owned_bound_seconds=9900)
    # Keep original planner output as a provenance receipt; this is the final budget.
    save(V/'BUDGET_FINAL.json',budget)
    print('PASS CPU clean72/actor static review; history pinned',len(history),'members; Bridge count966 all-process starts incl helpers; no GPU')
if __name__=='__main__':main()
