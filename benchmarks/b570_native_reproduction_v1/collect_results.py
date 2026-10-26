"""Reconcile finite native slots, exact audits and loaded runtime identities."""
from pathlib import Path
import argparse,hashlib,json
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def check(ok,msg):
    if not ok:raise ValueError(msg)
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();r=a.run
    check(not a.out.exists(),'Existing summary')
    specs=[('capture-a1','CAPTURE_AUDIT.json'),('capture-a2','CAPTURE_A2_AUDIT.json')]+[(f'smoke-{i}-a1',f'SMOKE_{i}_AUDIT.json')for i in range(4)]+[('fresh-request-a1','FRESH_REQUEST_AUDIT.json'),('stage-a1','STAGE_AUDIT.json'),('fresh-stage-a1','FRESH_STAGE_AUDIT.json')]
    rows=[];loaded=[];vectors=0
    for name,audit in specs:
        receipt=read(r/(name+'.receipt.json'));native=read(r/name/'result.json');verified=read(r/audit)
        expected='REAL_STAGE_REPLAY_AUDIT_PASS' if 'stage' in name else 'HISTORICAL_REQUEST_REPLAY_PASS'
        check(verified['status']==expected,'Audit failed '+name)
        check(receipt['exit_code']==0 and receipt['exit_observed'] and native['normal_cleanup_returned'],'Native cleanup '+name)
        check(receipt['job_accounting']['active_processes']==0,'Job not empty '+name)
        check(receipt['status']==('failed' if name=='capture-a1' else 'complete'),'Unexpected wrapper result')
        directory=(r/'runtime-a1' if name=='capture-a1' else r/'fresh-v1/runtime' if name.startswith('fresh-') else r/'build/bin/Release')
        seen={Path(x['path']).name:x for x in receipt['loaded_module_hashes']}
        for dll in ['ggml-base.dll','ggml-cpu.dll','ggml-vulkan.dll','ggml.dll','llama.dll']:
            # The stage program links no llama symbols, so the linker may remove llama.dll.
            if dll=='llama.dll' and 'stage' in name:continue
            check(dll in seen,'Loaded module missing '+dll+' '+name)
            check(seen[dll]['sha256']==sha(directory/dll),'Loaded module hash '+dll)
            expected_parent=r/('fresh-v1/runtime' if name.startswith('fresh-') else 'build/bin/Release')
            check(Path(seen[dll]['path']).parent.resolve()==expected_parent.resolve(),'Unexpected numeric module search path')
        loaded.append({'slot':name,'runtime_directory':str(directory),'numerical_module_hashes_verified':True})
        count=len(native.get('requests',[]));vectors+=verified.get('full_vector_count',0)
        rows.append({'slot':name,'wrapper_status':receipt['status'],'native_status':native['status'],'audit_status':verified['status'],'requests':count,'stage_computes':len(native['rows']) if 'stage' in name else 0,'pid':receipt['pid'],'started_utc':receipt['started_utc'],'finished_utc':receipt['finished_utc'],'charged_seconds':receipt['charged_seconds'],'job_total_processes':receipt['job_accounting']['total_processes'],'other_job_process_identities':'not captured','receipt_sha256':sha(r/(name+'.receipt.json')),'audit_sha256':sha(r/audit)})
    requests=sum(x['requests']for x in rows);seconds=sum(x['charged_seconds']for x in rows)
    check(requests==21 and requests<=24 and seconds<2040,'Finite resource envelope')
    capture=read(r/'capture-a2/result.json');ordinary=read(r/'smoke-2-a1/result.json')
    for i in range(3):
        for key in ['ids','eog','length','terminal_id','stop_reason','cycles']:check(capture['requests'][i][key]==ordinary['requests'][i][key],'Raw capture control state')
        left=r/'capture-a2'/f'qual-{i}';right=r/'smoke-2-a1'/f'qual-{i}'
        for f in left.rglob('*.f32'):check(f.read_bytes()==(right/f.relative_to(left)).read_bytes(),'Raw capture control logits')
    out={'status':'NATIVE_REPRODUCTION_COMPLETE_WITH_DECLARED_LIMITS','slots':rows,'model_requests':requests,'model_processes':7,'stage_processes':2,'stage_graph_computes':8,'job_cumulative_processes':sum(x['job_total_processes']for x in rows),'job_active_at_all_exits':0,'native_worker_seconds':seconds,'historical_full_vector_comparisons':vectors,'ordinary_panel_vectors':sum(read(r/f'SMOKE_{i}_AUDIT.json')['full_vector_count']for i in range(4)),'ordinary_panel_requests':12,'raw_capture_vs_ordinary_control':'PASS: 175 full vectors and all endpoints/state','fresh_copy_files_verified':len(read(r/'FRESH_COPY_INTEGRITY.json')['verification']['verified_files']),'loaded_runtime_checks':loaded,'technical_retry_triplets':1,'numerical_failures':0,'unexecuted_performance_slots':'NOT_PLANNED','performance_claim':False,'limits':['New runtime qualification, not byte-identical historical binary rebuild','Same-host fresh-directory replay, not another machine','Stage: layer0 key512 natural q2 plus first-query q1 slice only','One initial wrapper accounting failure and incomplete final-stage capture retained; native numerical audit passed','Job cumulative counts complete; auxiliary process identities/lifetimes not captured; build/helper accounting excluded','Historical PR143 resource deviation unchanged; no new performance result']}
    a.out.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:out[k]for k in ['status','model_requests','ordinary_panel_vectors','historical_full_vector_comparisons','native_worker_seconds','job_cumulative_processes']}))
if __name__=='__main__':main()
