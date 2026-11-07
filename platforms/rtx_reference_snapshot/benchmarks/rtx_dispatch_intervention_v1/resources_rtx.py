"""CPU-derived scoped counts and conservative process-owned accounting."""
import datetime,platform,sys,time
from pathlib import Path
from common import V,load,save,sha
from prepare_rtx import root
from close_rtx import allocation
def main():
    r=root();s=load(r/'RUN_SPEC.json');hosts=[];jobs=[];profile=0
    for a in (r/'attempts').iterdir():
        hosts.append(load(a/'host.LIFETIME.json'));jobs.append(load(a/'host.JOB_EVENTS.json'));profile+=load(a/'JOB.json')['profile']
    controllers=[]
    for start in r.glob('*_STARTED.json'):
        name=start.name[:-len('_STARTED.json')];end=r/(name+'_ENDED.json');fail=r/(name+'_FAILED.json');finish=end if end.exists() else fail if fail.exists() else None
        if not finish:continue
        a=load(start);b=load(finish);seconds=datetime.datetime.fromisoformat(b['utc']).timestamp()-a['epoch'];controllers.append(dict(stage=name,pid=a['pid'],wall_seconds=seconds,receipt=finish.name,status=b.get('status','FAILED')))
    telemetry=list((r/'environment').glob('*.json'));C0=list((r/'CAPABILITY').glob('SMI_*.json'));actual=sum(len(j['started_unique_PIDs']) for j in jobs);native=len(hosts);environment=[load(p) for p in telemetry]
    result=dict(native_hosts=native,native_completed_with_exit0=sum(x['exit_code']==0 for x in hosts),native_failed=sum(x['exit_code']!=0 for x in hosts),profile_attempts=profile,owned_native_and_console_starts=actual,console_starts=actual-native,SMI_queries=len(telemetry)+len(C0),C0_NVML_API_calls=0,node_support_query_count_basis='two Graph.registry(backend) traversals per completed native graph;no hidden census host',native_command_wall_sum_seconds=sum(x['seconds'] for x in hosts),controller_stage_wall_seconds=sum(x['wall_seconds'] for x in controllers),native_helper_controller_conservative_owned_seconds=2*sum(x['seconds'] for x in hosts)+sum(x['wall_seconds'] for x in controllers),owned_scope='native plus its bounded console lifetime counted conservatively;stage controllers separately;not a whole-machine or all-tool process ledger',peak_observed_native_Job_commit_bytes=max(x['peak_job_commit_bytes'] for x in hosts),native_job_commit_limit_bytes=s['host_RAM_bytes'],memory_scope='actual native Job peak;controller guard enforces its8GiB limit,combined full-task OS peak not certified',elapsed_since_dispatch_seconds=time.time()-s['start_epoch'],global_seconds=s['global_seconds'],delivery_reserve_seconds=s['delivery_reserve_seconds'],controllers=controllers,SM_clock_gate=False,reported_endpoint_temperature_max_C=max(x['temperature'] for x in environment),reported_endpoint_utilization_max=max(x['utilization'] for x in environment),all_endpoint_identity_ok=all(x['identity_ok'] for x in environment),actual_block_environment={p.stem:load(p)['environment_qualified'] for p in r.glob('*BLOCK_*.json')},storage=allocation([r,Path(str(r)+'-archive'),Path(str(r)+'-fresh')]),GPU_calls_added=0)
    save(r/'RESOURCE_SUMMARY.json',result)
    save(r/'CPU_EXECUTION_IDENTITY_POSTCHECK.json',dict(python_path=sys.executable,python_sha256=sha(sys.executable),python_version=sys.version,OS=platform.platform(),scope='postcheck identity;interpreter path was registered prospectively,executable hash recorded now,not backdated'))
    files=[Path('D:/hs104-e1-v1/native/build/CMakeCache.txt'),Path('D:/hs104-e1-v1/native/build/build.ninja'),Path('D:/hs104-e1-v1/native/source/ggml/src/ggml-cuda/ggml-cuda.cu')]
    save(r/'BACKEND_BUILD_RECORDS.json',dict(files={str(p):sha(p) for p in files if p.exists()},scope='retained original build provenance and actual kernel trace;not a rebuilt numerical stack',graphs_option='GGML_CUDA_GRAPHS:BOOL=ON'))
    print(result['native_hosts'],result['SMI_queries'],result['peak_observed_native_Job_commit_bytes'])
if __name__=='__main__':main()
