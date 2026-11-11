"""Counterfactual raw copies of actual D0 runs; no fabricated PASS receipts."""
import sys,json,shutil,hashlib
from pathlib import Path
ROOT=Path(sys.argv[1]).resolve();sys.path.insert(0,str(ROOT/'source'));import cpu8_audit
sys.path.insert(0,str(ROOT/'legacy/repo/benchmarks/b570_supervision_fix_v2/host'));import raw_audit
out=ROOT/'synthetic/bridge';out.mkdir(parents=True,exist_ok=False);results=[]
normal='d0-smoke-r2-normal';journal='d0-smoke-r2-journal'
def readrows(p):return [json.loads(x) for x in p.read_bytes().splitlines()]
def save(p,rs):
    for i,r in enumerate(rs):r['seq']=i+1
    p.write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in rs))
def find_os(clone,runid):
    for p in (clone/'processes').glob('*/OS_EVENTS.jsonl'):
        rs=readrows(p);start=next(r for r in rs if r['event']=='OBSERVER_START')
        argv=start['argv']
        if '--run' in argv and argv[argv.index('--run')+1]==runid:return p,rs
    raise AssertionError('actual OS case evidence missing')
for mode in ['missing_control','wrong_detector','early_rejection','missing_os_exit','wrong_os_time','missing_pending_completion','missing_independent_journal_receipt']:
    clone=out/mode;clone.mkdir()
    shutil.copytree(ROOT/'legacy',clone/'legacy');shutil.copytree(ROOT/'processes',clone/'processes')
    runid=journal if mode=='missing_independent_journal_receipt' else normal;cid='journal_write_failure' if runid==journal else 'normal_single'
    run=clone/'legacy/runs'/runid;rp=run/'external/ROUND.jsonl';rr=readrows(rp)
    if mode=='missing_control':save(rp,[r for r in rr if r['event']!='CONTROL_POINT'])
    elif mode=='wrong_detector':
        for r in rr:
            if r['event']=='POSITIVE_COMPLETE':r['code']='WRONG_REASON'
        save(rp,rr)
    elif mode=='early_rejection':
        index=next(i for i,r in enumerate(rr) if r['event']=='CASE_BEGIN')+1
        rr.insert(index,dict(event='DETECTOR',at_ns=rr[index-1]['at_ns'],pid=rr[index-1]['pid'],native_thread_id=1,thread_name='synthetic',case_id=cid,code='RESOURCE_READ_REJECTED',target='resource',detail={'counterfactual':True},fault_id=None));save(rp,rr)
    elif mode in ['missing_os_exit','wrong_os_time']:
        op,ors=find_os(clone,runid);child=next(r['pid_child'] for r in rr if r['event']=='CHILD_SPAWNED')
        if mode=='missing_os_exit':ors=[r for r in ors if not(r['event']=='PROCESS_CLOSED' and r['pid']==child)]
        else:
            for r in ors:
                if r['event']=='PROCESS_CLOSED' and r['pid']==child:r['exit_filetime']=str(int(r['exit_filetime'])+10000)
        save(op,ors)
    elif mode=='missing_pending_completion':
        wp=run/'external/WATCH.jsonl';ws=readrows(wp);victim=next(r['seq'] for r in ws if r['event']=='IO_COMPLETION' and r['closing'])
        ws=[r for r in ws if r['seq']!=victim];mapping={r['seq']:i+1 for i,r in enumerate(ws)}
        for r in ws:
            if r['event']=='NOTIFY_DECISION':r['raw_seq']=mapping[r['raw_seq']]
        save(wp,ws)
    else:
        stderr=run/'external/launcher/CONTROLLER.stderr.log';raw=stderr.read_bytes();assert b'EMERGENCY_JOURNAL_FAILURE' in raw
        b=b''.join(l+b'\n' for l in raw.splitlines() if b'EMERGENCY_JOURNAL_FAILURE' not in l);stderr.write_bytes(b)
        cp=run/'external/launcher/CLOSED.json';closed=json.loads(cp.read_bytes())
        for row in closed['files']:
            if row['name']=='CONTROLLER.stderr.log':row['bytes']=len(b);row['sha256']=hashlib.sha256(b).hexdigest()
        cp.write_text(json.dumps(closed,sort_keys=True)+'\n')
    members=[]
    for p in sorted((clone/'legacy').rglob('*')):
        if p.is_file() and not p.name.startswith('AUDIT_INPUT_MANIFEST'):
            members.append(dict(path=p.relative_to(clone/'legacy').as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    mf=clone/'legacy/SYNTHETIC_INPUT_MANIFEST.json';mf.write_text(json.dumps(dict(members=members),sort_keys=True)+'\n')
    # Exclude the just-created synthetic manifest from ordinary members; Evidence reads its own bytes separately.
    try:
        raw=raw_audit.audit(clone/'legacy',mf.name)
        cpu8_audit.qualify(clone,raw,runid,cid,'D0')
    except (AssertionError,ValueError,KeyError) as e:
        result=dict(case=mode,status='EXPECTED_RAW_REJECTION',error=str(e),synthetic_mutation=True,not_an_executed_fault=True);results.append(result)
    else:raise AssertionError('counterfactual wrongly accepted '+mode)
    (clone/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
(ROOT/'development/BRIDGE_REGRESSIONS.json').write_text(json.dumps(dict(cases=results,status='PASS'),sort_keys=True,indent=2)+'\n');print(json.dumps(results,sort_keys=True))
