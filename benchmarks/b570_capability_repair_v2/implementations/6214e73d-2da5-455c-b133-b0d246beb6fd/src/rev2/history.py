"""Fail-closed D0 intake. Charges are conservative when historical OS exits are absent."""
import json
from pathlib import Path
def read(p):return json.loads(p.read_text())
def require(v,m):
    if not v:raise ValueError(m)
def lines(p):return [json.loads(s) for s in p.read_text().splitlines()]
def development_budget(root,current_run):
    root=Path(root);current_run=Path(current_run).resolve();registered={}
    from guards import revision_budget, reconcile_development_attempts
    revision_budget([read(p) for p in (root/'development').glob('REVISION_*.json') if 'run' in read(p)])
    for registry in (root/'development').glob('REVISION_*.json'):
        r=read(registry)
        if 'run' in r:registered[r['run']]=r
    reconcile_development_attempts(root,list(registered.values()))
    require(sum(r.get('case_attempts',0) for r in registered.values())<=20,'development attempt reservation budget')
    actual={p.relative_to(root).as_posix() for p in (root/'development').iterdir() if p.is_dir() and any((p/n).exists() for n in ['WATCHDOG.jsonl','SUMMARY.json','WATCHDOG_INCOMPLETE.json'])}
    require(actual<=set(registered),'unregistered development attempt')
    total_starts=0;total_life=0.;coverage=[]
    for rel in sorted(registered):
        folder=root/rel
        if folder.resolve()==current_run or not folder.exists():continue
        require((folder/'WATCHDOG.jsonl').exists(),'attempt lacks watchdog evidence');wd=lines(folder/'WATCHDOG.jsonl');raw=[]
        for p in folder.glob('*/EVENTS.jsonl'):raw.extend(lines(p))
        creates={};exits={}
        for r in raw:
            if r['event']=='PROCESS_CREATE':
                key=(r['pid'],r['created_filetime']);require(key not in creates,'duplicate historical identity');creates[key]=r
            if r['event']=='PROCESS_EXIT':
                key=(r['pid'],r['created_filetime']);require(key not in exits,'duplicate historical exit');exits[key]=r
        require(set(exits)<=set(creates),'historical exit without create')
        for r in wd:
            if r['event']=='RESIDUAL_RETAINED':creates.setdefault((r['pid'],r['created_filetime']),r)
            if r['event']=='RESIDUAL_OS_EXIT':exits.setdefault((r['pid'],r['created_filetime']),r)
        summary=read(folder/'SUMMARY.json') if (folder/'SUMMARY.json').exists() else None
        closure=read(folder/'WATCHDOG_RECEIPT.json') if (folder/'WATCHDOG_RECEIPT.json').exists() else None
        resolution=read(folder/'CLEANUP_RESOLUTION.json') if (folder/'CLEANUP_RESOLUTION.json').exists() else None
        if closure:require(closure.get('outer_job_empty') is True and closure.get('owned_handles_closed') is True and int(closure['supervisor_os_times']['exit_filetime'])>0,'historical outer closure incomplete')
        else:require(resolution and resolution.get('all_known_not_live') is True,'missing-summary attempt cleanup unresolved')
        resolved={}
        if resolution:
            for r in resolution['identities']:
                require(r['state'] in ['NO_SUCH_PID','OLD_IDENTITY_GONE_PID_REUSED','SIGNALED_EXIT'],'historical live/unknown process');resolved[(r['pid'],r['created_filetime'])]=r
            for r in wd:
                if r['event'] in ['WATCHDOG_START','SUPERVISOR_CREATED_SUSPENDED','RESIDUAL_RETAINED']:
                    require((r['pid'],r['created_filetime']) in resolved or (r['pid'],r['created_filetime']) in exits,'unresolved known historical identity')
        for api in [r for r in raw if r['event']=='ROOT_CREATED_BY_API']:require(any(key[0]==api['pid'] for key in creates),'root creation without OS identity')
        charge=0.;missing=[]
        for key,c in creates.items():
            if key in exits:
                e=exits[key];life=(int(e['exit_filetime'])-int(c['created_filetime']))/1e7;require(life>=0,'negative historical OS lifetime');charge+=life
            else:
                require(key in resolved and resolution is not None,'historical identity not closed');upper=(resolution['at_ns']-wd[0]['at_ns'])/1e9;require(upper>=0,'historical lifetime bound');charge+=upper;missing.append(dict(pid=key[0],created_filetime=key[1],actual_exit_filetime=None,lifetime_upper_seconds=upper))
        if summary:
            actual_creates=[r for r in raw if r['event']=='PROCESS_CREATE'];require(len(actual_creates)==summary['actor_starts'],'historical summary starts mismatch')
        total_starts+=len(creates);total_life+=charge;coverage.append(dict(run=rel,start_charge=len(creates),lifetime_charge_seconds=charge,missing_actual_exit_times=missing))
    return dict(current_case_reservation=registered.get(current_run.relative_to(root).as_posix(),{}).get('case_attempts',0),starts=total_starts,lifetime_seconds=total_life,coverage=coverage,reserved_development_cases=sum(r.get('case_attempts',0) for r in registered.values()))
