"""Reconstruct real monitoring intervals; never apply v3 to old receipts."""
import pathlib
from legacy import load,sha,need,audit_raw,OLD
from timing import Coverage
from workers import rows

def audit(folder):
    life=load(folder/'LIFECYCLE.json')
    need(life.get('schema')=='SUPERVISION_V4','only new v4 receipts accepted; no legacy reclassification')
    commit=load(folder/'RECEIPT_COMMITTED.json')
    need(life['stop'] is None and life['returncode']==0 and life['GO_sent'] and life['post_audit_success'],'failed process/supervision/output audit')
    begin,exit_ns=life['launch_begin_ns'],life['exit_observed_ns']
    need(begin<=life['spawn_returned_ns']<=exit_ns<=life['post_audit_begin_ns']<=life['post_audit_end_ns']<=life['lifecycle_write_begin_ns']<=commit['lifecycle_write_completed_ns'],'ordered explicit phase boundaries')
    need(sha(folder/'LIFECYCLE.json')==commit['lifecycle_sha256'],'committed lifecycle identity')
    begin,exit_ns=life['launch_begin_ns'],life['exit_observed_ns']
    lease=load(folder/'STORAGE_LEASE.json')
    need(sha(folder/'STORAGE_LEASE.json')==life['storage_lease_sha256'],'storage lease identity')
    need(all(x['error'] is None and not x['thread_alive_after_cleanup'] and x['max_loop_interval_ns']<=1_000_000_000 for x in lease['watches']),'sealed storage watch audit')
    need(lease['preflight_ready_ns']>=lease['preflight_begin_ns'],'storage snapshot boundaries')
    for w in lease['watches']:
        pulses=rows(folder/w['journal']);need(pulses,'storage watcher pulse journal missing')
        previous=None
        for p in pulses:
            need(0<=p['end_ns']-p['begin_ns']<=1_000_000_000 and 0<=p['end_ns']-p['previous_begin_ns']<=1_000_000_000,'independent watcher interval')
            if previous is not None:need(p['previous_begin_ns']==previous,'complete watcher pulse chain')
            previous=p['begin_ns']
        # Journal is real monotonic even in virtual CPU tests.
        if life['clock']=='SYSTEM_MONOTONIC_NS':
            need(pulses[0]['begin_ns']<=begin and exit_ns-pulses[-1]['begin_ns']<=1_000_000_000,'storage watcher covers target lifetime')
    exit_record=load(folder/'EXIT_OBSERVED.json');need(exit_record['exit_observed_ns']==exit_ns,'actual exit confirmation record')
    need(life['creation_FILETIME']==life['process_times']['creation_FILETIME'] and life['process_times']['exit_FILETIME']>0,'OS lifecycle evidence')
    coverage=Coverage(begin);job=load(folder/'JOB.json');limits=job['limits']
    for row in rows(folder/'MONITOR.jsonl'):
        coverage.event(row,exit_ns)
        if row['event']=='READ_END' and row['end_ns']<=exit_ns:
            v=row['values']
            if row['stream']=='resource':
                need(v['RSS']<=limits['worker_RSS_bytes'] and v['host_available']>=limits['host_available_bytes'] and v['disk_free']>=limits['disk_free_bytes'],'independent resource ceiling')
                need(all(x['RSS']<=limits['worker_RSS_bytes'] for x in v.get('control_RSS',[])),'independent control RSS ceiling')
            else:
                need(v['output_bytes']+v['archive_reserve_bytes']<=limits['output_bytes'],'independent output/export ceiling')
                b=lease['baseline']
                need(v['historical_files_scanned']==0 and v['active_observed_bytes']<=b['active_bytes_cap'] and v['active_observed_files']<=b['active_files_cap'],'bounded active storage audit')
                need(v['output_bytes']==b['actual_bytes']+b['active_bytes_cap'],'conservative actual reservation')
                need(v['archive_reserve_bytes']==b['run_bytes']+b['active_bytes_cap']+(b['run_files']+b['active_files_cap'])*1024+1024**2,'conservative export reservation')
    result=coverage.terminal(exit_ns);need(result==life['coverage'],'independent interval reconstruction')
    need(len(life['control_processes'])==2 and all(p['returncode']==0 for p in life['control_processes']),'CPU control process cleanup')
    need((folder/'POST_AUDIT.json').exists() and (folder/'GATE_MODULES.json').exists() and (folder/'CLOSING_MODULES.json').exists(),'mandatory independent identity/output audit artifacts')
    need(life['post_exit_audit_seconds']==(life['post_audit_end_ns']-life['post_audit_begin_ns'])/1e9,'separate audit clock')
    if job['purpose']=='FROZEN_NATIVE_PANEL':
        f0=load(job['F0_path']);raw=rows(folder/'raw.jsonl');audit_raw(raw,job['request'],life['pid'],load(OLD/'EXPECTED_GRAPHS.json'))
        required={pathlib.Path(x['path']).name.lower():x['sha256'] for x in f0['dependencies']+[f0['executable']]};drivers={}
        for x in f0['driver_files']:drivers.setdefault(pathlib.Path(x['path']).name.lower(),set()).add(x['sha256'])
        for event,filename in (('AWAIT_RUNTIME_GATE','GATE_MODULES.json'),('CLOSE','CLOSING_MODULES.json')):
            native=next(e for e in raw if e['event']==event);observed=load(folder/filename)
            need([x['path'] for x in observed]==native['modules'],'independent actual module paths');seen=set()
            for x in observed:
                name=pathlib.Path(x['path']).name.lower()
                if name in required:need(x['sha256']==required[name],'independent module hash');seen.add(name)
                elif name.startswith(('ggml','llama')):raise ValueError('unadmitted numerical module')
                if name in drivers:need(x['sha256'] in drivers[name],'independent driver hash')
            need(seen==set(required),'complete numerical and executable identity')
    return dict(coverage=result,observed_native_lifetime_seconds=(exit_ns-begin)/1e9,
        post_exit_audit_seconds=life['post_exit_audit_seconds'],engineering_seconds_before_commit=commit['slot_engineering_seconds_before_commit'])
