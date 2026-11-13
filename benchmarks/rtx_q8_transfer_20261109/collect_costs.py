"""Complete durable reservations, native reports and overlapping host cost windows."""
from pathlib import Path
import collections,datetime,hashlib,json,sqlite3,sys
from admission import ROOT,put,sha
from execute import WORK,BASE

def read(p):return json.loads(Path(p).read_bytes())

def main(output=ROOT):
    db=sqlite3.connect((WORK/'ledger.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    attempts=[dict(x) for x in db.execute('SELECT * FROM attempts ORDER BY started')];db.close()
    assert all(x['status'] in ('COMPLETE','EXPECTED_REJECT') for x in attempts),'Unresolved/failed attempt requires explicit stopped report'
    detailed=[];stages=collections.defaultdict(lambda:dict(requests_reserved=0,rows_reserved=0,attempts=0,native_requests_reported=0,native_rows_reported=0,native_report_coverage_attempts=0,host_wall_s=0,measured_request_service_s=0,service_receipts=0))
    resource_min={};resource_max={};power_samples=0;telemetry_anomalies=[]
    for a in attempts:
        folder=WORK/'runs'/a['id'];host=read(folder/'HOST.json');row=dict(ledger=a,host=host,path=str(folder));stage=stages[a['stage']]
        stage['requests_reserved']+=a['requests'];stage['rows_reserved']+=a['rows'];stage['attempts']+=1;stage['host_wall_s']+=host['wall_seconds']
        if (folder/'COMPLETE.json').exists():
            c=read(folder/'COMPLETE.json');row['native_completion']=c;stage['native_requests_reported']+=c['actual_requests'];stage['native_rows_reported']+=c['actual_rows'];stage['native_report_coverage_attempts']+=1
        else:row['native_completion']=None
        if (folder/'RESULT_MARKERS.json').exists():
            markers=read(folder/'RESULT_MARKERS.json');row['actual_result_markers']=markers
            values=markers['markers'];tests=[x for x in values if x['name'].startswith('test-')]
            primers=[x for x in values if x['name'].startswith('primer-')]
            clock='native_main_to_pre_record_seconds'
            row['result_windows']=dict(first_any_result_from_native_main_s=values[0][clock] if values else None,
                first_test_result_from_native_main_s=tests[0][clock] if tests else None,
                test_burst_after_last_primer_s=tests[-1][clock]-primers[-1][clock] if tests and primers else None,
                test_first_to_last_result_s=tests[-1][clock]-tests[0][clock] if tests else None,
                scope='Native timestamp captured before receipt JSON writing; marker flushed after that write. Burst includes inter-request/reset/receipt overhead, not model-load time or token TTFT.')
        meta=folder/'native/result.json'
        if meta.exists():
            m=read(meta);row['native_model_load_s']=m.get('model_load_s');row['native_pool_setup_s']=m.get('pool_setup_s')
            for call in m.get('requests',[]):
                r=read(folder/'native'/call['record'])
                if 'service_seconds' in r:stage['measured_request_service_s']+=r['service_seconds'];stage['service_receipts']+=1
            row['same_work_costs']=[]
            for x in m.get('same_work',[]):
                r=read(folder/'native'/x['record'])
                fields=['operation_seconds','setup_seconds','save_seconds','restore_seconds','post_timer_output_and_state_seconds','elapsed_seconds','position','execution','capture','target_physical_width_hist','graphs_built','graphs_reused','planning_seconds','output_copy_seconds']
                row['same_work_costs'].append(dict(name=x['name'],**{k:r[k] for k in fields}))
        samples=folder/'resources.jsonl';count=0
        if samples.exists():
            for line in samples.read_text().splitlines():
                s=json.loads(line);count+=1
                for k in ('gpu_free','ram_free','output_free','system_free'):
                    resource_min[k]=min(resource_min.get(k,s[k]),s[k])
                for k in ('temperature_C','clock_MHz','power_W'):
                    try:value=float(s[k])
                    except (ValueError,TypeError):continue
                    resource_max[k]=max(resource_max.get(k,value),value)
                    if k=='clock_MHz' and value>10000:
                        telemetry_anomalies.append(dict(attempt=a['id'],sample_line=count,reported_clock_MHz=value,utc=s['utc'],
                            note='Implausible nvidia-smi reported graphics clock; original sample retained, no timing row removed or clock value imputed.'))
                if s.get('power_W') not in (None,'N/A','[N/A]'):power_samples+=1
        row['resource_samples']=count;detailed.append(row)
    new_req=sum(a['requests'] for a in attempts);new_rows=sum(a['rows'] for a in attempts)
    inherited=read(ROOT/'CUMULATIVE_LEDGER_INITIAL.json');assert sha(BASE/'ledger.sqlite')==inherited['sha256']
    gaps=[]
    for a,b in zip(attempts,attempts[1:]):
        gap=b['started']-a['ended']
        gaps.append(dict(previous=a['id'],next=b['id'],inter_attempt_wall_s=gap))
    ledger=dict(as_of_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),inherited_requests=904,inherited_reserved_rows=557528,
        new_requests=new_req,new_reserved_rows=new_rows,cumulative_requests=904+new_req,cumulative_reserved_rows=557528+new_rows,
        limits=dict(cumulative_requests=3072,cumulative_rows=4000000,new_requests=2048),stage_limits=dict(qualification=512,diagnostic=160,profiling=32,live=1152,closure=192),
        stages=dict(stages),attempts=attempts,refunds=0,original_ledger_unchanged=True,source_new_ledger_sha256=sha(WORK/'ledger.sqlite'))
    put(output/'CUMULATIVE_LEDGER.json',ledger)
    commands=[]
    for name in ('BUILD_PREPARATION.json','BUILD_V2.json'):
        for c in read(ROOT/name)['commands']:commands.append(c)
    costs=dict(stages=dict(stages),attempts=detailed,inter_attempt_gaps=gaps,profiling=dict(requests=0,rows=0,status='NOT_RUN_OPTIONAL',kernel_attribution=None),
        sampled_resource_minimum_bytes=resource_min,sampled_resource_maxima=resource_max,power_samples=power_samples,
        telemetry_anomalies=telemetry_anomalies,resource_maxima_scope='Raw reported maxima; anomalous driver telemetry is retained and does not establish actual operating clock.',
        build_commands=commands,recorded_build_command_wall_s=sum(c.get('seconds',c.get('wall_seconds',0)) for c in commands),
        total_initial_engineering_wall_s=None,missing_costs='Initial coordinator/source inspection and every individual helper command were not fully metered; retained timed subsets are not called a complete engineering total.',
        coverage='All reservations, complete/expected-negative native attempts and host windows retained; native actual rows missing for expected aborts stay null. Reserved work is never refunded.',
        clocks='Inclusive load/setup/first-result/burst/worker/wrapper clocks overlap. No summation across overlapping windows. Native host decode clocks include synchronization; residual is unassigned, not logging or kernel time.',
        memory='Device-global free memory sampled every2s; extrema are sampled, not guaranteed per-process peaks. GPU power is not whole-system power.',
        inherited_costs='PR195904-request snapshot retained separately; its partial service coverage is not pooled with new timing.')
    put(output/'COMPLETE_COSTS.json',costs)
    print(json.dumps(dict(new_requests=new_req,new_rows=new_rows,cumulative_requests=904+new_req,cumulative_rows=557528+new_rows,stages=dict(stages)),indent=2),flush=True)

if __name__=='__main__':main(Path(sys.argv[1]) if len(sys.argv)>1 else ROOT)
