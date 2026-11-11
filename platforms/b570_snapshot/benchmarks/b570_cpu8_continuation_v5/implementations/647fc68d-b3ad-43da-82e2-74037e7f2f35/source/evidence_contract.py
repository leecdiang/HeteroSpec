"""Exact sealed evidence tree and raw watchdog closure; portable, read-only."""
import hashlib,json,os
from pathlib import Path

def need(v,m):
    if not v:raise ValueError(m)
def relative(name):
    p=Path(name)
    need(isinstance(name,str) and name and not p.is_absolute() and '..' not in p.parts and ':' not in name and '\\' not in name and p.as_posix()==name,'evidence path')
    return p
def member(root,name,directory=False):
    root=Path(root).resolve();p=root/relative(name)
    need(root in p.resolve().parents,'evidence reference escape')
    for part in [p,*p.parents]:
        if part==root:break
        need(not part.is_symlink() and not getattr(part,'is_junction',lambda:False)(),'evidence reference alias')
    need(p.is_dir() if directory else p.is_file(),'missing evidence member')
    if not directory:need(p.stat().st_nlink==1,'evidence hardlink')
    return p
def inventory(root):
    root=Path(root).resolve();found=set()
    def fail(error):raise error
    for parent,dirs,files in os.walk(root,followlinks=False,onerror=fail):
        for name in dirs+files:
            p=Path(parent)/name
            need(not p.is_symlink() and not getattr(p,'is_junction',lambda:False)(),'evidence alias')
            need(root in p.resolve().parents,'evidence escape')
        for name in files:
            p=Path(parent)/name;need(p.is_file() and p.stat().st_nlink==1,'nonregular or hardlinked evidence');found.add(p.relative_to(root).as_posix())
    return found
def manifest_check(root,name):
    root=Path(root).resolve();rel=relative(name).as_posix();m=json.loads(member(root,rel).read_bytes());listed={}
    for row in m['files']:
        item=relative(row['path']).as_posix();need(item not in listed and item!=rel,'duplicate/self manifest member');listed[item]=row
    need(listed and set(listed)==inventory(root)-{rel},'manifest must cover exact sealed tree')
    for item,row in listed.items():
        data=(root/item).read_bytes();need(len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],'manifest member')
    return dict(members=len(listed),scope='entire sealed root except manifest itself; completion receipt stays outside')
def watchdog_check(events,receipt,supervisor_events):
    def one(event):
        found=[x for x in events if x['event']==event];need(len(found)==1,'unique '+event);return found[0]
    need(events and all(x['seq']==i+1 for i,x in enumerate(events)),'watchdog sequence')
    need(all(type(x['at_ns']) is int for x in events) and all(x['at_ns']<=y['at_ns'] for x,y in zip(events,events[1:])),'watchdog event clock')
    start=one('WATCHDOG_START');end=one('WATCHDOG_END');created=one('SUPERVISOR_CREATED_SUSPENDED');exited=one('SUPERVISOR_OS_EXIT')
    need(events[-1]==end and end['receipt']==receipt,'watchdog receipt/raw mismatch')
    need(receipt['status']=='WATCHDOG_CLOSED' and receipt['error'] is None,'watchdog successful closure')
    begin=receipt['begin_ns'];finish=receipt['end_ns'];need(type(begin) is int and type(finish) is int,'watchdog interval types')
    need(begin==start['begin_ns']<=start['at_ns']<=created['at_ns']<=exited['at_ns']<=finish<=end['at_ns'],'watchdog lifecycle bounds')
    need(receipt['watchdog_pid']==start['pid'] and receipt['supervisor_pid']==created['pid']==exited['pid'],'watchdog lifecycle identity')
    times=receipt['supervisor_os_times']
    need(times['created_filetime']==created['created_filetime']==exited['created_filetime'] and int(times['exit_filetime'])>int(times['created_filetime']),'supervisor OS interval')
    need(all(times[k]==exited[k] for k in times),'supervisor OS times mismatch')
    need(receipt['supervisor_exit_code']==exited['exit_code']==0,'supervisor OS exit code')
    empty=one('OUTER_JOB_EMPTY');assigned=one('OUTER_JOB_ASSIGNED');resumed=one('SUPERVISOR_RESUMED')
    need(empty['active_pids']==[] and receipt['outer_job_empty'] is True and receipt['owned_handles_closed'] is True,'raw outer Job closure')
    closed={}
    for kind in ('supervisor_primary_thread','supervisor_process','outer_job'):
        found=[x for x in events if x['event']=='HANDLE_CLOSED' and x['handle_kind']==kind]
        need(len(found)==1,'unique raw handle closure '+kind);closed[kind]=found[0]
    need(assigned['pid']==resumed['pid']==created['pid'],'raw assignment identity')
    order=[created,assigned,resumed,closed['supervisor_primary_thread'],exited,empty,closed['supervisor_process'],closed['outer_job'],end]
    need(all(x['seq']<y['seq'] for x,y in zip(order,order[1:])),'raw closure lifecycle order')
    need(supervisor_events and all(begin<=x['at_ns']<=finish for x in supervisor_events),'supervisor outside watchdog interval')
    need(all(x['at_ns']<=finish for x in events[:-1]),'watchdog end before raw activity')
    return dict(status='WATCHDOG_RAW_RECONCILED',begin_ns=begin,end_ns=finish)
