"""Construct all real wires/reference CAS and resource bounds, CPU/disk only."""
import struct
from common import V,RUN,load,save,sha,pin,retain,stage_sizes
from pathlib import Path
B=V.parent
def main():
    old=load(B/'repair_timer_v1/GPU14_F0.json');source=load(B/'DESCRIPTOR_PLAN.json')
    ds=[d for d in source['descriptors'] if d['kind']=='ACTUAL_FULL_SNAPSHOT'];assert len(ds)==72
    families=('Qwen','SmolLM2','Llama');layouts=('MQ','PQ','QB','QH_C','QH_D')
    for d in ds:
        parts=d['id'].split('_');d['family']=parts[0];d['layer']=int(parts[1][1:]);d['phase']=parts[2];d['q']=int(parts[3][1:])
    ds.sort(key=lambda d:(d['q']!=1,families.index(d['family']),d['layer'],('prefill','continuation').index(d['phase']),d['q']))
    original_graphs=load(B/'repair_timer_v1/CPU_REGISTRY_release.json')['records']
    graphs={(g['descriptor_id'],g['layout']):g for g in original_graphs if g['stage_outputs']}
    root='D:/hs113-formal-numerical-v2';refs={};slots=[];unique_inputs={};immutable={};max_input=0
    for d in ds:
        p=Path(d['root']);m=load(p/'snapshot.json');assert m==d['metadata']
        input_files=[];files={}
        for name,h in d['registry'].items():
            fp=p/name;assert sha(fp)==h
            files[name]=retain(V/'reference_cas',fp.read_bytes());immutable[h]=fp.stat().st_size;input_files.append(pin(fp))
        for k in ('Q','K','V','mask'):unique_inputs[files[m[k]['file']]['sha256']]=m[k]['bytes']
        historical={}
        for l in ('PQ','QB'):
            for r in (0,1):
                for s in ('QK','softmax','AV'):
                    fp=Path(old['old_operator_root'])/('%03d'%d['snapshot_index'])/(l+'-r'+str(r))/(s+'.bin')
                    historical[l+'-r'+str(r)+'/'+s]=retain(V/'reference_cas',fp.read_bytes());immutable[sha(fp)]=fp.stat().st_size
        mask=(p/m['mask']['file']).read_bytes();visible=[]
        for j in range(d['q']):
            active=[key for key in range(m['mask']['ne'][0]) if struct.unpack_from('<f',mask,key*m['mask']['nb'][0]+j*m['mask']['nb'][1])[0]!=float('-inf')]
            assert active and all(struct.unpack_from('<f',mask,key*m['mask']['nb'][0]+j*m['mask']['nb'][1])[0]==0.0 for key in active)
            visible.append(dict(query_row=j,count=len(active),first=min(active),last=max(active),indices=active))
        d['visibility']=dict(padded_key_extent=m['K']['ne'][1],visible_keys_by_query=visible,cache_min_at_operator=m['cache_min_at_operator'],cache_max_at_operator=m['cache_max_at_operator'],
            semantics='Visible keys independently counted from complete frozen 0/-inf masks, never inferred from padded extent or treated as unseen prompts')
        d['stage_bytes']=stage_sizes(m);d['input_files']=input_files
        refs[d['id']]=dict(files=files,historical=historical,metadata_file=files['snapshot.json'])
        max_input=max(max_input,sum(m[k]['bytes'] for k in ('Q','K','V','mask')))
        for l in layouts:
            for repeat in (0,1):
                i=len(slots);slots.append(dict(run_id=RUN,stage='NUMERICAL',kind='numeric',index=i,id=f'v2/numeric/{i:03d}/{d["id"]}/{l}/r{repeat}',descriptor=d['id'],
                    family=d['family'],layer=d['layer'],phase=d['phase'],q=d['q'],root=d['root'],layout=l,repeat=repeat,old_index=d['snapshot_index'],
                    graph_computes=1,warmups=0,registered_support_queries=len(graphs[d['id'],l]['nodes']),input_files=input_files,
                    runtime_directory=old['runtime_directory'],core_sha256=old['numerical_DLLs']['ggml-base.dll'],registry_sha256=old['numerical_DLLs']['ggml.dll'],cuda_plugin_sha256=old['numerical_DLLs']['ggml-cuda.dll'],
                    cas_root=root+'/cas',native_output=root+f'/numerical/{i:03d}/native'))
    assert len(slots)==720 and sum(s['q']==1 for s in slots)==180 and all(s['q']==1 for s in slots[:180])
    qs=sum(s['registered_support_queries'] for s in slots);assert qs==10836
    census=dict(run_id=RUN,stage='CENSUS',id='v2/support/complete360',kind='support',runtime_directory=old['runtime_directory'],core_sha256=old['numerical_DLLs']['ggml-base.dll'],
        registry_sha256=old['numerical_DLLs']['ggml.dll'],cuda_plugin_sha256=old['numerical_DLLs']['ggml-cuda.dll'],cas_root=root+'/cas',native_output=root+'/census/native',graph_computes=0,warmups=0,registered_support_queries=5418)
    save(V/'PLAN.json',dict(schema=1,run_id=RUN,execution_root=root,descriptors=ds,numerical_slots=slots,census_wire=census,
        layouts=list(layouts),primary_QH='QH_C',QH_D='Original fixed contrast; never a replacement selected using new outputs',input_exposure='All72 are exposed PR104 operator snapshots, not unseen prompts',
        order='All18 q1 contexts first, then54 q>1; fixed family Qwen/SmolLM2/Llama, numeric layer, prefill then continuation, q; each context MQ/PQ/QB/QH_C/QH_D and r0/r1 in adjacent fresh processes',
        independent_input_contexts=72,distinct_context_layouts=360,technical_process_repeats=2,support_API_queries=qs+5418))
    save(V/'REFERENCE_INDEX.json',refs)
    subset=[graphs[d['id'],l] for d in ds for l in layouts];save(V/'EXPECTED_GRAPHS.json',subset)
    # Hard caps on non-CAS records/logs plus a no-dedup assumption for all new outputs.
    # Complete valid input readbacks can reuse verified immutable blobs. A first
    # mutant readback is retained before terminal rejection, covered separately.
    outputs=sum(sum(d['stage_bytes'].values())*10 for d in ds)
    immutable_bytes=sum(immutable.values());mutant_reserve=2*max_input
    noncas_numeric=720*256*1024;noncas_census=16*1024**2;control=16*1024**2
    raw=immutable_bytes+outputs+mutant_reserve+noncas_numeric+noncas_census+control
    zip_bound=raw+(raw//100)+1024**2 # conservative stored/deflate expansion + headers
    # live CAS/raw + one fresh raw restoration + repo archive + downloaded archive.
    # User delivery links to the repo ZIP instead of creating a third full ZIP copy.
    preparation_and_git=384*1024**2
    all_bound=2*raw+2*zip_bound+preparation_and_git
    assert all_bound<4*1024**3,(all_bound,raw)
    save(V/'BUDGET.json',dict(status='PREPARED_NOT_EXECUTED',counts=dict(numerical_hosts=720,support_hosts=1,readiness_processes=721,controllers=2,
        controlled_process_starts=1444,numerical_graph_calls=720,support_graph_calls=0,numerical_support_API_queries=10836,census_support_API_queries=5418,total_support_API_queries=16254,
        explicit_nvidia_smi_queries=721,backend_loads=721,backend_init_by_name=721,model_requests=0,warmups=0,extra_smoke=0,scientific_retries=0,
        internal_driver_API_queries='UNKNOWN; explicit process/API counts are not internal enumeration counts'),
        stages=dict(census=dict(controllers=1,native_hosts=1,readiness_processes=1,controlled_starts=3,wall_seconds=600,owned_bound_seconds=1200),
                    numerical=dict(controllers=1,native_hosts=720,readiness_processes=720,controlled_starts=1441,wall_seconds=3000,owned_bound_seconds=6000)),
        limits=dict(cumulative_owned_seconds=7200,total_derived_bytes=4*1024**3,census_native_seconds=240,numerical_native_seconds=60,readiness_seconds=10,native_process_commit_bytes=2*1024**3,
            job_active_process_limit=1,numeric_nonCAS_bytes_per_slot=256*1024,census_nonCAS_bytes=noncas_census,control_bytes=control,stdout_bytes_per_child=32768,stderr_bytes_per_child=32768,
            raw_root_bytes=raw,single_blob_bytes=16*1024**2),
        storage=dict(snapshot_input_logical_bytes=sum(sum(d['metadata'][k]['bytes'] for k in ('Q','K','V','mask')) for d in ds),
            unique_input_bytes=sum(unique_inputs.values()),complete_immutable_reference_unique_bytes=immutable_bytes,all720_outputs_no_dedup_bytes=outputs,
            first_mutant_input_readback_reserve_bytes=mutant_reserve,numeric_record_log_envelopes_bytes=noncas_numeric,census_envelope_bytes=noncas_census,
            raw_upper_bound_bytes=raw,archive_upper_bound_bytes=zip_bound,raw_copies=2,archive_copies=2,preparation_git_metadata_allowance_bytes=preparation_and_git,
            all_derived_upper_bound_bytes=all_bound,scheme='Full actual reads before/after; compare full bytes; hash-addressed complete blobs; per-occurrence PID/slot/size/hash receipts; retain first mutation bytes before stop. No downsampling or assumed output equality.'),
        monitoring='Frozen execution controller uses Windows kill-on-close Job Object, active limit1, commit limit; pipe readers enforce byte caps, 50ms watchdog plus sampled disk/slot caps and fail-closed budget reservation. Whole-controller wall x2 per stage; census1200+numeric6000=7200 maximum. Poll intervals are requested scheduling, not guaranteed maximum gaps; checkpoint readiness is not periodic GPU monitoring or continuous residency.',
        exhaustion='Terminal retain/mark all remaining planned slots unstarted; no budget reset or guaranteed completion from worst-case per-process deadlines'))
    print('Prepared72x5x2; immutable reference CAS',immutable_bytes,'bytes; conservative all-derived',all_bound,'<4GiB; GPU starts0')
if __name__=='__main__':main()
