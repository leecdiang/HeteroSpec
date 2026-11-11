"""Exact source inventory and independent D0 start reconciliation."""
import os,json,hashlib,datetime
from pathlib import Path
from continuation_policy import load as load_policy,review_id
def need(v,m):
    if not v:raise ValueError(m)
def check_sources(root,freeze):
    root=Path(root).resolve();prefixes=['source/','src/rev2/','legacy/repo/benchmarks/b570_supervision_fix_v2/host/']
    wanted={p for p in freeze['files'] if any(p.startswith(x) for x in prefixes)};actual=set()
    for prefix in prefixes:
        for p in (root/prefix).rglob('*'):
            need(not p.is_symlink() and not p.is_junction(),'source alias')
            if p.is_file():
                rel=p.relative_to(root).as_posix();need('__pycache__' not in p.parts and p.suffix not in ['.pyc','.pyo','.pyd','.so','.dll'],'non-source file in import tree');actual.add(rel)
    need(actual==wanted,'SOURCE_ONLY_INVENTORY_DRIFT')
    for rel in actual:need(hashlib.sha256((root/rel).read_bytes()).hexdigest()==freeze['files'][rel],'SOURCE_DRIFT')
def rows(path):
    raw=path.read_bytes();need(not raw or raw.endswith(b'\n'),'partial D0 journal');return [json.loads(x) for x in raw.splitlines()]
