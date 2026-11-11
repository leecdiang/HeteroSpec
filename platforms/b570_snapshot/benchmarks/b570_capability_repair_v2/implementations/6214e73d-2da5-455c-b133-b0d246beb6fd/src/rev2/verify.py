"""Independent read-only raw reconstruction; no supervisor/Win32 imports."""
import argparse,hashlib,json,shlex,sys,os
from pathlib import Path
from guards import FrozenBaseline, ProgressGuard, wall_budget, revision_budget, reconcile_development_attempts
READS=set()
def need(v,m):
    if not v:raise ValueError(m)
def data(p):
    p=Path(p).resolve();READS.add(p);return p.read_bytes()
def load(p):return json.loads(data(p).decode('utf-8'))
def sha(p):return hashlib.sha256(data(p)).hexdigest()
def rows(p):
    b=data(p);need(not b or b.endswith(b'\n'),'partial journal '+str(p));rs=[json.loads(s) for s in b.splitlines()]
    need(all(r['seq']==i+1 for i,r in enumerate(rs)),'journal sequence');need(all(x['at_ns']<=y['at_ns'] for x,y in zip(rs,rs[1:])),'journal clock');return rs
def one(rs,event):
    found=[r for r in rs if r['event']==event];need(len(found)==1,'expected one '+event);return found[0]
