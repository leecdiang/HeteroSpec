"""Success-path OS identity audit. Does not certify review content or outer processes."""
import argparse,json
from collections import Counter
from pathlib import Path

def check(folder,churn=False,breakpoint=False):
    folder=Path(folder);rows=[json.loads(x) for x in (folder/'OS_EVENTS.jsonl').read_text().splitlines()]
    if (folder/'INCOMPLETE.json').exists():raise ValueError('INCOMPLETE')
    def identity(r):
        pid=r['pid'];created=r['created_filetime']
        if type(pid) is not int or pid<=0 or not isinstance(created,str) or not created.isdigit() or int(created)<=0:raise ValueError('identity')
        return pid,created
    observed={};closed={};handles=set();exits={};raw=[];received=0;root=None;empty=False
    for r in rows:
        event=r['event']
        if event=='ROOT_CREATED_SUSPENDED':root=identity(r)
        elif event=='PROCESS_CREATE_RECEIVED':received+=1
        elif event=='PROCESS_CREATE_OBSERVED':raw.append(identity(r))
        elif event=='PROCESS_CREATE':
            k=identity(r)
            if k in observed or any(x[0]==k[0] and x not in closed for x in observed):raise ValueError('duplicate identity or active PID')
            observed[k]=r
            if (r['role']=='root')!=(k==root):raise ValueError('root identity')
        elif event=='EXIT_OBSERVED':
            k=identity(r)
            if k not in observed or k in exits:raise ValueError('unmatched exit')
            exits[k]=r['exit_code']
        elif event=='PROCESS_CLOSED':
            k=identity(r)
            if k not in exits or k in closed or exits[k]!=r['exit_code']:raise ValueError('close pairing')
            elapsed=(int(r['exit_filetime'])-int(k[1]))/1e7
            if elapsed<=0 or abs(elapsed-r['lifetime_seconds'])>1e-9:raise ValueError('OS lifetime')
            closed[k]=r
        elif event=='HANDLE_CLOSED' and r['handle_kind']=='retained_process':
            k=identity(r)
            if k not in closed or k in handles:raise ValueError('handle pairing')
            handles.add(k)
        elif event=='JOB_EMPTY':
            if r['active_pids']:raise ValueError('Job active')
            empty=True
        elif event in ('OBSERVER_FAILURE','CLEANUP_ERROR','CLEANUP_EVENT_ERROR','REJECTED_PROCESS_OS_EXIT'):raise ValueError(event)
    receipt=json.loads((folder/'RECEIPT.json').read_text())
    if not observed or root not in observed or not empty or set(observed)!=set(closed) or set(closed)!=handles or set(exits)!=set(closed):raise ValueError('incomplete identities')
    if len(raw)!=received or len(raw)!=len(observed) or set(raw)!=set(observed):raise ValueError('raw admission coverage')
    if receipt['status']!='CLOSED' or receipt['error'] is not None or receipt['all_observed_closed'] is not True:raise ValueError('receipt status')
    if exits[root]!=receipt['root_exit_code']:raise ValueError('root exit contradiction')
    if (receipt['root_exit_code']==0)==breakpoint:raise ValueError('expected root outcome')
    if breakpoint:
        output=(folder/'stdout.log').read_text()
        if 'APPLICATION_BREAKPOINT_BEGIN' not in output or 'APPLICATION_BREAKPOINT_SWALLOWED' in output:raise ValueError('breakpoint control')
        if not any(x['event']=='EXCEPTION' and x['pid']==root[0] and x['code']==0x80000003 and x['continuation']==0x80010001 for x in rows):raise ValueError('breakpoint not passed through')
    if receipt['observed']!=len(observed) or receipt['closed']!=len(closed) or abs(receipt['lifetime_seconds']-sum(r['lifetime_seconds'] for r in closed.values()))>1e-6:raise ValueError('receipt totals')
    if churn:
        output=[json.loads(line) for line in (folder/'stdout.log').read_text().splitlines()]
        if len(output)!=201 or output[-1]!=dict(status='CHURN_COMPLETE',children=200):raise ValueError('churn completion')
        counts=Counter()
        for index,row in enumerate(output[:-1]):
            if row['index']!=index or row['parent_pid']!=root[0] or type(row['pid']) is not int:raise ValueError('churn worker')
            counts[row['pid']]+=1
        available=Counter(k[0] for k in observed if k!=root)
        if any(available[pid]<count for pid,count in counts.items()):raise ValueError('churn identity coverage')
    return dict(status='IDENTITY_STREAM_PASS' ,identities=len(observed),reused_pids=len(observed)-len({k[0] for k in observed}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--folder',required=True);p.add_argument('--churn',action='store_true');p.add_argument('--breakpoint',action='store_true');a=p.parse_args();print(json.dumps(check(a.folder,a.churn,a.breakpoint)))
