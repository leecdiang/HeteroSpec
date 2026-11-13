"""Post-terminal full text/capture readback and descriptive-statistic replay.

No CUDA/model calls, no arithmetic eligibility inferred from exit codes. Waits
for success by default; a failed gate is left for explicit agent repair/closure.
"""
from pathlib import Path
from collections import Counter
import argparse,datetime,fcntl,gzip,hashlib,importlib.util,json,os,re,sys,time

def sha(p):
    h=hashlib.sha256()
    with p.open('rb')as f:
        for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
    return h.hexdigest()
def read(p):return json.loads(p.read_text())
def save(p,x):
    with p.open('x')as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)

def replay(root,work,out,driver):
    panel=work/'panel-01';records=read(panel/'CHECKED.json');plan=read(panel/'PLAN.json');rows=[]
    for w,checked in zip(plan['workers'],records):
        assert w['id']==checked['id'] and checked['status']=='COMPLETE'
        dest=panel/'runs'/w['id'];payload=read(panel/w['job']);assert sha(panel/w['job'])==w['job_sha256']
        meta=read(dest/'native/result.json');assert sha(dest/'native/result.json')==checked['native_result_sha256']
        assert read(dest/'HOST.json')==checked['actual_host'] and read(dest/'CLOCKS.json')==checked['actual_result_clocks']
        for i,(entry,call)in enumerate(zip(payload['inputs'],checked['calls'])):
            path=dest/'native'/entry['name']/'receipt.json';r=read(path);assert sha(path)==call['receipt_sha256']
            assert r['service_seconds']==call['service_s'] and r['request_seconds']==call['request_s']
            assert r['target_phases']==call['target_phases'] and r['draft_phases']==call['draft_phases']
            assert r['proposal_mode']==w['proposal_mode'] and r['k']==w['k'] and r['target_output_reserve']==8
            assert all(v==0 for v in r['observed_API_calls_within_service'].values())
            histogram=dict(Counter(str(x['width'])for x in r['executions']if x['phase']=='VERIFY'))
            assert histogram==call['physical']['verify_width_histogram']
            assert sum(int(k)*v for k,v in r['target_physical_width_hist'].items())==call['physical']['target_rows']
            assert sum(int(k)*v for k,v in r['draft_physical_width_hist'].items())==call['physical']['draft_rows']
            assert len(r['cycles'])==call['cycles'] and sum(c['accepted']for c in r['cycles'])==call['accepted_proposals']
            assert sum(len(c['proposals'])for c in r['cycles'])==call['proposed'] and len(r['ids'])==call['output_tokens']
            if w['proposal_mode']=='replay':assert r['draft_calls']==0 and r['proposal_tape_sha256']==entry['input']['proposal_tape_sha256']
        rows.append(checked)
    sys.path.insert(0,str(driver));import panel as analyzer
    result=analyzer.analyze(rows);expected=read(panel/'RESULTS.json');assert canonical(result)==canonical(expected)
    assert result['live']['measurements']==64 and result['replay']['measurements']==32
    save(out/'RESULTS_REPRODUCED.json',result)
    # Compare actual live proposal operands to the independently produced common
    # position-indexed tape; retain differences instead of assuming equality.
    tapes=read(work/'OWNED_TAPES_FROZEN.json')['tapes'];fidelity=[]
    for w in plan['workers']:
        if w['proposal_mode']!='live':continue
        payload=read(panel/w['job'])
        for key,entry in zip(w['primers']+w['roots'],payload['inputs']):
            r=read(panel/'runs'/w['id']/'native'/entry['name']/'receipt.json');t=tapes[key]['tape'];diff=[]
            for c in r['cycles']:
                tape_row=t['rows'][c['base']-len(t['prompt_ids'])]
                if tape_row['seed']!=c['seed'] or tape_row['proposals'][:w['k']]!=c['proposals']:diff.append(dict(cycle=c['cycle'],base=c['base']))
            fidelity.append(dict(worker=w['id'],root=key,cycles=len(r['cycles']),all_actual_live_proposals_match_common_tape=not diff,differences=diff))
    save(out/'TAPE_FIDELITY_AUDIT.json',dict(records=fidelity,all_match=all(x['all_actual_live_proposals_match_common_tape']for x in fidelity),
        scope='Observed live operands at visited bases, not a guarantee for other inputs. Free replay still excludes live drafting cost.'))
    save(out/'STATISTICS_REPLAY_CHECKED.json',dict(passed=True,raw_request_receipts_checked=sum(len(w['calls'])for w in rows),
        reported_results_sha256=sha(panel/'RESULTS.json'),reproduced_results_sha256=sha(out/'RESULTS_REPRODUCED.json'),
        analyzer_sha256=sha(driver/'panel.py'),model_forwards=0,new_native_jobs=0,inference='DESCRIPTIVE_ONLY'))