def verify_case(folder):
    rs=rows(folder/'EVENTS.jsonl');b=one(rs,'CASE_BEGIN');end=one(rs,'CASE_CLOSED');cid=b['case'];nonce=b['nonce'];need(not any(r['event'] in ['REAL_FAILURE','CASE_ERROR','FORBIDDEN_MODULE'] for r in rs),'case raw error')
    creates=[r for r in rs if r['event']=='PROCESS_CREATE'];exits=[r for r in rs if r['event']=='PROCESS_EXIT'];need(len(creates)==len(exits)==(3 if cid=='C3' else 1),'actor count')
    bypid={r['pid']:r for r in creates};ex={r['pid']:r for r in exits};need(len(bypid)==len(creates) and set(ex)==set(bypid),'exit set');need(sorted(r['role'] for r in creates)==(['child','grandchild','root'] if cid=='C3' else ['root']),'roles');lives=[]
    for c in creates:
        e=ex[c['pid']];need(c['created_filetime']==e['created_filetime'],'identity');life=(int(e['exit_filetime'])-int(c['created_filetime']))/1e7;need(life>=0 and abs(life-e['lifetime_seconds'])<1e-6,'OS lifetime');lives.append(life)
        hs=[r for r in rs if r['event']=='HANDLE_CLOSED' and r.get('handle_kind')=='retained_actor' and r.get('pid')==c['pid']];need(len(hs)==1 and hs[0]['at_ns']>=e['at_ns'],'retained handle');need(c['at_ns']<=e['exit_observed_ns']<=e['at_ns'],'exit order');obs=[r for r in rs if r['event']=='EXIT_OBSERVED' and r.get('pid')==c['pid']];need(len(obs)==1 and obs[0]['at_ns']==e['exit_observed_ns'] and obs[0]['exit_code']==e['exit_code'],'earliest exit observation binding')
    root=next(r for r in creates if r['role']=='root');api=one(rs,'ROOT_CREATED_BY_API');need(api['pid']==root['pid'],'API/debug root identity');base_argv=api['argv']
    for c in creates:
        expected=list(base_argv);expected[expected.index('--role')+1]=c['role'];need([s.replace('/','\\') for s in command_args(c['command'])]==[s.replace('/','\\') for s in expected],'actual actor command');need(hashlib.sha256(c['command'].encode()).hexdigest()==c['command_sha256'],'command hash')
    re=ex[root['pid']];ready=one(rs,'READY_OBSERVED');need(ready['nonce']==nonce and ready['pid']==root['pid'],'READY');need(ready['at_ns']-b['at_ns']<=(3 if cid=='C2' else 5)*1e9,'READY deadline')
    empty=one(rs,'JOB_EMPTY');need(empty['active_pids']==[] and one(rs,'FINAL_JOB_COUNT')['active_pids']==[],'Job empty');one(rs,'STDIO_CLOSED')
    for kind in ['popen_root','case_job']:need(len([r for r in rs if r['event']=='HANDLE_CLOSED' and r.get('handle_kind')==kind])==1,'handle '+kind)
    if cid=='C1':
        c=load(folder/'COMPLETE.json');need(c['nonce']==nonce and c['pid']==root['pid'] and c['event']=='COMPLETE','completion');need(re['exit_code']==0 and re['at_ns']-b['at_ns']<=5e9,'normal exit/deadline')
    elif cid=='C2':
        t=one(rs,'TIMEOUT_CONTROL');kill=one(rs,'JOB_TERMINATE');need(t['actor_alive'] is True and t['ready_ns']==ready['at_ns'] and 2e9<=t['at_ns']-ready['at_ns']<=3e9,'timeout control');need(kill['reason']=='EXPECTED_TIMEOUT' and kill['at_ns']>=t['at_ns'],'timeout kill');need(re['exit_code']!=0 and re['at_ns']>=kill['at_ns'] and end['at_ns']-t['at_ns']<=5e9,'timeout exit/cleanup');need(not (folder/'LATE_WORK.json').exists(),'late work')
    else:
        tree=one(rs,'TREE_READY_COMPLETE');go=one(rs,'CRASH_GO_CONTROL');sent=one(rs,'CRASH_GO_SENT');need(tree['at_ns']-b['at_ns']<=5e9 and go['at_ns']>=tree['at_ns'],'complete tree READY');need(go['all_alive'] is True and go['nonce']==nonce and sent['at_ns']>=go['at_ns'],'tree control');need(re['exit_code']==7 and re['exit_observed_ns']>=sent['at_ns'],'root exit 7');kill=one(rs,'JOB_TERMINATE');need(kill['reason']=='EXPECTED_ABNORMAL_TREE' and kill['at_ns']>=re['at_ns'],'root then kill')
        child=bypid[go['child_pid']];grand=bypid[go['grandchild_pid']];need(child['parent_pid']==root['pid'] and grand['parent_pid']==child['pid'],'parent links')
        for name,c in [('child',child),('grandchild',grand)]:
            r=load(folder/(name+'.ready.json'));need(r['nonce']==nonce and r['pid']==c['pid'] and c['at_ns']<=tree['at_ns'],'descendant READY');e=ex[c['pid']];delta=(int(e['exit_filetime'])-int(re['exit_filetime']))/1e7;need(e['exit_code']!=0 and 0<=delta<=5,'descendant OS exit');need(e['at_ns']-re['exit_observed_ns']<=5e9,'descendant cleanup')
        need(empty['at_ns']-re['exit_observed_ns']<=5e9 and end['at_ns']-re['exit_observed_ns']<=5e9,'complete cleanup deadline')
    need(end['status']=='PASS' and end['cleanup_confirmed'] and end['job_empty'],'conclusion');need(end['at_ns']-b['at_ns']<=10e9,'case deadline');result=load(folder/'RESULT.json');need(all(result[k]==end[k] for k in result),'result reconciliation')
    return dict(label=b['label'],case=cid,actors=len(creates),lifetime_seconds=sum(lives),begin_ns=b['at_ns'],end_ns=end['at_ns'],identities=[(r['pid'],r['created_filetime']) for r in creates],nonce=nonce)
