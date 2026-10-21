"""Light coordinator + independent resource and audit CPU processes.

No full log parse/hash/recursive scan is performed in the live coordinator.
Only the monitor process (two independent reading threads) reads resources.
Only the audit process performs gate hashes and complete numerical audits.
"""
import json
import pathlib
import os
import subprocess
import sys
import time
from legacy import HERE,PYTHON,load,save,sha,need
from timing import Clock,Coverage,MAX_GAP_NS
from os_process import Target
from workers import Tail,rows
from storage import Lease,bounded_usage

def supervise(job,command):
    folder=pathlib.Path(job['folder']);folder.mkdir(parents=True,exist_ok=False)
    slot_started=time.monotonic_ns();slot_clock_started=Clock(job).now();lease=Lease(job);job['storage_baseline']=lease.baseline
    clock=Clock(job);begin=clock.now();coverage=Coverage(begin);states=[];native=None;workers=[];handles=[]
    stop=None;exit_ns=None;native_times=None;gate_ok=False;go=False;post_ok=False;post_begin=None;post_end=None;coverage_result=None
    def record(state,**fields):
        row=dict(state=state,ns=clock.now(),**fields);states.append(row)
        with (folder/'STATE.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(row,allow_nan=False)+'\n')
    def confirm_exit():
        nonlocal exit_ns,native_times
        code=native.poll()
        if code is not None and exit_ns is None:
            # No parsing, file hashing or directory walk may precede this stamp.
            exit_ns=clock.now()
            native_times=Target(native.pid,int(native._handle)).times()
            save(folder/'EXIT_OBSERVED.json',dict(exit_observed_ns=exit_ns,returncode=code,process_times=native_times,
                scope='First coordinator poll confirming exit; monotonic timestamp captured before any post-exit audit'))
            record('EXIT_OBSERVED',exit_observed_ns=exit_ns,returncode=code)
        return code
    try:
        need(job['purpose'] in ('CPU_TEST','FROZEN_NATIVE_PANEL'),'job purpose')
        need(job['purpose']=='CPU_TEST' or not any(k in job for k in ('faults','virtual_clock','test_module')),'no test hooks in production')
        storage=bounded_usage(job)
        need(storage['output_bytes']+storage['archive_reserve_bytes']<=job['limits']['output_bytes'],'pre-spawn conservative storage reservation')
        record('SPAWN_BEGIN');job['launch_begin_ns']=begin
        if job.get('request') is not None:(folder/'REQUEST.wire').write_bytes(job['wire_bytes'].encode('utf-8'))
        if job.get('cpu_child') is not None:save(folder/'CHILD.json',job['cpu_child'])
        for name in ('stdout','stderr'):
            handles.append((folder/(name+'.log')).open('xb'))
        native=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=handles[0],stderr=handles[1])
        returned=clock.now();job['pid']=native.pid
        native_times=Target(native.pid,int(native._handle)).times();job['creation_FILETIME']=native_times['creation_FILETIME']
        record('SPAWN_RETURNED',pid=native.pid,spawn_returned_ns=returned,creation_FILETIME=job['creation_FILETIME'])
        save(folder/'JOB.json',job)
        for role in ('monitor','audit'):
            out=(folder/(role+'.stdout.log')).open('xb');err=(folder/(role+'.stderr.log')).open('xb');handles.extend((out,err))
            p=subprocess.Popen([str(PYTHON),str(HERE/'workers.py'),role,str(folder/'JOB.json')],stdout=out,stderr=err)
            workers.append((role,p));record('CONTROL_PROCESS_STARTED',role=role,pid=p.pid)
        save(folder/'CONTROL_PIDS.json',dict(controller=os.getpid(),**{role:p.pid for role,p in workers}))
        monitor=Tail(folder/'MONITOR.jsonl');auditor=Tail(folder/'AUDITOR.jsonl');record('WAITING_FOR_IDENTITY')
        while True:
            # Poll first, immediately stamp exit, then inspect small worker events.
            code=confirm_exit();now=clock.now()
            lease.check()
            for row in monitor.read():
                if row['event']=='MONITOR_ERROR':raise ValueError('monitor process error: '+row['error'])
                coverage.event(row,exit_ns)
                if row['event']=='READ_END' and (exit_ns is None or row['end_ns']<=exit_ns):
                    v=row['values'];limits=job['limits']
                    if row['stream']=='resource':need(v['RSS']<=limits['worker_RSS_bytes'] and v['host_available']>=limits['host_available_bytes'] and v['disk_free']>=limits['disk_free_bytes'],'resource ceiling')
                    else:need(v['output_bytes']+v['archive_reserve_bytes']<=limits['output_bytes'],'storage plus export-reserve ceiling')
                    for helper in v.get('control_RSS',[]):need(helper['RSS']<=limits['worker_RSS_bytes'],'CPU control process RSS ceiling')
            for row in auditor.read():
                if row['event']=='AUDIT_ERROR':raise ValueError('identity/output audit failed: '+row['error'])
                if row['event']=='GATE_AUDIT_OK':gate_ok=True;record('IDENTITY_ADMITTED')
                if row['event']=='POST_AUDIT_BEGIN':post_begin=row['ns'];record('POST_EXIT_AUDITING',audit_begin_ns=post_begin)
                if row['event']=='POST_AUDIT_OK':post_ok=True;post_end=row['ns']
            need(now-job.get('slot_begin_ns',slot_clock_started)<=int(job['per_slot_seconds']*1e9),'slot engineering timeout')
            need(now-job['panel_begin_ns']<=int(job['panel_seconds']*1e9),'whole controller engineering budget')
            if exit_ns is None:
                coverage.live(now)
                for role,p in workers:need(p.poll() is None,role+' worker exited while target running')
                if gate_ok and not go and all(s['completed'] for s in coverage.streams.values()):
                    # Identity was hashed in the separate auditor; monitor still live.
                    need(confirm_exit() is None,'target exited before GO')
                    lease.check();native.stdin.write(b'GO\n');native.stdin.flush();go=True;record('GO_SENT')
            else:
                # These are CPU-control observations after target exit, never
                # appended to target samples or used to invent terminal coverage.
                for role,p in workers:
                    read_begin=clock.now();target=Target(p.pid,int(p._handle))
                    if target.active():
                        try:
                            rss=target.rss();read_end=clock.now()
                            if target.active():
                                with (folder/'POST_CONTROL_RESOURCES.jsonl').open('a') as f:f.write(json.dumps(dict(role=role,pid=p.pid,begin_ns=read_begin,end_ns=read_end,RSS=rss,scope='CPU control only, not target sample'))+'\n')
                                need(rss<=job['limits']['worker_RSS_bytes'],'post-exit CPU control RSS ceiling')
                        except OSError:
                            if target.active():raise
                # End runtime sampling eligibility at exit, not at audit completion.
                if coverage_result is None:
                    # Drain monitor final lines once its target-exit cleanup completes.
                    mp=workers[0][1]
                    if mp.poll() is not None:
                        for row in monitor.read():coverage.event(row,exit_ns)
                        coverage_result=coverage.terminal(exit_ns)
                if post_ok and coverage_result is not None:
                    need(code==0 and go,'child exit/GO gate');break
                for role,p in workers:
                    if role=='audit' and p.poll() is not None and not post_ok:raise ValueError('audit worker exited without success')
            time.sleep(.005)
    except Exception as e:
        stop=str(e);record('STOP',error=stop)
    finally:
        if native is not None:
            if confirm_exit() is None:
                record('TERMINATE_TARGET');native.kill()
            # Confirmation stamp remains before cleanup/log/hash operations.
            deadline=time.monotonic()+3
            while confirm_exit() is None and time.monotonic()<deadline:time.sleep(.005)
            if exit_ns is None:stop=(stop or '')+'; target exit not confirmed'
        cleanup=[]
        for role,p in workers:
            if p.poll() is None:
                try:p.wait(timeout=1)
                except subprocess.TimeoutExpired:p.kill();p.wait(timeout=2)
            cleanup.append(dict(role=role,pid=p.pid,returncode=p.returncode,process_times=Target(p.pid,int(p._handle)).times()))
        if stop is None:
            try:
                need(all(x['returncode']==0 for x in cleanup),'control worker abnormal exit')
                need(clock.now()-job.get('slot_begin_ns',slot_clock_started)<=int(job['per_slot_seconds']*1e9),'slot engineering cleanup timeout')
            except Exception as e:stop=str(e)
        try:
            lease.check()
        except Exception as e:stop=stop or str(e)
        try:lease.close()
        except Exception as e:stop=stop or ('storage watcher cleanup: '+str(e))
        storage_receipt=lease.receipt()
        save(folder/'STORAGE_LEASE.json',storage_receipt)
        for f in handles:f.close()
        if native is not None and native.stdin is not None:
            try:native.stdin.close()
            except OSError:pass
        write_begin=clock.now();record('LIFECYCLE_WRITE_BEGIN',write_begin_ns=write_begin)
        receipt=dict(schema='SUPERVISION_V4',purpose=job['purpose'],clock='CPU_TEST_SHARED_VIRTUAL' if clock.path else 'SYSTEM_MONOTONIC_NS',
            launch_begin_ns=begin,spawn_returned_ns=next((r['spawn_returned_ns'] for r in states if r['state']=='SPAWN_RETURNED'),None),
            exit_observed_ns=exit_ns,post_audit_begin_ns=post_begin,post_audit_end_ns=post_end,lifecycle_write_begin_ns=write_begin,
            pid=native.pid if native else None,creation_FILETIME=job.get('creation_FILETIME'),process_times=native_times,
            returncode=native.returncode if native else None,stop=stop,GO_sent=go,gate_admitted=gate_ok,
            post_audit_success=post_ok,coverage=coverage_result,control_processes=cleanup,
            observed_native_lifetime_seconds=(exit_ns-begin)/1e9 if exit_ns is not None else None,
            post_exit_audit_seconds=(post_end-post_begin)/1e9 if post_begin is not None and post_end is not None else None,
            CPU_control_workers=2,monitor_sampling_threads=2,monitor_main_threads=1,auditor_threads=1,
            FILETIME_not_used_for_monitor_intervals=True,command=command)
        receipt['storage_lease_sha256']=sha(folder/'STORAGE_LEASE.json')
        receipt['whole_slot_engineering_seconds_before_lifecycle']=(time.monotonic_ns()-slot_started)/1e9
        save(folder/'LIFECYCLE.json',receipt)
        written=clock.now()
        save(folder/'RECEIPT_COMMITTED.json',dict(lifecycle_write_completed_ns=written,lifecycle_sha256=sha(folder/'LIFECYCLE.json'),
            slot_engineering_seconds_before_commit=(written-begin)/1e9))
    return receipt
