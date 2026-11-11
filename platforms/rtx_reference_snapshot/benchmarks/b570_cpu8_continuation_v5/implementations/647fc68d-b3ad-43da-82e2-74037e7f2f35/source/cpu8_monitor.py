"""Independent CPU8 outer monitoring reconstruction; never substitutes for inner 1s."""
import json,sys
from pathlib import Path
def need(v,m):
    if not v:raise ValueError(m)
def records(p):
    p=Path(p);need(p.is_file(),'missing monitor stream '+p.name)
    b=p.read_bytes();need(b and b.endswith(b'\n'),'empty/partial monitor stream '+p.name)
    r=[json.loads(s) for s in b.splitlines()]
    need(all(x['seq']==i+1 and type(x['at_ns']) is int for i,x in enumerate(r)),'monitor sequence')
    need(all(a['at_ns']<=b['at_ns'] for a,b in zip(r,r[1:])),'monitor clock order')
    return r
def one(rs,event):
    x=[r for r in rs if r['event']==event];need(len(x)==1,'unique '+event);return x[0]
def number(x):return type(x) is int and x>=0
def check(folder):
    folder=Path(folder);root=folder
    while not (root/'src/rev2').is_dir() and root!=root.parent:root=root.parent
    if (root/'src/rev2').is_dir():sys.path.insert(0,str(root/'src/rev2'))
    from guards import ProgressGuard
    sr=records(folder/'SUPERVISOR.jsonl');wr=records(folder/'WATCHDOG.jsonl')
    st=one(sr,'SUPERVISOR_START');we=one(wr,'WATCHDOG_START');se=one(sr,'SUPERVISOR_END');ee=one(wr,'WATCHDOG_END')
    sup_exit=one(wr,'SUPERVISOR_EXIT_OBSERVED');created=one(wr,'SUPERVISOR_CREATED_SUSPENDED')
    need(created['pid']==st['pid'] and created['created_filetime']==st['created_filetime'],'monitor supervisor identity')
    pg=ProgressGuard(we['pid'],we['created_filetime']);progress={}
    prs=[r for r in wr if r['event']=='WATCHDOG_PROGRESS']
    need(prs and [r['progress_seq'] for r in prs]==list(range(1,len(prs)+1)),'raw progress sequence')
    for r in prs:
        need((r['pid'],r['created_filetime'])==(we['pid'],we['created_filetime']),'raw progress identity')
        need(type(r['progress_ns']) is int and r['progress_ns']<=r['at_ns'],'raw progress time')
        progress[r['progress_seq']]=r
    hb=records(folder/'HEARTBEATS.jsonl')
    need(all(r['event']=='HEARTBEAT' and r['pid']==st['pid'] and r['writer_pid']==st['pid'] for r in hb),'heartbeat identity')
    need(all(number(r['storage_upper_bytes']) and r['storage_upper_bytes']<=1024**3 for r in hb),'heartbeat storage')
    out={}
    for name,start,end,pid in [('SAMPLES.jsonl',st['at_ns'],sup_exit['at_ns'],st['pid']),('WATCHDOG_SAMPLES.jsonl',we['begin_ns'],ee['at_ns'],we['pid'])]:
        rows=records(folder/name);ss=[r for r in rows if r['event']=='SAMPLE'];need(ss,'missing SAMPLE '+name)
        need(all(r['event'] in ('SAMPLE','RESOURCE_EXIT_RACE') for r in rows),'unknown monitor row')
        need(all(r['writer_pid']==pid for r in rows),'monitor writer identity')
        for r in ss:need(number(r['begin_ns']) and number(r['end_ns']) and r['begin_ns']<=r['end_ns']<=r['at_ns'],'monitor read interval')
        gaps=[ss[0]['end_ns']-start,end-ss[-1]['end_ns']]+[b['end_ns']-a['end_ns'] for a,b in zip(ss,ss[1:])]+[r['end_ns']-r['begin_ns'] for r in ss]
        need(min(gaps)>=0 and max(gaps)<=5_000_000_000,'outer effective monitor gap '+name)
        for r in ss:
            need(number(r['disk_free_bytes']) and r['disk_free_bytes']>=10*1024**3,'monitor disk')
            if name=='SAMPLES.jsonl':
                need(all(number(r[k]) and r[k]<=512*1024**2 for k in ('supervisor_rss','watchdog_rss')),'supervisor resource limit')
                pr=progress.get(r.get('watchdog_progress_seq'));need(pr is not None and pr['progress_ns']==r.get('watchdog_progress_ns'),'raw progress linkage')
                checked=pg.check(pr,r['end_ns']);need(checked['watchdog_progress_age_ns']==r['watchdog_progress_age_ns'],'raw progress age')
            else:
                need(number(r['watchdog_rss']) and r['watchdog_rss']<=512*1024**2,'watchdog resource limit')
                ms=r['job_members'];need(len({x['pid'] for x in ms})==len(ms)==r['job_active'],'Job membership count')
                live=[x for x in ms if x['rss_bytes'] is not None]
                need(len([x for x in live if x['pid']!=st['pid']])<=8,'live process limit')
                for x in ms:
                    if x['rss_bytes'] is None:need(x.get('exit_race') is True,'missing resource value')
                    else:need(number(x['rss_bytes']) and x['rss_bytes']<=(512 if x['pid']==st['pid'] else 256)*1024**2,'member resource limit')
                total=r['watchdog_rss']+sum(x['rss_bytes'] or 0 for x in ms)
                need(total==r['total_observed_rss'] and total<=1536*1024**2,'resource reconciliation')
                need(number(r['heartbeat_age_ns']) and r['heartbeat_age_ns']<=10_000_000_000,'heartbeat age')
                storage=r['storage_upper_bytes']
                need(storage is None and r['end_ns']-we['begin_ns']<=10_000_000_000 or number(storage) and storage<=1024**3,'watchdog storage coverage')
        out[name]=dict(samples=len(ss),maximum_effective_gap_ns=max(gaps))
    return dict(status='OUTER_MONITOR_RECONSTRUCTED',streams=out,heartbeats=len(hb),scope='Outer 5s streams only; inner original 1s qualification remains independently required')
