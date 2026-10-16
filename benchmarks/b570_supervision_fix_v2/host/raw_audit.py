"""Read-only raw reconstruction. No Windows/GPU APIs, report inputs or fixtures.

The output attests only the manifested raw prefix. Final review, prospective
remote freeze and task-closing/recovery gates remain separately mandatory.
"""
import argparse,base64,hashlib,json,struct,sys,importlib.util
from pathlib import Path,PureWindowsPath
sys.path.insert(0,str(Path(__file__).resolve().parent))
_spec=importlib.util.spec_from_file_location('_b570_receipts',Path(__file__).resolve().parents[1]/'check_receipts.py')
_receipts=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_receipts)
CASES,BASE_CHECKS,EXTRA_CHECKS,judge,confirmation_order=(_receipts.CASES,_receipts.BASE_CHECKS,_receipts.EXTRA_CHECKS,_receipts.judge,_receipts.confirmation_order)
from coverage import evaluate, pre_injection
from evidence_io import Evidence, strict_json
from audit_integrity import round_integrity
from output_integrity import positive_output, capture_files
from diagnostics import diagnostic

ORIGINAL=PureWindowsPath('C:/hs/b570-supervision-fix-v2-20261016')
def digest(data):return hashlib.sha256(data).hexdigest()
def read_json(p):return strict_json(p.read_bytes())
def read_rows(p):return [strict_json(s) for s in p.read_bytes().splitlines()]
def decode_notifications(data):
    if not data:return []
    result=[];offset=0
    while True:
        assert offset+12<=len(data)
        nxt,action,size=struct.unpack_from('<III',data,offset)
        assert 1<=action<=5 and size>0 and size%2==0 and offset+12+size<=len(data)
        rel=data[offset+12:offset+12+size].decode('utf-16-le');p=PureWindowsPath(rel)
        assert not p.is_absolute() and '..' not in p.parts and ':' not in rel
        result.append((action,rel))
        if not nxt:break
        assert nxt%4==0 and nxt>=12+size and offset+nxt<len(data);offset+=nxt
    return result
def verify_watch_buffers(rows):
    handles={r['watch_id']:r for r in rows if r['event']=='WATCH_ARMED'}
    try:
        for r in rows:
            if r['event']!='RAW_NOTIFY':continue
            data=base64.b64decode(r['raw_base64'],validate=True);assert len(data)==r['bytes']
            expected=decode_notifications(data);h=handles[r['watch_id']];assert h['at_ns']<=r['at_ns']
            actual=[d for d in rows if d['event']=='NOTIFY_DECISION' and d['raw_seq']==r['seq']]
            assert len(actual)==len(expected)
            for d,(action,rel) in zip(actual,expected):
                assert d['action']==action and d['canonical']==str(PureWindowsPath(h['root'])/rel).lower()
                assert d['watch_id']==r['watch_id'] and d['writer_PID'] is None and d['operation_time'] is None
                if d['allowed']:assert h['kind'] in ('content','rootmeta','namespace') and d['state']=='ACTIVE'
                if d['allowed'] and h['kind']!='content':assert action==3
        return True
    except (AssertionError,KeyError,ValueError,UnicodeError,struct.error):return False
