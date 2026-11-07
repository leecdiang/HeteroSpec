import ast,collections,math,statistics,shutil,sys
from pathlib import Path
from common import V,load,save,sha,pin
from pe_review import PE
import audit
OLD=Path('D:/hs114-bridge-v2/benchmarks/rtx_lowering_envelope_v1/s1a_bridge_v2')
def main():
    for p in V.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'),filename=str(p))
    plan=load(V/'PLAN.json');rows=load(V/'CPU_GRAPHS_FINAL2.json')['records'];assert len(rows)==72
    inherited=load('D:/hs113-bridge/benchmarks/rtx_lowering_envelope_v1/s1a_bridge_v1/S1B_CPU_INTEGRATION.json')
    table={(r['descriptor'],r['layout']):r for r in inherited['records']};expected=[];counts=collections.defaultdict(list)
    for r in rows:
        key=r['descriptor_id'],r['layout'];old=table[key]
        assert audit.signature(r)==audit.signature(r['numeric_graph'])==audit.signature(old['clean_ordinary_dependency_graph'])
        assert r['nodes']==old['clean_ordinary_dependency_graph']['nodes']
        numeric=next(g for g in load(OLD/'CPU_GRAPH_EXPECTED.json') if (g['descriptor_id'],g['layout'])==key)
        assert r['numeric_graph']['nodes']==numeric['nodes']
        d=next(d for d in plan['descriptors'] if d['id']==key[0]);counts[(r['layout'],d['q'])].append(len(r['nodes']))
        assert len(r['nodes'])<len(r['numeric_graph']['nodes'])
        expected.append({k:v for k,v in r.items() if k!='numeric_graph'})
    save(V/'CPU_EXPECTED_FINAL.json',expected)
    N=sum(len(r['nodes']) for r in rows);E=sum(sum(not n['metadata_only'] for n in r['nodes']) for r in rows)
    cpu=load(V/'CPU_GRAPHS_FINAL2.json');assert cpu['new_CUDA_loads']==cpu['new_GPU_queries']==cpu['graph_computes']==0
    links={}
    for role in ['clean','trace']:
        imp=PE(V/f's1b_{role}.exe').imports();assert 'ggml_init' in imp['ggml-base.dll'] and 'ggml_gallocr_alloc_graph' in imp['ggml-base.dll'];links[role]=dict(host=pin(V/f's1b_{role}.exe'),imports=imp)
    save(V/'CPU_GRAPH_REVIEW_FINAL.json',dict(status='PASS',actual_clean_graphs=72,actual_native_serializer_roundtrips=72,clean_ordinary_dependency_signatures_equal_numeric=72,legacy_S1B_graph_node_records_equal=72,PR116_numeric_graph_node_records_equal=72,complete_actual_AV_to_ordinary_words=cpu['actual_PR116_AV_to_ordinary_words_checked'],node_counts=[dict(layout=l,q=q,counts=sorted(set(v))) for (l,q),v in counts.items()],support_queries_per_complete_census=N,executable_nodes_per72=E,links=links,qualification='Actual CPU graph/storage/serializer proof only. CUDA clean ordinary and allocator placement are NOT_ESTABLISHED;must validate real warmups before measured windows.',GPU_queries=0,CUDA_plugin_loads=0,graph_computes=0))
    cas={}
    def add(p):r=pin(p);cas[r['sha256']]=r
    for d in plan['descriptors']:
        root=Path(d['root']);add(root/'snapshot.json')
        for role in ['Q','K','V','mask']:add(root/d['metadata'][role]['file'])
    for s in plan['clean_slots'][:72]:add(s['ordinary_reference']['path'])
    save(V/'CAS_INDEX_FINAL.json',list(cas.values()))
    basis=load(V/'STORAGE_BASIS.json');immutable=sum(r['bytes'] for r in cas.values());mutation=2*basis['maximum_input_bytes'];records=288*1024*1024
    raw=immutable+basis['all_2088_ordinary_outputs_no_dedup_bytes']+mutation+records+8*1024**2+16*1024**2+72*4*1024**2
    archive=raw+raw//50+16*1024**2;allbytes=2*raw+3*archive+192*1024**2;assert allbytes<4*1024**3
    stages={s:dict(wall_seconds=600,owned_seconds=1800,native_seconds=240 if s=='census' else 60,readiness_seconds=10,native_hosts=1 if s=='census' else 72,graph_computes=0 if s=='census' else 648,controlled_process_starts=5 if s=='census' else 289) for s in ['census','clean0','clean1','clean2']}
    save(V/'BUDGET_FINAL.json',dict(stages=stages,limits=dict(controller_commit=512*1024**2,native_commit=2*1024**3,readiness_process_commit_bytes=256*1024**2,disk_free_before=4*1024**3,disk_free_during=512*1024**2,raw_bytes=raw,per_host_reserve=8*1024**2,per_host_nonCAS=1024**2,census_nonCAS=8*1024**2,pipe_bytes=32768,deadline_reserve_seconds=5,job_active2=True),
        original_S1B=dict(clean_hosts=216,trace_hosts=72,graph_calls=2088,warmups=288,clean_measured=1728,trace_measured=72),
        currently_registered_executable_stages=dict(native_support_hosts=1,native_clean_hosts=216,native_trace_hosts=0,controllers=4,readiness_queries=217,conhost_helpers=434,total_controlled_starts=872,graph_calls=1944,warmups=216,support_API_queries=4*N,explicit_context_completion_sync_calls=2160,explicit_backend_device_identity_calls=216,explicit_default_buffer_type_calls=216,explicit_buffer_owner_device_calls=3*(E+4*72),internal_driver_API_calls='UNKNOWN'),
        trace_reserved_NOT_ADMITTED=dict(hosts=72,graph_calls=144,warmups=72,readiness_queries=72,support_API_queries=N,explicit_completion_sync_calls=216,maximum_profile_bytes_per_host=4*1024**2,wall_seconds_proposed=600,owned_seconds_proposed=1800,collector_process_count='UNRESOLVED:requires collector identity,ABI,process and overhead registration before any trace authorization',whole_original_S1B_cannot_be_reported_complete=True),
        offline_CPU_delivery=dict(wall_seconds=900,conservative_owned_seconds=15300,normal_job_active=2,transport_job_active=16,controller_commit=512*1024**2,job_commit=4*1024**3,includes='All registered audit/archive/restore/gh/Git actions. CPU transport max16descendants+controller=17;normal jobs x3. No uncharged automatic retry.'),
        storage=dict(immutable_full_input_reference_bytes=immutable,all_output_no_dedup_bytes=basis['all_2088_ordinary_outputs_no_dedup_bytes'],first_mutation_reserve=mutation,nonCAS_metadata_logs_bytes=records,trace_files_reserved_bytes=72*4*1024**2,raw_upper_bound_bytes=raw,archive_upper_bound_bytes=archive,raw_copies=2,archive_copies=2,preparation_Git_allowance=archive+192*1024**2,Git_archive_object_copy_bytes=archive,all_derived_upper_bound_bytes=allbytes,limit_bytes=4*1024**3,input_readback_traffic=basis['input_readback_traffic']),
        basis='Independent budgets,not unused PR116 capacity. Prior numerical463s/240instrumented hosts is context only,not a timing estimate. Per-host deadlines do not guarantee complete panel within stage cap.',monitoring='Native/readiness Windows Job active2 and commit limits;requested25mscontroller/50mschild polling,not guaranteed maximum gaps. Immutable per-slot observations,CAS full-byte reads and occurrence records;append-only storage ledger,full reconciliation every18hosts.5sdurable stop reserve. No extra GPU polling.'))
    # Statistical implementation test: synthetic CPU records are never GPU times.
    synthetic=[]
    for i,s in enumerate(plan['clean_slots']):
        value={'PQ':4,'QB':2,'QH_C':1}[s['layout']]
        synthetic.append(dict(**{k:s[k] for k in ['descriptor','family','phase','q','layer','layout','block']},process_identity=[i+1,100+i],qualified=True,mean_FG_ms=value,mean_FGH_ms=value+1))
    result=audit.aggregate(synthetic,plan);assert result['status']=='COMPLETE_CLEAN_PANEL' and all(r['speed_ratio']==2 for r in result['contrasts'])
    assert audit.aggregate(synthetic[:-1],plan)['status']=='INCOMPLETE_WITHHOLD_AGGREGATES'
    failures=[]
    for label,rs in [('duplicate',synthetic+[synthetic[0]]),('reused_process',[dict(r,process_identity=[1,1]) for r in synthetic]),('zero',[dict(r,mean_FG_ms=0) for r in synthetic])]:
        try:audit.aggregate(rs,plan)
        except AssertionError:failures.append(label)
    assert len(failures)==3
    save(V/'CPU_STATISTICS_TESTS_FINAL.json',dict(status='PASS',synthetic_216_hosts=True,contrasts=144,complete_and_missing_panel_controls=True,negative_rejections=failures,GPU_timings_generated=False))
    print('PASS72clean dependence graphs;actual AV bytes;support node count',N,';storage',allbytes,'<4GiB')
if __name__=='__main__':main()