def costs(root,work,out):
    lanes={}
    for name in [f'm2-run-{i:02d}' for i in range(1,int(work.name.rsplit('-',1)[1])+1)]:
        w=root/name;events=[json.loads(x)for x in(w/'ledger.jsonl').read_text().splitlines()];reserved=[x for x in events if x['event']=='RESERVE'];hosts=[]
        for row in reserved:
            dest=Path(row['out']);p=dest/'HOST.json';h=read(p)if p.exists()else None
            hosts.append(dict(logical_out=str(dest.relative_to(root)),phase=row['phase'],reserved_requests=row['requests'],reserved_rows=row['rows'],
                host=h,host_sha256=sha(p)if p.exists()else None,expected_native_negative='negative-'in dest.name))
        lanes[name]=dict(ledger_sha256=sha(w/'ledger.jsonl'),reserved_requests=sum(x['requests']for x in reserved),reserved_rows=sum(x['rows']for x in reserved),
            reserved_workers=len(reserved),hosts=hosts,native_worker_wall_known_s=sum(x['host']['worker_wall_s']for x in hosts if x['host']and x['host']['worker_wall_s']is not None))
    build={}
    for core in ('loop4','packed'):
        build[core]={phase:read(root/'m2-build-01'/core/phase/'command.json')for phase in ('compile','link')}
    save(out/'COSTS.json',dict(lanes=lanes,build_phase_clocks=build,build_inclusive_wall_s=None,
        historical_epoch_statuses={f'm2-audit-{i:02d}':read(root/f'm2-audit-{i:02d}'/'STATUS.json')for i in range(1,int(work.name.rsplit('-',1)[1])+1)},
        current_epoch_status=read(root/('m2-audit-'+work.name.rsplit('-',1)[1])/'STATUS.json'),
        inherited_accounting=read(work/'INHERITED_ACCOUNTING.json'),clock_categories_overlap_do_not_add=True,
        reserved_rows_are_bounds_not_actual_physical_work=True,missing_build_or_setup_clocks_are_unknown_not_zero=True,
        actual_model_or_kernel_GPU_time='NOT_MEASURED_FROM_PROCESS_WALL',native_reexecution_by_this_observer=False))

def scrub(text,root):
    text=text.replace(str(root),'$WORKSPACE').replace(str(Path.home()),'$HOME')
    text=re.sub(r'GPU-[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}','$ALLOCATED_GPU',text)
    assert not re.search(r'gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|(?<![0-9])192\.168\.[0-9]+\.[0-9]+',text)
    return text
def narrow(x):
    if isinstance(x,dict):return {k:('USER_AUTHORIZED_ALLOCATION'if k=='allocation_id'else narrow(v))for k,v in x.items()if k not in ('available_RAM_bytes','disk_free_bytes')}
    if isinstance(x,list):return [narrow(v)for v in x]
    return x