def actual_d0(root,registrations):
    root=Path(root).resolve();registered={}
    for r in registrations:
        need(r['run'] not in registered,'duplicate D0 run');p=(root/r['run']).resolve();need(root in p.parents,'D0 run escape');registered[r['run']]=r
    counts={};sources={};first_created={}
    def add(run,n,path):
        counts[run]=max(counts.get(run,0),n);sources.setdefault(run,[]).append(str(path.relative_to(root)))
    binding=root/'legacy/ROOT_BINDING.json';original=Path(json.loads(binding.read_bytes())['task_root']) if binding.exists() else root
    meta=json.loads((root/'preflight/TOOLS.json').read_bytes()) if (root/'preflight/TOOLS.json').exists() else {}
    observed={}
    for path in sorted((root/'processes').glob('*/OS_EVENTS.jsonl')):
        rr=rows(path);starts=[x for x in rr if x.get('event')=='OBSERVER_START'];need(len(starts)==1,'observer attempt identity')
        st=starts[0];argv=st.get('argv',[]);normalized=[str(x).replace(chr(92),'/') for x in argv]
        def has(rel):return (original/rel).as_posix() in normalized
        if has('source/bridge.py'):
            need('--run' in argv and '--phase' in argv,'bridge invocation identity');rid=argv[argv.index('--run')+1];phase=argv[argv.index('--phase')+1]
            if phase=='FORMAL':
                f=root/'CAPABILITY_FREEZE.json';cfg=root/'legacy/runs'/rid/'CONFIG.json'
                need(f.exists() and cfg.exists(),'unregistered formal bridge')
                c=json.loads(cfg.read_bytes());plan=json.loads((root/'CPU8_PLAN.json').read_bytes())
                need(rid in [x['run_id'] for x in plan['cases']] and c['phase']=='FORMAL' and '--freeze-sha256' in argv and argv[argv.index('--freeze-sha256')+1]==hashlib.sha256(f.read_bytes()).hexdigest()==c['freeze_sha256'],'unregistered formal bridge')
                continue
            need(phase=='D0','unknown bridge phase');key='legacy/runs/'+rid
        elif has('src/rev2/watchdog.py') and '--mode' in argv and argv[argv.index('--mode')+1]=='development':
            need('--run' in argv,'native watchdog run');key=argv[argv.index('--run')+1]
        elif has('source/native_freeze_gates.py'):key='development/freeze-r1'
        elif has('source/stall_harness.py'):key='development/stall-r2-a1'
        elif argv and meta.get('csharp',{}).get('path') and Path(argv[0])==Path(meta['csharp']['path']):
            need('/target:library' in argv and any(str(x).endswith('LauncherCapture.cs') for x in argv),'unknown compiler command');continue
        elif argv and meta.get('reviewer',{}).get('path') and Path(argv[0])==Path(meta['reviewer']['path']):
            need(review_id(path.parent.name,load_policy(root)) and st.get('process_kind')=='review' and '--sandbox' in argv and argv[argv.index('--sandbox')+1]=='read-only','unknown review command');continue
        else:key=path.parent.relative_to(root).as_posix()
        observed[key]=observed.get(key,0)+1;need(observed[key]==1,'D0 attempt reused');add(key,1,path)
        created=[int(x['created_filetime']) for x in rr if x.get('event')=='ROOT_CREATED_SUSPENDED']
        if created:first_created[key]=min(created)
    for path in sorted((root/'development').rglob('WATCHDOG.jsonl')):
        st=[x for x in rows(path) if x.get('event')=='WATCHDOG_START'];need(len(st)==1,'native watchdog start')
        key=path.parent.relative_to(root).as_posix();add(key,1,path)
        first_created[key]=int(st[0]['created_filetime'])
    for path in sorted((root/'development').rglob('EVENTS.jsonl')):
        rr=rows(path);n=sum(x.get('event')=='CASE_BEGIN' for x in rr)
        if n:
            rel=path.relative_to(root);key='/'.join(rel.parts[:2]);sources.setdefault(key,[]).append(rel.as_posix());counts[key]=counts.get(key,0)+n
            # Remove the one parent-supervision charge once actual cases exist.
    for key in list(counts):
        if key.startswith('development/'):
            group=root/key;actual=sum(sum(x.get('event')=='CASE_BEGIN' for x in rows(p)) for p in group.rglob('EVENTS.jsonl'))
            counts[key]=max(actual,observed.get(key,0))
    for path in sorted((root/'legacy/runs').glob('*/external/ROUND.jsonl')):
        cfg=path.parents[1]/'CONFIG.json';c=json.loads(cfg.read_bytes());n=sum(x.get('event')=='CASE_BEGIN' for x in rows(path))
        if c.get('phase')=='D0' or c.get('round',0)<0 and c.get('phase')!='FORMAL':add('legacy/runs/'+path.parents[1].name,n,path)
    need(set(counts)<=set(registered),'UNREGISTERED_D0_START:'+','.join(sorted(set(counts)-set(registered))))
    result=[];total=0
    for key,r in registered.items():
        count=counts.get(key,0)
        if count and key in first_created:
            from guards import utc
            actual_utc=datetime.datetime(1601,1,1,tzinfo=datetime.timezone.utc)+datetime.timedelta(microseconds=first_created[key]//10)
            need(utc(r['registered_utc'])<=actual_utc,'NON_PROSPECTIVE_D0_RESERVATION')
        need(type(r['case_attempts']) is int and 0<=count<=r['case_attempts'],'D0_ACTUAL_EXCEEDS_RESERVATION');total+=count
        result.append(dict(run=key,reserved=r['case_attempts'],actual=count,evidence=sources.get(key,[])))
    need(load_policy(root) is not None or total<=20,'D0_ACTUAL_LIMIT');return dict(actual=total,reservations=result,unregistered=[])
def d0_now(root):
    from guards import utc,revision_budget
    root=Path(root);origin=utc(json.loads((root/'ACQUISITION.json').read_bytes())['first_preparation_utc']);elapsed=(datetime.datetime.now(datetime.timezone.utc)-origin).total_seconds()
    policy=load_policy(root);need(0<=elapsed<=(policy['development_seconds'] if policy else 5400),'DEVELOPMENT_TIME_LIMIT');regs=json.loads((root/'D0_RESERVATIONS.json').read_bytes());revision_budget(regs,policy);return actual_d0(root,regs)