def sample_check(run,sr,wr,sup_pid):
    out={}
    for filename,start,end in [('SAMPLES.jsonl',one(sr,'SUPERVISOR_START')['at_ns'],one(sr,'SUPERVISOR_END')['at_ns']),('WATCHDOG_SAMPLES.jsonl',one(wr,'WATCHDOG_START')['at_ns'],one(wr,'WATCHDOG_END')['at_ns'])]:
        stream=rows(run/filename);need(all(r['event'] in ['SAMPLE','RESOURCE_EXIT_RACE'] for r in stream),'unknown sample event');ss=[r for r in stream if r['event']=='SAMPLE'];need(ss,'missing samples');gaps=[ss[0]['end_ns']-start,end-ss[-1]['end_ns']]+[y['end_ns']-x['end_ns'] for x,y in zip(ss,ss[1:])]+[r['end_ns']-r['begin_ns'] for r in ss];need(min(gaps)>=0 and max(gaps)<=5e9,'effective gap')
        for r in ss:
            need(r['disk_free_bytes']>=10*1024**3 and r['total_observed_rss']<=1536*1024**2,'disk/aggregate limit');need(0<=r['heartbeat_age_ns']<=10e9,'heartbeat')
            if filename=='SAMPLES.jsonl':
                members=r['live_identities'];need(len(members)<=8 and r['job_active']<=8,'actor count');need(r['supervisor_rss']<=512*1024**2 and r['watchdog_rss']<=512*1024**2,'supervisor RSS');need(all(x['rss_bytes']<=256*1024**2 for x in members),'actor RSS');need(r['total_observed_rss']==r['supervisor_rss']+r['watchdog_rss']+sum(x['rss_bytes'] for x in members),'RSS reconciliation')
            else:
                members=r['job_members'];need(len([x for x in members if x['pid']!=sup_pid])<=8 and r['job_active']<=9,'outer count');need(r['watchdog_rss']<=512*1024**2,'watchdog RSS')
                for x in members:
                    if x['rss_bytes'] is None:need(x.get('exit_race') is True,'missing RSS')
                    else:need(x['rss_bytes']<=(512 if x['pid']==sup_pid else 256)*1024**2,'individual RSS')
                need(r['total_observed_rss']==r['watchdog_rss']+sum(x['rss_bytes'] or 0 for x in members),'outer RSS reconciliation')
            if r['storage_upper_bytes'] is None:need(filename=='WATCHDOG_SAMPLES.jsonl' and r['end_ns']-start<=10e9,'storage coverage')
            else:need(r['storage_upper_bytes']<=1024**3,'storage limit')
        out[filename]=dict(samples=len(ss),maximum_effective_gap_ns=max(gaps))
    return out