def verify_bundle(out):
    index={x['path']:x for x in read(out/'TEXT_INDEX.json')['files']};head='{"schema":"linux-transfer.public-text-bundle.v1","records":['
    seen=set();decoder=json.JSONDecoder();buffer='';ended=False;total=0
    with gzip.open(out/'scientific-records.json.gz','rt',encoding='utf8')as f:
        prefix=f.read(len(head));assert prefix==head;total+=len(prefix.encode())
        eof=False
        while not ended:
            block=f.read(4*1024**2);eof=not block;total+=len(block.encode());buffer+=block
            while True:
                buffer=buffer.lstrip(' \n\r\t,')
                if buffer.startswith(']}'):
                    buffer=buffer[2:];ended=True;break
                if not buffer:break
                try:record,end=decoder.raw_decode(buffer)
                except json.JSONDecodeError:
                    assert not eof,'Incomplete gzip record';break
                buffer=buffer[end:];key=record['path'];assert key not in seen and key in index
                b=record['text'].encode('utf8');i=index[key];assert len(b)==i['exported_bytes']and hashlib.sha256(b).hexdigest()==i['exported_sha256'];seen.add(key)
            if eof:assert ended,'Truncated bundle'
        rest=f.read();total+=len(rest.encode());assert not(buffer+rest).strip()
    assert len(seen)==len(index)and total==read(out/'TEXT_INDEX.json')['uncompressed_bytes'];return len(seen),total

