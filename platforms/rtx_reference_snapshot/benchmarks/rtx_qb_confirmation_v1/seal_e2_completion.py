"""CPU E2 completion accounting, all-session/task contrasts; no native starts."""
import csv
from pathlib import Path
import shutil
import experiment as e

ROOT=Path('D:/hs-qb-confirmation-v02');OUT=Path(__file__).parent/'e2_completed_20261015'
def csvfile(name,rows):
    with (OUT/name).open('x',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
    e.require(not (ROOT/'EXECUTION.lock').exists() and (ROOT/'SESSION-5-COMPLETE.json').exists(),'E2 not complete')
    OUT.mkdir(exist_ok=False);analysis=e.analyze(ROOT)
    e.require(analysis==e.read(ROOT/'exact_restoration_20261015/E2_ANALYSIS.json'),'completion reanalysis differs')
    e.save(OUT/'ANALYSIS.json',analysis)
    events=[e.read(p) for p in (ROOT/'ledger').glob('*.json')]
    records=[e.read(p) for p in (ROOT/'runs').rglob('RECORD.json')]
    life=sum(e.read(p)['seconds'] for p in (ROOT/'runs').rglob('LIFETIME.json'))
    keys=('target_prefill_calls','target_continuation_calls','draft_prefill_calls','draft_continuation_caller_calls',
          'physical_micrograph_calls','physical_micrograph_rows','target_verification_calls','target_replay_calls')
    counters={k:sum(r.get('workload',{}).get(k,0) for r in records) for k in keys}
    counts=dict(status='COMPLETED_QUALIFIED_FINITE_PANEL',completed_sessions=list(range(6)),
                request_starts=sum(x['kind']!='load' for x in events),workers=sum(x['kind']=='load' for x in events),
                warmups=sum(r['warmup'] for r in records),completed_records=len(records),
                scientific_request_failures=len(list((ROOT/'runs').rglob('FAILED.json'))),
                failed_blocks=sum(e.read(p)['status']!='COMPLETED' for p in (ROOT/'blocks').glob('*.json')),
                invalid_contracts=sum(not r['contract_valid'] for r in records),
                workload_errors=sum(bool(r['workload_error']) for r in records),
                heavy_observer_flags=sum(any(r['observation'].values()) for r in records),
                output_mismatches=sum(len(r['mismatches']) for r in analysis['comparisons']),
                unstarted_E2_slots=0,native_owned_seconds=life,observed_workload_counters=counters,
                logical_model_caller_invocations=sum(counters[k] for k in keys[:4]),
                hardware_kernel_starts='UNKNOWN',all_auxiliary_OS_processes='NOT_GLOBALLY_CAPTURED',
                this_resumption_native_workers=54,this_resumption_requests=270,
                this_resumption_native_owned_seconds=life-4149.035876499896,
                E1_status='BUILT_NOT_STARTED_PENDING_AUTHENTICATED_F0')
    e.require(counts['request_starts']==1620 and counts['workers']==324 and len(records)==1620,'E2 slot count incomplete')
    e.save(OUT/'COUNTS.json',counts)
    sessions=[];tasks=[];estimates=[]
    for c in analysis['comparisons']:
        sessions.extend(dict(family=c['family'],path=c['path'],**r) for r in c['session_log_contrasts'])
        tasks.extend(dict(family=c['family'],path=c['path'],**r) for r in c['task_ratios'])
        x=c['estimate'];estimates.append(dict(family=c['family'],path=c['path'],status=c['status'],ratio=x['speed_ratio_PQ_over_QB'],
                                             lower=x['session_cluster_percentile_interval'][0],upper=x['session_cluster_percentile_interval'][1],
                                             interpretation='practical improvement evidence' if x['speed_ratio_PQ_over_QB']>1.02 else 'weak/no practical difference',
                                             interval_entirely_above_1_02=x['interval_entirely_above_threshold']))
    csvfile('SESSION_CONTRASTS.csv',sessions);csvfile('TASK_CONTRASTS.csv',tasks);csvfile('PQ_QB.csv',estimates)
    csvfile('REQUEST_LATENCIES.csv',[dict(session=r['followup_block']['session'],family=r['family'],arm=r['condition'],slot=r['slot'],warmup=r['warmup'],
                                             latency_ms=r['wall_ms'],output_length=r['output']['length'],stop_reason=r['output']['stop_reason'],
                                             pid=r.get('pid'),contract_valid=r['contract_valid']) for r in records])
    for name in ('AUTHENTICATED_READBACK.json','CONTROLLER_STARTED.json','CONTROLLER_COMPLETE.json'):
        shutil.copyfile(ROOT/'exact_restoration_20261015'/name,OUT/('RESTORATION_'+name))
    for i in range(6):
        shutil.copyfile(ROOT/f'SESSION-{i}.json',OUT/f'SESSION-{i}.json')
        shutil.copyfile(ROOT/f'SESSION-{i}-COMPLETE.json',OUT/f'SESSION-{i}-COMPLETE.json')
    print(counts)
if __name__=='__main__':main()