def audit(root,manifest_relative='AUDIT_INPUT_MANIFEST.json',ledger_relative='task/PROCESS_LEDGER.snapshot.jsonl'):
    root=Path(root);problems=[]
    inputs=Evidence(root,root/manifest_relative)
    read_json=inputs.json;read_rows=inputs.rows
    def local(p):
        w=PureWindowsPath(p)
        if w.is_absolute():return root/Path(*w.relative_to(ORIGINAL).parts)
        q=Path(p);assert not q.is_absolute() and '..' not in q.parts;return root/q
    def reference(p):
        p=Path(p);return dict(path=p.relative_to(root).as_posix(),sha256=digest(inputs.bytes(p)))
    manifest=root/manifest_relative;valid_manifest=True
    ledger_path=root/ledger_relative;ledger=read_rows(ledger_path) if ledger_path.is_file() else []
    opened={};closed={};ledger_errors=[]
    for r in ledger:
        if r['kind']=='PROCESS_CREATE':
            key=(r['pid'],r['created_filetime'])
            if key in opened:ledger_errors.append('duplicate process create')
            if r.get('command_sha256') is None:ledger_errors.append('missing command identity')
            if r['role']=='descendant' and not any(x['pid']==r['parent_pid'] and x['at_ns']<=r['at_ns'] for x in opened.values()):ledger_errors.append('unobserved process parent')
            opened[key]=r
        elif r['kind']=='PROCESS_CLOSED':
            key=(r['pid'],r['created_filetime'])
            if key in closed:ledger_errors.append('duplicate process closure')
            closed[key]=r
            actual=(r['exit_filetime']-r['created_filetime'])/1e7
            if abs(actual-r['lifetime_seconds'])>1e-6:ledger_errors.append('incorrect lifetime sum')
            if key not in opened or r['exit_filetime']<r['created_filetime']:ledger_errors.append('invalid process closure')
    if set(opened)!=set(closed):ledger_errors.append('unclosed processes in published prefix')
    process_ok=bool(ledger) and not ledger_errors
    reports=[];confirmation=[];forbidden={k:0 for k in ('GPU_queries','GPU_initializations','model_file_reads','model_requests','graph_computes','scientific_native_starts')}
    for config_path in sorted((root/'runs').glob('*/CONFIG.json')) if (root/'runs').exists() else []:
        cfg=read_json(config_path);external=config_path.parent/'external'
        for k in forbidden:forbidden[k]+=cfg.get(k,1)
        round_path=external/'ROUND.jsonl';watch_path=external/'WATCH.jsonl'
        if not round_path.is_file() or not watch_path.is_file():
            reports.append(dict(run=cfg['id'],status='EVIDENCE_MISSING',missing='round/watch raw'));continue
        rows=read_rows(round_path);watch=read_rows(watch_path)
        buffers_ok=verify_watch_buffers(watch)
        if not buffers_ok:problems.append(cfg['id']+': raw notification/decision mismatch')
        if any(r['event'] in ('WATCH_ENGINE_ERROR','WATCH_CLOSE_ERROR') for r in watch):problems.append(cfg['id']+': watcher engine/closure failure')
        streams={name:[row for spec in cfg['cases'] for row in (read_rows(external/spec['id']/(name.upper()+'.jsonl')) if (external/spec['id']/(name.upper()+'.jsonl')).is_file() else [])] for name in ('resource','directory')}
        integrity=True
        try:
            round_integrity(cfg,rows,watch,read_json(external/'CONTROLLER_END.json'),
                read_json(config_path.parent/'LAUNCH_RECEIPT.json'),read_json(external/'launcher/CLOSED.json'))
        except (ValueError,KeyError,OSError,TypeError) as error:
            integrity=False;problems.append(cfg['id']+': '+diagnostic(error,root))
        resource_budget_ok=all(r['values']['RSS']<=2147483648 and r['values']['controller_RSS']<=2147483648 and r['values']['host_available']>=2147483648 and r['values']['disk_free']>=10737418240 for r in streams['resource'] if r['event']=='READ_END')
        directory_budget_ok=all(r['values']['bytes']<=2097152 and r['values']['files']<=32 and r['values']['historical_files_scanned']==0 for r in streams['directory'] if r['event']=='READ_END')
        if not resource_budget_ok or not directory_budget_ok:problems.append(cfg['id']+': actual sampled resource/directory budget violation')
        caps_ok=all((external/'source_caps'/name).is_file() and digest(inputs.bytes(external/'source_caps'/name))==value for name,value in cfg['code_hashes'].items())
        caps_ok=caps_ok and all(cfg.get(k)==0 for k in ('GPU_queries','GPU_initializations','model_file_reads','model_requests','graph_computes','scientific_native_starts'))
        if cfg['round']>=0:
            fpath=root/'repo/benchmarks/b570_supervision_fix_v2/results/CONFIRMATION_FREEZE.json'
            rpath=fpath.with_name('REMOTE_FREEZE.json')
            if fpath.is_file() and rpath.is_file():
                freeze=read_json(fpath);remote=read_json(rpath)
                caps_ok=caps_ok and digest(inputs.bytes(fpath))==cfg['freeze_sha256']==remote['freeze_sha256']
                caps_ok=caps_ok and all(freeze['bound_files'].get(k)==v for k,v in cfg['code_hashes'].items())
                caps_ok=caps_ok and all(digest(inputs.bytes(local(r['downloaded_path'])))==r['sha256'] for r in remote['members'])
                caps_ok=caps_ok and cfg['id']==freeze['rounds'][cfg['round']]['id'] and cfg['order']==freeze['rounds'][cfg['round']]['order']
            else:caps_ok=False
        actual_order=[r['case_id'] for r in rows if r['event']=='CASE_BEGIN']
        if actual_order!=[r['id'] for r in cfg['cases']][:len(actual_order)]:problems.append(cfg['id']+': case order mismatch')
        if cfg['round']>=0 and actual_order!=confirmation_order(cfg['round'])[:len(actual_order)]:problems.append(cfg['id']+': confirmation order differs from fixed matrix')
        for spec in cfg['cases']:
            cid=spec['id'];starts=[r for r in rows if r['event']=='CASE_BEGIN' and r['case_id']==cid];ends=[r for r in rows if r['event']=='CASE_CLOSED' and r['case_id']==cid]
            if not starts:
                reports.append(dict(run=cfg['id'],round=cfg['round'],case_id=cid,status='UNSTARTED'));continue
            if len(starts)!=1 or len(ends)!=1:
                reports.append(dict(run=cfg['id'],round=cfg['round'],case_id=cid,status='EVIDENCE_MISSING',missing='unique case lifecycle'));continue
            start,end=starts[0],ends[0];b,e=start['at_ns'],end['at_ns']
            case_rows=[r for r in rows if b<=r['at_ns']<=e]
            rejects=[r for r in case_rows if r['event']=='DETECTOR']
            rejects=[r for r in rejects if r.get('case_id')==cid]
            deferred=[r for r in rows if r['event']=='DETECTOR' and r.get('case_id')==cid and r['at_ns']>e]
            positives=[r for r in case_rows if r['event']=='POSITIVE_COMPLETE']
            detector=rejects[0] if rejects else positives[-1] if positives else None
            child_spawns=[r for r in case_rows if r['event']=='CHILD_SPAWNED'];child_closes=[r for r in case_rows if r['event']=='CHILD_CLOSED']
            commands=[r for r in case_rows if r['event'] in ('GO_SENT','CONTINUE_SENT')]
            control=[r for r in case_rows if r['event']=='CONTROL_POINT']
            producer=[];producer_paths=[];modules=[]
            for slot in spec['slots']:
                folder=external/cid/slot;p=folder/'PRODUCER.jsonl'
                if p.is_file():producer.extend(read_rows(p));producer_paths.append(p)
                p=folder/'MODULE_GATE.json'
                if p.is_file():modules.append(read_json(p))
            process_match=True
            for r in child_spawns:
                k=(r['pid_child'],r['os_times']['creation_FILETIME'])
                c=next((x for x in child_closes if x['pid_child']==r['pid_child'] and x['slot']==r['slot']),None)
                process_match=process_match and k in opened and k in closed and c is not None
                if c is not None and k in closed:process_match=process_match and c['os_times']['exit_FILETIME']==closed[k]['exit_filetime'] and c['exit_code']==closed[k]['exit_code']
            cleanup=bool(child_spawns) and len(child_spawns)==len(child_closes) and all(r['pumps_closed'] and r['observers_closed'] and r['os_times']['exit_FILETIME']>0 for r in child_closes)
            coverage={};normal_cov=True
            for spawn in child_spawns:
                slot=spawn['slot'];close=next((x for x in child_closes if x['slot']==slot),None)
                if not close:normal_cov=False;continue
                coverage[slot]={}
                for name in streams:
                    sample=[r for r in streams[name] if r.get('slot')==slot]
                    cov=evaluate(sample,spawn['launch_ns'],close['exit_ns']);coverage[slot][name]=cov
                    normal_cov=normal_cov and cov['valid']
            wrows=[]
            loops={r['begin_ns']:r for r in watch if r['event']=='WATCH_LOOP_END'}
            for r in watch:
                if r['event']=='WATCH_LOOP_BEGIN' and b<=r['begin_ns']<=e:
                    finish=loops.get(r['begin_ns'])
                    if finish is not None and finish['end_ns']<=e:
                        wrows.extend([dict(r,event='READ_BEGIN'),dict(finish,event='READ_END')])
            wcov=evaluate(wrows,b,e);normal_cov=normal_cov and wcov['valid']
            target=spec['target'];fault_id=f"{cfg['round']}:{cid}";trigger=None;effect=False;reached=False;extras={};missing_outputs=[]
            injection=external/cid/'INJECTION.json'
            fault_events=[r for r in producer if r['event']=='FAULT_CONTROL']
            inj_begin=[r for r in case_rows if r['event']=='INJECTION_BEGIN'];inj_end=[r for r in case_rows if r['event']=='INJECTION_END']
            if spec['kind']=='positive':
                data_ok=True
                source_hash=next(v for k,v in cfg['code_hashes'].items() if PureWindowsPath(k).as_posix()=='host/cpu_child.py')
                for spawn in child_spawns:
                    slot=spawn['slot'];folder=external/cid/slot;active=local(cfg['registry'][slot]['path'])
                    files,absent=capture_files(inputs,dict(data=active/'DATA.bin',ack=active/'ACK.jsonl',stdout=folder/'stdout.log',stderr=folder/'stderr.log'))
                    missing_outputs.extend(absent)
                    captured=[r['record'] for r in case_rows if r['event']=='CHILD_RECORD' and r['slot']==slot]
                    closed_child=next((r for r in child_closes if r['slot']==slot),None)
                    if absent or closed_child is None:
                        data_ok=False;continue
                    data_ok=data_ok and files['data']==b''.join(bytes([i])*64 for i in range(4)) and positive_output(files['stdout'],files['stderr'],files['ack'],captured,spawn['pid_child'],source_hash,closed_child['counts'])
                if missing_outputs:problems.append(cfg['id']+': '+cid+': missing positive outputs: '+', '.join(missing_outputs))
                ready_records=[r['record'] for r in case_rows if r['event']=='CHILD_RECORD' and r['record'].get('event')=='READY']
                data_ok=data_ok and len(ready_records)==len(child_spawns) and all(r['source_sha256']==source_hash for r in ready_records) and len(modules)==len(child_spawns) and all(m['matched'] for m in modules)
                reached=len(control)==len(child_spawns) and len(child_spawns)>0 and data_ok
            elif spec.get('filesystem') and injection.is_file():
                x=read_json(injection);p=local(x['target']);token=('CPU_FAULT:'+fault_id).encode()
                effect=(x['fault_id']==fault_id and x['trigger']==spec['trigger'] and x['target'].lower()==target.lower() and bytes.fromhex(x['after_hex'])==token and digest(token)==x['after_sha256'] and x['before_sha256']!=x['after_sha256'] and p.is_file() and inputs.bytes(p)==token and x['before_file_id']==x['after_file_id'])
                deferred_ok=all(r.get('owner_remains_failed') and r['target'].lower()==target.lower() and r['code']==spec['detector'] and r['post_case_identity']['file_id']==x['after_file_id'] and r['post_case_identity']['mtime_ns']==x.get('after_mtime_ns') and r['post_case_sha256']==x['after_sha256'] for r in deferred)
                effect=effect and deferred_ok
                reached=bool(control) and effect
                trigger=dict(code=x['trigger'],begin_ns=x['begin_ns'],end_ns=x['end_ns'],fault_id=fault_id,target_id=target)
            elif cid in ('quick_exit','abnormal_exit','truncated_stdout','log_overflow'):
                f=next((r for r in fault_events if r['code']==spec['trigger']),None)
                if f:
                    trigger=dict(code=f['code'],begin_ns=f['at_ns'],end_ns=detector['at_ns'] if detector else f['at_ns'],fault_id=fault_id,target_id=target)
                    if cid=='quick_exit':effect=bool(child_closes) and all(r['exit_code']==0 for r in child_closes) and not any(r['event']=='GO_RECEIVED' for r in producer);reached=effect
                    elif cid=='abnormal_exit':effect=bool(child_closes) and child_closes[-1]['exit_code']==23;reached=bool(control) and effect
                    elif cid=='truncated_stdout':
                        raw=inputs.bytes(external/cid/spec['slots'][0]/'stdout.log');effect=raw.endswith(b'{"event":"INCOMPLETE"');reached=bool(control) and effect
                    else:
                        raw=inputs.bytes(external/cid/spec['slots'][0]/'stdout.log');full={}
                        for line in raw.split(b'\n')[:-1]:
                            j=json.loads(line)
                            if j.get('event')=='FRAME':full[j['index']]=line+b'\n'
                        ackpath=local(cfg['registry'][spec['slots'][0]]['path'])/'ACK.jsonl'
                        acks=[json.loads(line) for line in inputs.bytes(ackpath).split(b'\n')[:-1]] if ackpath.is_file() else []
                        subset=bool(acks) and all(a['index'] in full and a['bytes']==len(full[a['index']]) and a['sha256']==digest(full[a['index']]) for a in acks)
                        extras.update(soft_limit_reached=len(raw)>32768,ack_nonempty=bool(acks),all_ack_frames_retained=subset,hard_limit_respected=len(raw)<=32768+131072)
                        effect=all(extras.values());reached=bool(control) and effect
            elif inj_begin and inj_end:
                ib,ie=inj_begin[0],inj_end[-1];trigger=dict(code=spec['trigger'],begin_ns=ib['at_ns'],end_ns=ie['at_ns'],fault_id=fault_id,target_id=target)
                if cid=='wrong_module':effect=bool(modules) and all(not m['matched'] and m['expected_python_sha256']=='0'*64 and any(x['sha256']!=m['expected_python_sha256'] for x in m['actual']) for m in modules);reached=effect
                elif cid=='journal_write_failure':effect=bool(ie['effect'].get('actual_write_failed')) and ie['effect'].get('failed_path')==str(PureWindowsPath(cfg['root'])/'external'/cid/'RESOURCE.jsonl');reached=effect
                elif cid=='notification_loss':effect=any(r['event']=='PARSER_LOSS_INJECTED' and b<=r['at_ns']<=e for r in watch) and any(r['event']=='RAW_NOTIFY' and r['bytes']==0 and b<=r['at_ns']<=e for r in watch);reached=bool(control) and effect
                elif cid=='resource_read_failure':effect=bool(ie['effect'].get('closed_handle')) and any(r['event']=='READ_ERROR' for r in streams['resource'] if b<=r['at_ns']<=e);reached=bool(control) and effect
                elif cid=='directory_read_timeout':effect=any(r['event']=='DIRECTORY_STALL_CONTROL_POINT' for r in case_rows) and any(not x['directory']['valid'] and x['directory']['max_effective_gap_ns']>1000000000 for x in coverage.values());reached=bool(control) and effect
                elif cid=='watcher_stall':effect=any(r['event']=='STALL_CONTROL_POINT' and b<=r['at_ns']<=e for r in watch) and not wcov['valid'] and wcov['max_effective_gap_ns']>1000000000;reached=bool(control) and effect
                elif cid=='child_timeout':effect=bool(detector and detector.get('detail',{}).get('alive') and detector['detail']['observed_ns']>=detector['detail']['deadline_ns']) and any(r.get('code')=='EXCEED_CHILD_DEADLINE' for r in fault_events);reached=effect
            coverage_checked=normal_cov
            if cid in ('directory_read_timeout','watcher_stall','resource_read_failure','quick_exit','journal_write_failure'):
                # These are rejected qualifications, never ordinary valid coverage.
                coverage_checked=effect and bool(detector and detector['code']==spec['detector'])
                if cid!='watcher_stall':coverage_checked=coverage_checked and wcov['valid']
                if cid in ('directory_read_timeout','resource_read_failure','journal_write_failure'):
                    other='resource' if cid=='directory_read_timeout' else 'directory';coverage_checked=coverage_checked and all(c[other]['valid'] for c in coverage.values())
                if trigger and cid in ('directory_read_timeout','resource_read_failure','journal_write_failure'):
                    affected='directory' if cid=='directory_read_timeout' else 'resource'
                    for spawn in child_spawns:
                        affected_rows=[r for r in streams[affected] if r.get('slot')==spawn['slot']]
                        pre=pre_injection(affected_rows,spawn['launch_ns'],trigger['begin_ns'],require_crossing=cid!='journal_write_failure',allow_dangling=cid=='journal_write_failure')
                        coverage_checked=coverage_checked and pre['valid']
                if cid=='watcher_stall':
                    coverage_checked=coverage_checked and bool(trigger) and pre_injection(wrows,b,trigger['begin_ns'])['valid'] and all(c[n]['valid'] for c in coverage.values() for n in ('resource','directory'))
                if cid=='quick_exit':coverage_checked=coverage_checked and all(set(c['errors'])<={'no valid samples'} for per in coverage.values() for c in per.values())
            negative=spec['kind']=='negative';object_match=bool(detector and (not negative or str(detector.get('target','')).lower()==target.lower()))
            if spec.get('filesystem') and object_match:
                d=detector.get('detail',{});x=read_json(injection) if injection.is_file() else {}
                object_match=(d.get('file_identity') or {}).get('file_id')==x.get('after_file_id') and any(r['event']=='NOTIFY_DECISION' and r['seq']==d.get('decision_seq') and r['canonical']==target.lower() and not r['allowed'] for r in watch)
            no_after=bool(detector) and not any(r['at_ns']>detector['at_ns'] for r in commands)
            handoffs=[]
            for state in case_rows:
                if state['event']=='SLOT_STATE' and state['state']=='SEALED':
                    h=state['handoff'];a=next((r for r in watch if r['event']=='WATCH_ARMED' and r['watch_id']==h['new']),None);c=next((r for r in watch if r['event']=='WATCH_CLOSED' and r['watch_id']==h['old']),None)
                    handoffs.append(bool(a and c and a['at_ns']<c['at_ns']<=state['at_ns'] and c['directory_closed'] and c['event_closed'] and not c['pending']))
            if cid=='normal_transition':
                pairs=[r for r in case_rows if r['event']=='PAIR_A_SEALED_BEFORE_B']
                extras.update(eight_pairs=len(pairs)==8,sixteen_unique_slots=len({r['slot'] for r in child_spawns})==16 and len(child_spawns)==16,sealed_guard_continuous=len(handoffs)==16 and all(handoffs),pending_io_closed=len(handoffs)==16 and all(handoffs))
            if cid=='normal_single':
                a=[r for r in case_rows if r['event']=='POST_AUDIT_BEGIN'];z=[r for r in case_rows if r['event']=='POST_AUDIT_END']
                extras.update(work_completed=bool(producer) and any(r['event']=='PRODUCER_STREAMS_FLUSHED' for r in producer),post_audit_separated=bool(a and z and child_closes and a[0]['at_ns']>=child_closes[-1]['exit_ns'] and z[-1]['at_ns']-a[0]['at_ns']>=1000000000))
            if cid=='normal_late_panel':
                hist=local(cfg['root'])/'protected/history';files=list(hist.rglob('*.bin'))
                extras.update(eight_thousand_files=len(files)==8000 and sum(p.stat().st_size for p in files)<=16777216 and all(inputs.bytes(p)==('CPU_HISTORY_'+p.stem).encode() for p in files),active_scan_only=all(r.get('values',{}).get('historical_files_scanned')==0 for r in streams['directory'] if r['event']=='READ_END' and b<=r['at_ns']<=e),historical_guard_continuous=any(r['event']=='WATCH_ARMED' and r['owner']=='history' and r['at_ns']<b for r in watch) and any(r['event']=='WATCH_CLOSED' and r['watch_id']=='history:sealed:0' and r['at_ns']>e for r in watch))
            if cid=='late_closed_slot_write':extras.update(a_sealed_b_active=any(r['event']=='LATE_WRITE_A_SEALED' for r in case_rows) and len(child_spawns)==2 and len(handoffs)==1,sealed_guard_continuous=bool(handoffs and all(handoffs)))
            if cid=='terminal_pending_completion':extras.update(pending_completion_observed=any(r['event']=='IO_COMPLETION' and r['watch_id'].startswith('pending_probe:') and r['closing'] and r['success'] and r['bytes']>0 for r in watch),pending_io_closed=any(r['event']=='WATCH_CLOSED' and r['watch_id'].startswith('pending_probe:') and r['directory_closed'] and r['event_closed'] and not r['pending'] for r in watch))
            if cid=='notification_loss':extras['production_parser_injected']=effect
            if cid=='watcher_stall':
                watch_threads={r.get('native_thread_id') for r in watch if r['event']=='WATCH_LOOP_BEGIN'}
                extras['independent_watchdog']=bool(detector and detector.get('native_thread_id') is not None and detector['native_thread_id'] not in watch_threads and any(r['event']=='STALL_CONTROL_POINT' for r in watch))
            if cid=='journal_write_failure':
                stderr=external/'launcher/CONTROLLER.stderr.log'
                outer=[strict_json(line) for line in inputs.bytes(stderr).splitlines() if line.startswith(b'{')]
                failure=[r for r in outer if r.get('event')=='EMERGENCY_JOURNAL_FAILURE' and r.get('case_id')==cid]
                expected=str(PureWindowsPath(cfg['root'])/'external'/cid/'RESOURCE.jsonl')
                extras['independent_outer_receipt']=bool(failure and detector and any(r['path']==expected and r['at_ns']<=detector['at_ns'] for r in failure))
                # Match the launcher's own file hash receipt to captured raw bytes.
                close=read_json(external/'launcher/CLOSED.json')
                entries=[r for r in close['files'] if r['name']=='CONTROLLER.stderr.log']
                extras['independent_outer_receipt']=extras['independent_outer_receipt'] and len(entries)==1 and entries[0]['sha256']==digest(inputs.bytes(stderr))
            if cid=='wrong_module':extras.update(no_go=not commands,no_data_write=not any((local(cfg['registry'][slot]['path'])/'DATA.bin').exists() for slot in spec['slots']))
            if cid=='truncated_stdout':extras['raw_tail_incomplete']=effect
            if cid=='abnormal_exit':extras['actual_nonzero_exit']=effect
            if cid=='child_timeout':extras.update(deadline_reached=effect,subtree_terminated=cleanup and all(r['terminated'] for r in child_closes))
            if cid=='quick_exit':extras.update(actual_creation_exit=process_match and cleanup,no_fabricated_coverage=not any(c['valid_reads']>0 and not c['valid'] for per in coverage.values() for c in per.values()))
            checks=dict(freeze_binding=caps_ok,raw_hashes=valid_manifest and buffers_ok,coverage_checked=integrity and coverage_checked and resource_budget_ok and directory_budget_ok,process_ledger=process_ok and process_match,cleanup_checked=cleanup,**extras)
            if negative:checks.update(trigger_side_effect=effect,detector_object_match=object_match)
            needed=BASE_CHECKS|EXTRA_CHECKS.get(cid,set())|({'trigger_side_effect','detector_object_match'} if negative else set())
            for name in needed:checks.setdefault(name,False)
            ref_keys={'fixture','lifecycle','cleanup','watch','coverage'}|needed|({'injection','detector'} if negative else set())
            refs={k:reference(round_path) for k in ref_keys};refs['watch']=reference(watch_path);refs['fixture']=reference(config_path);refs['process_ledger']=reference(ledger_path) if ledger_path.is_file() else reference(config_path);refs['raw_hashes']=reference(manifest) if manifest.is_file() else reference(config_path)
            if injection.is_file():refs['injection']=reference(injection)
            det=dict(code=detector['code'],at_ns=detector['at_ns'],fault_id=detector.get('fault_id',fault_id),target_id=detector.get('target',target)) if detector else {}
            receipt=dict(case_id=cid,round=cfg['round'],freeze_sha256=cfg.get('freeze_sha256'),fixture_ready=caps_ok,control_point_reached=reached,trigger_observed=effect,early_failure=not integrity or any(r['code']!=spec['detector'] or str(r.get('target','')).lower()!=str(target).lower() for r in rejects),cleanup_complete=cleanup,closed_ns=e,planned_target_id=target,no_work_after_detection=no_after,detector=det,verified=checks,evidence=refs)
            if trigger:receipt['trigger']=trigger
            status,reason=judge(receipt)
            record=dict(run=cfg['id'],revision=cfg['revision'],round=cfg['round'],case_id=cid,status=status,reason=reason,checks=checks,coverage=coverage,watcher_coverage=wcov,receipt=receipt,actual_rejections=rejects,deferred_owner_rejections=deferred,missing_outputs=missing_outputs)
            reports.append(record)
            if cfg['round']>=0:confirmation.append(receipt)
    confirmations={(r.get('round'),r.get('case_id')):r for r in reports if r.get('round',-1)>=0}
    planned=[(r,c) for r in range(3) for c in confirmation_order(r)]
    missing=[dict(round=r,case_id=c) for r,c in planned if (r,c) not in confirmations or confirmations[r,c]['status']=='UNSTARTED']
    budget=dict(child_starts=len(opened),child_lifetime_sum_seconds=sum(r['lifetime_seconds'] for r in closed.values()),ledger_prefix_start_ns=ledger[0]['at_ns'] if ledger else None,ledger_prefix_end_ns=ledger[-1]['at_ns'] if ledger else None,scope='Closed task-command prefix only; broker and future audit/delivery tail separately closed')
    complete_order=[(r['round'],r['case_id']) for r in confirmation]==planned
    return dict(schema=1,scope='Independent manifested raw reconstruction; not portable checker attestation or final readiness',forbidden_counts=forbidden,forbidden_count_scope='Aggregated registered CPU execution modes, executable/module/source/command evidence; not a syscall trace of unrelated apps',input_manifest_path=manifest.relative_to(root).as_posix(),ledger_prefix=dict(path=ledger_path.relative_to(root).as_posix(),bytes=len(inputs.bytes(ledger_path)),sha256=digest(inputs.bytes(ledger_path))),input_manifest_sha256=digest(inputs.bytes(manifest)) if manifest.is_file() else None,manifest_valid=valid_manifest,process_ledger_valid=process_ok,process_ledger_errors=ledger_errors,budget_prefix=budget,cases=reports,confirmation_receipts=confirmation,confirmation_unstarted=missing,confirmation_status='RAW_CONFIRMATION_PASS' if complete_order and len(confirmations)==57 and not missing and all(r['status']=='PASS' for r in confirmations.values()) and not problems else 'RAW_CONFIRMATION_INCOMPLETE_OR_FAILED',problems=problems)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output',required=True);p.add_argument('--manifest',default='AUDIT_INPUT_MANIFEST.json');p.add_argument('--ledger',default='task/PROCESS_LEDGER.snapshot.jsonl');a=p.parse_args();result=audit(a.root,a.manifest,a.ledger)
    data=(json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
    with Path(a.output).open('xb') as f:f.write(data)
    print(json.dumps(dict(cases=[{k:r.get(k) for k in ('run','case_id','status','reason')} for r in result['cases']],confirmation=result['confirmation_status'],manifest=result['manifest_valid'],ledger=result['process_ledger_valid'])))