def command_args(s):return [x[1:-1] if x.startswith('"') and x.endswith('"') else x for x in shlex.split(s,posix=False)]
def audit(root,relative,manifest=None,tool_receipt=None,completion_receipt=None,completion_sha256=None):
    READS.clear()
    root=Path(root).resolve();run=(root/relative).resolve();need(root in run.parents,'run confinement');names=None;mp=None
    if manifest:
        mp=(root/manifest).resolve();m=load(mp);names=set();need(m['files'],'empty manifest')
        for x in m['files']:
            p=x['path'];need(p not in names and not Path(p).is_absolute() and '..' not in Path(p).parts and ':' not in p and '\\' not in p,'manifest path');names.add(p);f=root/p;need(root in f.resolve().parents and f.is_file() and f.stat().st_size==x['bytes'] and sha(f)==x['sha256'],'manifest hash '+p)
        actual=set()
        def fail_walk(error):raise error
        for parent,dirs,files in os.walk(root,followlinks=False,onerror=fail_walk):
            dirs[:]=[n for n in dirs if (Path(parent)/n).relative_to(root).as_posix()!='delivery/post_manifest']
            for n in dirs+files:
                p=Path(parent)/n;need(not p.is_symlink() and not p.is_junction(),'manifest inventory alias')
            for n in files:
                p=Path(parent)/n
                if p.resolve()!=mp:actual.add(p.relative_to(root).as_posix())
        need(actual==names,'manifest inventory')
    sr=rows(run/'SUPERVISOR.jsonl');wr=rows(run/'WATCHDOG.jsonl');summary=load(run/'SUMMARY.json');receipt=load(run/'WATCHDOG_RECEIPT.json');need(not any(r['event']=='SUPERVISOR_FAILURE' for r in sr),'supervisor failure');need(not any(r['event'] in ['WATCHDOG_FAILURE','WATCHDOG_EXCEPTION','CLEANUP_ERROR'] for r in wr),'watchdog failure')
    sup=one(wr,'SUPERVISOR_CREATED_SUSPENDED');ex=one(wr,'SUPERVISOR_OS_EXIT');need(sup['at_ns']<=one(wr,'OUTER_JOB_ASSIGNED')['at_ns']<=one(wr,'SUPERVISOR_RESUMED')['at_ns']<ex['at_ns'],'registration/resume');need(sup['created_filetime']==ex['created_filetime'] and ex['exit_code']==0 and int(ex['exit_filetime'])>int(sup['created_filetime']),'supervisor exit');need(one(wr,'OUTER_JOB_EMPTY')['active_pids']==[],'outer Job')
    for kind in ['supervisor_primary_thread','supervisor_process','outer_job']:need(len([r for r in wr if r['event']=='HANDLE_CLOSED' and r.get('handle_kind')==kind])==1,'outer handle '+kind)
    need(one(wr,'WATCHDOG_END')['receipt']==receipt and receipt['error'] is None and receipt['status']=='WATCHDOG_CLOSED','watchdog receipt');results=[]
    for r in sr:
        if r['event']=='CASE_RESULT':
            d=verify_case(run/r['label']);need(d['label']==r['label'] and r['status']=='PASS','case linkage');results.append(d)
    need({p.name for p in run.iterdir() if p.is_dir()}=={r['label'] for r in results},'case directory set');need([r['case'] for r in results[:3]]==['C1','C2','C3'],'Q order');ids=[x for r in results for x in r['identities']];need(len(ids)==len(set(ids)) and len({r['nonce'] for r in results})==len(results),'duplicate identity/nonce');need(all(x['end_ns']<=y['begin_ns'] for x,y in zip(results,results[1:])),'overlap')
    starts=sum(r['actors'] for r in results);life=sum(r['lifetime_seconds'] for r in results);need(starts==summary['actor_starts'] and abs(life-summary['actor_lifetime_seconds'])<1e-5,'current accounting');prior_starts=0;prior_life=0.
    registrations={}
    revision_budget([load(p) for p in (root/'development').glob('REVISION_*.json') if 'run' in load(p)])
    for p in (root/'development').glob('REVISION_*.json'):
        r=load(p)
        if 'run' in r:registrations[r['run']]=r
    reconcile_development_attempts(root,list(registrations.values()))
    need(sum(r.get('case_attempts',0) for r in registrations.values())<=20,'D0 attempt budget')
    actual={p.relative_to(root).as_posix() for p in (root/'development').iterdir() if p.is_dir() and any((p/n).exists() for n in ['WATCHDOG.jsonl','SUMMARY.json','WATCHDOG_INCOMPLETE.json'])};need(actual<=set(registrations),'unregistered D0 attempt')
    for rel in sorted(registrations):
        d=root/rel
        if d.resolve()==run or not d.exists():continue
        wd=rows(d/'WATCHDOG.jsonl');raw=[]
        for p in d.glob('*/EVENTS.jsonl'):raw.extend(rows(p))
        created={};closed={}
        for r in raw:
            if r['event']=='PROCESS_CREATE':
                key=(r['pid'],r['created_filetime']);need(key not in created,'duplicate previous create');created[key]=r
            if r['event']=='PROCESS_EXIT':
                key=(r['pid'],r['created_filetime']);need(key not in closed,'duplicate previous exit');closed[key]=r
        need(set(closed)<=set(created),'previous exit without create')
        for r in wd:
            if r['event']=='RESIDUAL_RETAINED':created.setdefault((r['pid'],r['created_filetime']),r)
            if r['event']=='RESIDUAL_OS_EXIT':closed.setdefault((r['pid'],r['created_filetime']),r)
        outer=load(d/'WATCHDOG_RECEIPT.json') if (d/'WATCHDOG_RECEIPT.json').exists() else None
        resolution=load(d/'CLEANUP_RESOLUTION.json') if (d/'CLEANUP_RESOLUTION.json').exists() else None
        if outer:need(outer['outer_job_empty'] and outer['owned_handles_closed'] and int(outer['supervisor_os_times']['exit_filetime'])>0,'previous outer closure')
        else:need(resolution and resolution['all_known_not_live'],'previous attempt lacks cleanup disposition')
        resolved={}
        if resolution:
            for r in resolution['identities']:
                need(r['state'] in ['NO_SUCH_PID','OLD_IDENTITY_GONE_PID_REUSED','SIGNALED_EXIT'],'previous identity live/unknown');resolved[(r['pid'],r['created_filetime'])]=r
            for r in wd:
                if r['event'] in ['WATCHDOG_START','SUPERVISOR_CREATED_SUSPENDED','RESIDUAL_RETAINED']:need((r['pid'],r['created_filetime']) in resolved or (r['pid'],r['created_filetime']) in closed,'previous known identity unresolved')
        for r in raw:
            if r['event']=='ROOT_CREATED_BY_API':need(any(k[0]==r['pid'] for k in created),'missing historical OS identity')
        for key,c in created.items():
            if key in closed:
                life_value=(int(closed[key]['exit_filetime'])-int(c['created_filetime']))/1e7;need(life_value>=0,'previous lifetime');prior_life+=life_value
            else:
                need(key in resolved,'previous actor cleanup unresolved');upper=(resolution['at_ns']-wd[0]['at_ns'])/1e9;need(upper>=0,'previous lifetime bound');prior_life+=upper
        prior_starts+=len(created)
        if (d/'SUMMARY.json').exists():need(len([r for r in raw if r['event']=='PROCESS_CREATE'])==load(d/'SUMMARY.json')['actor_starts'],'previous summary reconciliation')
    need(starts+prior_starts<=6000 and life+prior_life<=21600,'development-inclusive budget');need(summary['historical_actor_starts']==prior_starts and abs(summary['historical_actor_lifetime_seconds']-prior_life)<1e-5,'historical accounting');samples=sample_check(run,sr,wr,sup['pid']);cycles=0;seconds=None
    if summary['mode']=='measured':
        f=load(root/'CAPABILITY_FREEZE.json');required={'src/rev2/'+n for n in ['win.py','actor.py','supervisor.py','watchdog.py','verify.py','history.py','guards.py']}|{'CONFIG.json'}|{'acquisition/'+n for n in ['PROTOCOL.md','B570_PROMPT.md','REVIEW_BINDING.json','review/REPORT.json','review/STATUS.json']};need(required<=set(f.get('files',{})) and f.get('source_relative')=='src/rev2','incomplete freeze');need(all(sha(root/p)==h for p,h in f['files'].items()),'freeze drift');need(Path(f['python']).resolve()==Path('C:/Users/DIANG/AppData/Local/Programs/Python/Python312/python.exe').resolve() and sha(f['python'])==f['python_sha256'],'Python identity')
        for image in [one(wr,'WATCHDOG_START')['image'],sup['image'],one(sr,'SUPERVISOR_START')['image']]:need(Path(image).resolve()==Path(f['python']).resolve(),'executing Python image')
        for result in results:
            for r in rows(run/result['label']/'EVENTS.jsonl'):
                if r['event']=='PROCESS_CREATE':need(Path(r['image']).resolve()==Path(f['python']).resolve(),'actor Python image')
        sb=one(sr,'SOAK_BEGIN');se=one(sr,'SOAK_END');need(results[2]['end_ns']<=sb['begin_ns'],'Q before S');seconds=(se['at_ns']-sb['begin_ns'])/1e9;need(seconds>=10800 and se['at_ns']>=sb['end_ns'],'full soak');cs=[r for r in sr if r['event']=='CYCLE_COMPLETE'];cycles=len(cs);need(350<=cycles<=360 and len(results)==3+cycles*3,'cycle completeness')
        for i,c in enumerate(cs):
            trio=results[3+3*i:6+3*i];need(c['cycle']==i+1 and [r['case'] for r in trio]==['C1','C2','C3'] and [r['label'] for r in trio]==['S_%03d_%s'%(i,cid) for cid in ['C1','C2','C3']],'cycle order');need(0<=c['begin_ns']-(sb['begin_ns']+i*30e9)<5e9,'cadence');need(sb['end_ns']-c['begin_ns']>=25e9,'remaining admission window');need(c['begin_ns']<=trio[0]['begin_ns']<=trio[-1]['end_ns']<=c['end_ns']<=sb['end_ns'],'actual cycle/soak intervals');need(c['end_ns']-c['begin_ns']<=25e9,'cycle deadline')
    budget=None
    if summary['mode']=='measured':
        start=one(wr,'WATCHDOG_START')
        expected=start['freeze_sha256'];need(one(sr,'SUPERVISOR_START')['freeze_sha256']==expected,'supervisor freeze pin')
        need(sha(root/'CAPABILITY_FREEZE.json')==expected,'freeze replaced')
        FrozenBaseline(root,expected).check()
        budget=wall_budget(load(root/'ACQUISITION.json'),f,list(registrations.values()),start,receipt)
    # Both development and measurement must prove watchdog progress observed by the supervisor.
    start=one(wr,'WATCHDOG_START');pg=ProgressGuard(start['pid'],start['created_filetime'])
    progress=[r for r in wr if r['event']=='WATCHDOG_PROGRESS']
    need(progress and [r['progress_seq'] for r in progress]==list(range(1,len(progress)+1)),'watchdog progress stream')
    for row in progress:pg.check(row,row['progress_ns'])
    indexed={r['progress_seq']:r for r in progress};pg=ProgressGuard(start['pid'],start['created_filetime'])
    for row in rows(run/'SAMPLES.jsonl'):
        if row['event']!='SAMPLE':continue
        observed=indexed[row['watchdog_progress_seq']]
        fields=pg.check(observed,row['end_ns']);need(all(row[k]==v for k,v in fields.items()),'watchdog progress sample binding')
    if tool_receipt:
        def ref(p):
            need(isinstance(p,str) and not Path(p).is_absolute() and '..' not in Path(p).parts and ':' not in p and chr(92) not in p,'tool evidence path');q=(root/p).resolve();need(root in q.parents,'tool evidence escape');return q
        binding=load(ref(tool_receipt));intent=load(ref(binding['intent_path']));final=load(ref(binding['final_result_path']));initial=load(ref(binding['initial_result_path']));poll=load(ref(binding['final_poll_path']))
        need(sha(ref(binding['intent_path']))==binding['intent_sha256'] and sha(ref(binding['final_result_path']))==binding['final_result_sha256'],'tool evidence hash')
        need(initial['request']==intent['tool_request'] and initial['request']['cmd']==intent['command'],'formal invocation command');need(initial['request']['shell']==intent['shell'] and Path(initial['request']['workdir']).resolve()==root,'formal invocation shell/cwd')
        need(final['exit_code']==0 and initial['response']['session_id']==binding['session_id']==poll['request']['session_id'] and poll['response']==final,'final result/session linkage')
        actual=command_args(one(wr,'WATCHDOG_START')['command']);need([s.replace('/','\\') for s in actual]==[s.replace('/','\\') for s in intent['argv']],'watchdog OS command binding');need(intent['run']==relative and Path(intent['root']).resolve()==root,'tool root/run')
        if summary['mode']=='measured':
            need(intent['freeze_sha256']==expected,'prospective freeze digest binding')
            args=intent['argv'];need(args.count('--freeze-sha256')==1 and args[args.index('--freeze-sha256')+1]==expected,'launch freeze pin')
        lines=[s for s in final['output'].splitlines() if s.strip().startswith('{')];need(json.loads(lines[-1])==dict(watchdog_closed=True,error=None,run=relative),'formal final closure output')
    if completion_receipt is not None:
        need(summary['mode']=='measured' and manifest and tool_receipt,'completion requires full audit')
        cp=Path(completion_receipt).resolve();need(not root in cp.parents,'completion must be external immutable tail')
        raw=cp.read_bytes();need(hashlib.sha256(raw).hexdigest()==completion_sha256,'completion hash')
        complete=json.loads(raw);need(complete['manifest_sha256']==sha(mp) and complete['tool_binding_sha256']==sha(root/tool_receipt) and complete['freeze_sha256']==expected,'completion evidence binding')
        budget=wall_budget(load(root/'ACQUISITION.json'),f,list(registrations.values()),one(wr,'WATCHDOG_START'),receipt,complete)
    if names is not None:need({p.relative_to(root).as_posix() for p in READS if root in p.parents and p!=mp}<=names,'consumed manifest coverage')
    return dict(status='CAPABILITY_ENDURANCE_PASS' if summary['mode']=='measured' and manifest and tool_receipt and completion_receipt else 'CAPABILITY_ENDURANCE_PENDING_DELIVERY' if summary['mode']=='measured' and manifest and tool_receipt else 'DEVELOPMENT_EVIDENCE_PASS' if summary['mode']=='development' else 'CAPABILITY_3CHECK_PASS',budget=budget,cases=len(results),cycles=cycles,soak_seconds=seconds,actor_starts=starts,actor_lifetime_seconds=life,historical_start_charge=prior_starts,historical_lifetime_charge_seconds=prior_life,supervisor_os_lifetime_seconds=(int(ex['exit_filetime'])-int(sup['created_filetime']))/1e7,sampling=samples,manifest_checked=bool(manifest),tool_exit_checked=bool(tool_receipt),outer_gaps=['watchdog own OS exit','command shell','tool host','some preflight/development/review/delivery processes'],historical_upper_charges_are_not_actual_exit_measurements=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--run',required=True);p.add_argument('--manifest');p.add_argument('--tool-receipt');p.add_argument('--completion-receipt');p.add_argument('--completion-sha256');a=p.parse_args()
    try:print(json.dumps(audit(a.root,a.run,a.manifest,a.tool_receipt,a.completion_receipt,a.completion_sha256),sort_keys=True))
    except Exception as e:print(json.dumps(dict(status='VERIFICATION_FAILED',error=repr(e))));sys.exit(1)
