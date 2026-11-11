"""Independent offline S0 reconstruction. Reads restored bytes; executes no host."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import struct
import zipfile

MAX=1_000_000_000

def require(x,why):
    if not x:raise ValueError(why)

def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def lines(p):return [json.loads(s) for s in Path(p).read_text(encoding='utf-8').splitlines() if s]

def raw_notifications(data):
    out=[];pos=0
    if not data:return out
    while True:
        require(pos+12<=len(data),'notification header')
        nxt,action,size=struct.unpack_from('<III',data,pos)
        require(size%2==0 and pos+12+size<=len(data),'notification extent')
        out.append(dict(action=action,relative_path=data[pos+12:pos+12+size].decode('utf-16-le')))
        if not nxt:break
        require(nxt>=12+size and pos+nxt<len(data),'notification offset');pos+=nxt
    return out

def coverage(path,exit_ns,spawn_ns):
    streams={s:dict(last=None,pending=None,reads=0,max_read_ns=0,max_effective_gap_ns=0,initial_gap_ns=None,errors=[],violations=[],values=[]) for s in ('resource','directory')}
    if not path.exists():return None
    data=lines(path)
    for x in data:
        if x.get('stream') not in streams:continue
        s=streams[x['stream']]
        if x['event']=='READ_BEGIN':
            if s['pending'] is not None:s['violations'].append('overlapping read')
            s['pending']=x['begin_ns']
        if x['event'] in ('READ_END','READ_ERROR','READ_DISCARDED'):
            if s['pending']!=x['begin_ns']:s['violations'].append('unmatched read')
            s['pending']=None
        if x['event']=='READ_ERROR':s['errors'].append(x['error'])
        if x['event']!='READ_END':continue
        b,e=x['begin_ns'],x['end_ns']
        if not spawn_ns<=b<=e<=exit_ns:s['violations'].append('invalid live read')
        if e-b>MAX:s['violations'].append('read>1s')
        if s['last'] is not None and e-s['last']>MAX:s['violations'].append('effective gap>1s')
        if s['initial_gap_ns'] is None:
            s['initial_gap_ns']=e-spawn_ns
            if e-spawn_ns>MAX:s['violations'].append('initial gap>1s')
        s['values'].append(x['values'])
        s['max_read_ns']=max(s['max_read_ns'],e-b)
        if s['last'] is not None:s['max_effective_gap_ns']=max(s['max_effective_gap_ns'],e-s['last'])
        s['last']=b;s['reads']+=1
    for s in streams.values():s['terminal_gap_ns']=exit_ns-s['last'] if s['last'] is not None else None
    return streams

def rebuild(root):
    root=Path(root);rows=[];identities=set();controller_ids=set();launcher_ids=set();suites=[]
    for rev in (0,1):
        base=root/'journals'/('S0_revision'+str(rev));suite=load(base/'SUITE.json')
        suites.append(dict(revision=rev,tests=suite['tests'],reported_assertion_failures=suite['failures'],reported_errors=suite['errors']))
        source=base/'SOURCE_BEFORE_REVISION.zip'
        require(source.exists(),'retained source revision missing')
        with zipfile.ZipFile(source) as z:
            for name,value in suite['source_hashes'].items():require(hashlib.sha256(z.read(name)).hexdigest()==value,'source/run identity '+name)
        for saved in suite['receipts']:
            p=base/saved['name'];case=load(p/'CASE.json');result=load(p/'CONTROLLER_RESULT.json')['result']
            initial=load(p/'launcher/INITIAL.json');closed=load(p/'launcher/CLOSED.json')
            require(saved['result']['result']==result,'suite/native receipt mismatch')
            launcher_ids.add(initial['launcher_pid']);controller_ids.add(closed['controller_pid'])
            for f in closed['files']:
                path=p/'launcher'/f['name'];require(path.stat().st_size==f['bytes'] and sha(path)==f['sha256'],'closed raw log identity')
            require(closed['readers_completed']==2 and closed['error'] is None,'outer capture integrity')
            rejected=[];raws=[];watch_errors=[];watch_gaps=[]
            for log in (p/'native').glob('WATCH_*.jsonl'):
                raw_for_watch=[]
                for event in lines(log):
                    if event['event']=='RAW_NOTIFY':
                        parsed=raw_notifications(base64.b64decode(event['raw_base64']));raw_for_watch.extend(parsed);raws.append(event)
                    elif event['event']=='NOTIFY_DECISION' and not event['allowed']:
                        require(any(x['action']==event['action'] and x['relative_path']==event['relative_path'] for x in raw_for_watch),'rejection lacks preceding raw bytes')
                        rejected.append(event)
                    elif event['event']=='WATCH_ERROR':watch_errors.append(event['error'])
            pid=result['PID'];observed=actual=None;observations=None
            if pid is not None:
                t=result['process_times'];key=(pid,t['creation_FILETIME']);require(key not in identities,'reused child identity');identities.add(key)
                require(t['exit_FILETIME']>=t['creation_FILETIME']>0,'actual CPU lifecycle')
                actual=(t['exit_FILETIME']-t['creation_FILETIME'])/10**7
                observed=(result['exit_observed_ns']-result['spawn_begin_ns'])/10**9
                require(observed==result['native_observed_seconds'],'observed lifecycle arithmetic')
                observations=coverage(p/'native/MONITOR.jsonl',result['exit_observed_ns'],result['spawn_begin_ns'])
            if result['status']=='ADMITTED':
                require(pid is not None and not rejected and not watch_errors,'invalid admitted supervision')
                require(result['error'] is None and closed['controller_exit_code']==0,'invalid admitted exit')
                require(result['post_exit_audit_begin_ns']>=result['exit_observed_ns'],'audit enlarges live interval')
                for state in observations.values():
                    require(state['reads']>0 and not state['errors'] and not state['violations'] and state['terminal_gap_ns']<=MAX,'complete observation qualification')
                for v in observations['resource']['values']:
                    require(v['RSS']<=8*1024**3 and v['host_available']>=2*1024**3 and v['disk_free']>=20*1024**3,'observed resource limits')
                    require(all(x['RSS']<=8*1024**3 for x in v['control_RSS']),'observed control RSS')
                out=root/'outputs'/Path(case['active']).name
                require((out/'DATA.bin').stat().st_size==case.get('frames',14)*4096,'CPU output reconstruction')
                output=lines(p/'native/stdout.log');require(any(x['event']=='CPU_RESULT' for x in output),'missing CPU result')
            row=dict(revision=rev,name=saved['name'],reported_test_expectation=saved['expected'],actual_controller_status=result['status'],
                child_started=pid is not None,PID=pid,CPU_process_FILETIME_seconds=actual,CPU_observed_seconds=observed,
                expected_fault_reached=pid is not None if saved['name'] in ('frozen_input','inactive','sealed_results','overflow') else None,
                error=result['error'],rejected_notifications=rejected,raw_notification_buffers=len(raws),watch_errors=watch_errors,
                coverage=observations,post_exit_audit_seconds=result['post_exit_audit_seconds'],case_command_wall_seconds=saved['wall_seconds'],
                launcher_engineering_ns=closed['engineering_ns'])
            rows.append(row)
    complete=[r for r in rows if r['actual_controller_status']=='ADMITTED']
    return dict(classification='ENGINEERING_BLOCKED',integration_revisions_used=2,suites=suites,cases=rows,
        CPU_test_child_starts=len(identities),PowerShell_launcher_PIDs=sorted(launcher_ids),gated_CPU_controller_PIDs=sorted(controller_ids),
        CPU_FILETIME_lifetime_sum_seconds=sum(r['CPU_process_FILETIME_seconds'] or 0 for r in rows),
        CPU_observed_lifetime_sum_seconds=sum(r['CPU_observed_seconds'] or 0 for r in rows),
        case_command_wall_sum_seconds=sum(r['case_command_wall_seconds'] for r in rows),
        launcher_engineering_sum_seconds=sum(r['launcher_engineering_ns']/10**9 for r in rows),
        admitted_positive_cases=[dict(revision=r['revision'],name=r['name']) for r in complete],
        negative_control_preemptions=[dict(revision=r['revision'],name=r['name'],error=r['error']) for r in rows if r['expected_fault_reached'] is False],
        experimental_native_starts=0,GPU_queries=0,model_requests=0,standalone_graph_computes=0,
        S1='NOT_ADMITTED',S2='NOT_ADMITTED',S3='NOT_ADMITTED',
        note='Assertion pass is not substituted for reaching the intended fault. CPU process FILETIME durations are distinct from monotonic observed durations. Parent command engineering is not claimed as exact parent process lifetime.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output',required=True);args=p.parse_args()
    result=rebuild(args.root)
    with Path(args.output).open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('cases','negative_control_preemptions','PowerShell_launcher_PIDs','gated_CPU_controller_PIDs')},ensure_ascii=False))