def export(root,work,out,driver,status):
    out.mkdir();started=time.monotonic();analysis=out/'analysis';analysis.mkdir()
    if status['status']=='COMPLETE':replay(root,work,analysis,driver)
    else:save(analysis/'STATISTICS_REPLAY_SKIPPED.json',dict(reason='Native gates or full panel incomplete; no complete-pilot performance conclusion',status=status))
    costs(root,work,analysis)
    folders=['m2-run-01',work.name,'m2-audit-01','m2-audit-'+work.name.rsplit('-',1)[1],'m2-runtime-01','m2-runtime-'+work.name.rsplit('-',1)[1],
        'm2-native-source-01','m2-driver-source-01','m2-driver-source-'+work.name.rsplit('-',1)[1],'m2-build-01','m2-activation-01']
    folders=sorted(set(folders)|{f'{kind}-{i:02d}' for kind in ('m2-run','m2-audit','m2-runtime','m2-driver-source') for i in range(1,int(work.name.rsplit('-',1)[1])+1)})
    texts=[];binaries=[];seen=set()
    for folder in folders:
        for p in sorted((root/folder).rglob('*')):
            if not p.is_file()or p in seen:continue
            seen.add(p);key=str(p.relative_to(root))
            if p.suffix in ('.bin','.f32'):
                binaries.append(dict(path=key,bytes=p.stat().st_size,sha256=sha(p)));continue
            if p.suffix in ('.json','.jsonl','.py','.cpp','.hpp','.h','.inc','.txt','.md','.log'):texts.append((p,key))
    for p in sorted(root.glob('m2-*.log')):
        if p.is_file():texts.append((p,p.name))
    for pattern in ('m2-run-*-completed-snapshot.json','m2-*.py'):
        for p in sorted(root.glob(pattern)):
            if p.is_file():texts.append((p,p.name))
    for p in (root/'m2-run-01-completed-snapshot.json',root/'m2-activate-01.private.py',root/'run-01/reference-01/REFERENCE_FREEZE.json',root/'m1-source-01/M/RUNTIME_PIN.json'):
        if p.exists():texts.append((p,str(p.relative_to(root))))
    for p in analysis.glob('*.json'):texts.append((p,'analysis/'+p.name))
    texts=sorted(dict((key,p)for p,key in texts).items());index=[];expanded=0
    with(out/'scientific-records.json.gz').open('xb')as raw,gzip.GzipFile(fileobj=raw,mode='wb',compresslevel=9,mtime=0)as gz:
        header=b'{"schema":"linux-transfer.public-text-bundle.v1","records":[';gz.write(header);expanded+=len(header)
        for count,(key,p)in enumerate(texts):
            b=p.read_bytes();text=b.decode('utf8')
            if p.suffix=='.json':text=json.dumps(narrow(json.loads(text)),indent=2,allow_nan=False)+'\n'
            elif p.suffix=='.jsonl':text=''.join(json.dumps(narrow(json.loads(line)),allow_nan=False)+'\n'for line in text.splitlines()if line)
            text=scrub(text,root);exported=text.encode();index.append(dict(path=key,raw_bytes=len(b),raw_sha256=hashlib.sha256(b).hexdigest(),exported_bytes=len(exported),exported_sha256=hashlib.sha256(exported).hexdigest(),redacted=b!=exported))
            record=json.dumps(dict(path=key,text=text),ensure_ascii=False,separators=(',',':')).encode()
            if count:gz.write(b',');expanded+=1
            gz.write(record);expanded+=len(record)
        gz.write(b']}');expanded+=2
    save(out/'TEXT_INDEX.json',dict(files=index,uncompressed_bytes=expanded))
    save(out/'BINARY_CAPTURE_INDEX.json',dict(count=len(binaries),bytes=sum(x['bytes']for x in binaries),files=binaries,contents='RETAINED_PRIVATE_NOT_REDISTRIBUTED'))
    for row in binaries:assert sha(root/row['path'])==row['sha256'],'Private capture changed during full second readback'
    scope=dict(schema='linux-transfer.public-export.v1',status='COMPLETE_SANITIZED_EXPORT',formal_performance_status='DESCRIPTIVE64_LIVE32_REPLAY_COMPLETE'if status['status']=='COMPLETE'else'INCOMPLETE_NO_COMPLETE_PILOT_CLAIM',
        text_files=len(index),binary_captures=len(binaries),bundle_sha256=sha(out/'scientific-records.json.gz'),text_index_sha256=sha(out/'TEXT_INDEX.json'),binary_index_sha256=sha(out/'BINARY_CAPTURE_INDEX.json'),
        private_raw_capture_full_readback=True,public_raw_captures=False,redaction='Host roots/home/UUID/allocation id replaced; unrelated free-RAM/disk inventory omitted; exact raw/derived byte commitments retained',
        excluded=['model weights','full vocabulary','compiled binaries','private raw vector/KV payloads','unrelated company inventory'],native_reexecution=False,statistical_inference='DESCRIPTIVE_ONLY')
    save(out/'EXPORT_SCOPE.json',scope);count,bytes_read=verify_bundle(out)
    save(out/'LOCAL_READBACK.json',dict(passed=True,text_files=count,uncompressed_bytes_verified=bytes_read,private_raw_captures_read_back=len(binaries),
        private_capture_bytes_read_twice=sum(x['bytes']for x in binaries)*2,wall_s=time.monotonic()-started,scope='Full sanitized gzip text and private capture byte readback; not independent numerical requalification',model_forwards=0,new_native_jobs=0))
    print(json.dumps(dict(status='EXPORT_AND_READBACK_PASS',out=str(out),text_files=count,private_captures=len(binaries),bundle_sha256=scope['bundle_sha256'])),flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--work',default='m2-run-03');p.add_argument('--out',type=Path,required=True);p.add_argument('--terminal-failure',action='store_true');a=p.parse_args()
    root=a.root.resolve();work=root/a.work;driver=root/('m2-driver-source-'+a.work.rsplit('-',1)[1]);status_path=root/('m2-audit-'+a.work.rsplit('-',1)[1])/'STATUS.json'
    os.sched_setaffinity(0,{32});os.nice(19)
    while not status_path.exists():time.sleep(10)
    status=read(status_path)
    if status['status']!='COMPLETE'and not a.terminal_failure:
        print(json.dumps(dict(status='DEFERRED_FOR_GATE_REPAIR',native_status=status,no_export_or_GPU_work=True)),flush=True);return
    with(root/'STUDY_SCHEDULING.lock').open('a')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);export(root,work,a.out.resolve(),driver,status)
if __name__=='__main__':main()
