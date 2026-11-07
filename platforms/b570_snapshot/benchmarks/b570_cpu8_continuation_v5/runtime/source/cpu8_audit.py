"""CPU8 evidence interface. Keep old raw audit output and total-accounting gap intact."""
import sys,os,json,hashlib,shutil,datetime
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/rev2'))
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
def ledger(root):
    legacy=root/'legacy';rows=[];refs=[]
    folder=legacy/'task/raw_os';folder.mkdir(parents=True,exist_ok=True)
    for f in sorted((root/'processes').glob('*/OS_EVENTS.jsonl')):
        raw=f.read_bytes();dest=folder/(f.parent.name+'.jsonl')
        if dest.exists():assert dest.read_bytes()==raw
        else:dest.write_bytes(raw)
        digest=h(dest)
        for r in [json.loads(s) for s in raw.splitlines()]:
            if r['event'] not in ['PROCESS_CREATE','PROCESS_CLOSED']:continue
            record=dict(kind='PROCESS_CREATE' if r['event']=='PROCESS_CREATE' else 'PROCESS_CLOSED',pid=r['pid'],created_filetime=int(r['created_filetime']),at_ns=r['at_ns'],source_event=dict(path=dest.relative_to(legacy).as_posix(),sha256=digest,seq=r['seq']),scope='Real independently observed task-command descendant')
            if r['event']=='PROCESS_CREATE':record.update(parent_pid=r['parent_pid'],role=r['role'],command_sha256=r['command_sha256'],command=r['command'],image=r['image'])
            else:record.update(exit_filetime=int(r['exit_filetime']),exit_code=r['exit_code'],lifetime_seconds=r['lifetime_seconds'])
            rows.append(record)
    rows.sort(key=lambda x:x['at_ns']);out=legacy/'task/PROCESS_LEDGER.snapshot.jsonl'
    if out.exists():out.rename(out.with_name('PROCESS_LEDGER.previous-'+str(len(list(out.parent.glob('PROCESS_LEDGER.previous-*'))))+'.jsonl'))
    out.write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in rows))
    write(legacy/('task/TOTAL_LEDGER_GAP-'+str(len(list((legacy/'task').glob('TOTAL_LEDGER_GAP-*'))))+'.json'),dict(status='UNKNOWN',whole_task_ledger_valid=None,unobserved=['command observer own OS exit','watchdog own OS exit','command shell and tool host','preflight and early portable regression roots'],known_observed_prefix_not_complete_task_ledger=True))
    return rows
def manifest(legacy,runid):
    name='AUDIT_INPUT_MANIFEST-'+runid+'.json';p=legacy/name
    members=[]
    for f in sorted(legacy.rglob('*')):
        if f.is_file() and not f.name.startswith('AUDIT_INPUT_MANIFEST'):
            assert not f.is_symlink() and not f.is_junction();members.append(dict(path=f.relative_to(legacy).as_posix(),bytes=f.stat().st_size,sha256=h(f)))
    write(p,dict(members=members));return name
def exception_check(rs):
    """Reconstruct the native one-loader-breakpoint policy, never swallow app faults."""
    from exception_policy import ExceptionPolicy
    policy=ExceptionPolicy();active={};count=0
    for row in rs:
        if row['event']=='PROCESS_CREATE':
            ident=(row['pid'],row['created_filetime'])
            assert row['pid'] not in active,'active exception identity collision'
            active[row['pid']]=ident;policy.created(ident)
        elif row['event']=='EXCEPTION':
            ident=active.get(row['pid']);assert ident is not None,'exception identity missing'
            assert row['continuation']==policy.decide(ident,row['code'],row['first_chance']),'exception continuation mismatch'
            count+=1
        elif row['event']=='PROCESS_CLOSED':
            assert active.get(row['pid'])==(row['pid'],row['created_filetime']),'exception close identity'
            del active[row['pid']]
    assert not active,'exception identity remains live'
    return count
def case_os(root,runid,cid):
    root=Path(root);found=[];recorded_root=Path(json.loads((root/'legacy/ROOT_BINDING.json').read_bytes())['task_root'])
    for p in (root/'processes').glob('*/OS_EVENTS.jsonl'):
        raw=p.read_bytes()
        assert raw.endswith(b'\n'),'partial OS evidence'
        rs=[json.loads(x) for x in raw.splitlines()]
        start=[r for r in rs if r['event']=='OBSERVER_START']
        if len(start)!=1:continue
        argv=start[0]['argv']
        if '--run' not in argv or argv[argv.index('--run')+1]!=runid or str(recorded_root/'source/bridge.py').replace(chr(92),'/') not in [x.replace(chr(92),'/') for x in argv]:continue
        found.append((p,rs))
    assert len(found)==1,'unique actual case command observer'
    p,rs=found[0]
    from audit_identity_stream import check as identity_check
    identity_check(p.parent)
    exception_check(rs)
    assert all(r['seq']==i+1 for i,r in enumerate(rs)),'OS sequence'
    assert not any(r['event'] in ['OBSERVER_FAILURE','FORBIDDEN_MODULE','CLEANUP_ERROR'] for r in rs),'actual OS case failure'
    creates={(r['pid'],r['created_filetime']):r for r in rs if r['event']=='PROCESS_CREATE'}
    closes={(r['pid'],r['created_filetime']):r for r in rs if r['event']=='PROCESS_CLOSED'}
    assert creates and len(creates)==sum(r['event']=='PROCESS_CREATE' for r in rs) and set(creates)==set(closes),'case OS identity closure'
    for key,c in creates.items():
        e=closes[key];assert int(e['exit_filetime'])>=int(c['created_filetime']) and abs((int(e['exit_filetime'])-int(c['created_filetime']))/1e7-e['lifetime_seconds'])<1e-6,'case OS lifetime'
        assert len([r for r in rs if r['event']=='HANDLE_CLOSED' and r.get('pid')==key[0] and r.get('created_filetime')==key[1] and r.get('handle_kind')=='retained_process' and r['at_ns']>=e['at_ns']])==1,'case retained handle'
    assert len([r for r in rs if r['event']=='JOB_EMPTY' and r['active_pids']==[]])==1,'case Job empty'
    end=[r for r in rs if r['event']=='OBSERVER_END'];assert len(end)==1 and end[0]['receipt']['root_exit_code']==0 and end[0]['receipt']['all_observed_closed'],'case observer receipt'
    cfg=json.loads((root/'legacy/runs'/runid/'CONFIG.json').read_bytes())
    round_rows=[json.loads(x) for x in (root/'legacy/runs'/runid/'external/ROUND.jsonl').read_bytes().splitlines()]
    for s in [r for r in round_rows if r['event']=='CHILD_SPAWNED']:
        key=(s['pid_child'],str(s['os_times']['creation_FILETIME']));assert key in creates and key in closes,'inner child actual identity'
        close=[r for r in round_rows if r['event']=='CHILD_CLOSED' and r['slot']==s['slot'] and r['pid_child']==s['pid_child']]
        assert len(close)==1 and close[0]['os_times']['exit_FILETIME']==int(closes[key]['exit_filetime']) and close[0]['exit_code']==closes[key]['exit_code'],'inner/outer OS exit match'
    return dict(journal=p.relative_to(root).as_posix(),sha256=h(p),identities=len(creates),all_actual_closed=True,scope='Case command tree only; unrelated incomplete review/outer roots are not removed or synthesized')
def qualify(root,raw,runid,cid,phase):
    row=[r for r in raw['cases'] if r.get('run')==runid and r.get('case_id')==cid]
    assert len(row)==1,'one case required';r=row[0];receipt=r['receipt'];spec=raw_audit_spec(root,cid)
    checks=r['checks'];need_checks=set(checks)-{'process_ledger'}
    if phase=='D0':
        assert cid in ['normal_single','journal_write_failure'],'bounded D0 smoke'
        need_checks-={'freeze_binding'}
    assert all(checks[k] is True for k in need_checks),json.dumps(checks)
    assert receipt['control_point_reached'] and receipt['early_failure'] is False and receipt['cleanup_complete'],'raw controls/cleanup'
    if phase=='FORMAL':assert receipt['fixture_ready'] is True,'review/source gate required'
    detector=receipt['detector'];assert detector['code']==spec['detector'] and type(detector['at_ns']) is int,'correct actual detector'
    if spec['kind']=='negative':
        trigger=receipt['trigger'];expected='-1:'+cid
        assert receipt['trigger_observed'] and receipt['no_work_after_detection'],'actual fault and no later GO'
        assert trigger['code']==spec['trigger'] and trigger['fault_id']==detector['fault_id']==expected,'fault identity'
        assert trigger['target_id'].lower()==detector['target_id'].lower()==receipt['planned_target_id'].lower(),'fault target'
        assert 0<=trigger['begin_ns']<=detector['at_ns']<=receipt['closed_ns'] and trigger['begin_ns']<=trigger['end_ns']<=receipt['closed_ns'],'fault/control timing'
    observed=case_os(root,runid,cid)
    return dict(status='CPU8_CASE_PASS' if phase=='FORMAL' else 'D0_BRIDGE_SMOKE_PASS',run=runid,case_id=cid,phase=phase,original_raw_status=r['status'],original_raw_reason=r.get('reason'),original_task_process_ledger_valid=raw['process_ledger_valid'],task_total_ledger_status='UNKNOWN',case_os=observed,case_checks=checks,scope='Strict original controls/coverage/detectors plus independent case OS tree. Original whole-prefix ledger failure remains unchanged and visible.')
def raw_audit_spec(root,cid):
    p=Path(root)/'legacy/repo/benchmarks/b570_supervision_fix_v2/ACCEPTANCE.json'
    return next(s for s in json.loads(p.read_bytes())['cases'] if s['id']==cid)
def audit(root,runid,cid,phase,outdir):
    root=Path(root).resolve();legacy=root/'legacy';design=legacy/'repo/benchmarks/b570_supervision_fix_v2';outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
    ledger(root);m=manifest(legacy,runid);sys.path.insert(0,str(design/'host'));import raw_audit
    raw=raw_audit.audit(legacy,m);write(outdir/(runid+'.legacy_raw_audit.json'),raw)
    try:result=qualify(root,raw,runid,cid,phase)
    except BaseException as e:
        write(outdir/(runid+'.qualification.json'),dict(status='FAIL',case_id=cid,run=runid,error=repr(e)));raise
    result.update(raw_audit_sha256=h(outdir/(runid+'.legacy_raw_audit.json')),manifest_sha256=h(legacy/m));write(outdir/(runid+'.qualification.json'),result);return result
if __name__=='__main__':
    root,runid,cid,phase=sys.argv[1:5];print(json.dumps(audit(root,runid,cid,phase,Path(root)/'reports'),sort_keys=True))
