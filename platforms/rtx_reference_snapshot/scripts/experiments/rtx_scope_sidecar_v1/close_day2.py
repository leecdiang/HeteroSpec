import sys, json, hashlib, shutil
from pathlib import Path
from collections import Counter, defaultdict
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as c

out=c.DESIGN/'host_execution/day2'
assert not out.exists(), 'retain any existing closeout before proceeding'
with c.exclusive('day2-closeout',3600):
    binding=c.host.validate_freeze(c.MAIN)
    before=c.s.read(c.REPO/'work/day2-preflight.json')['main_checkpoint']
    for name,p in before.items():
        if name not in ('REQUESTS.jsonl','ATTEMPTS.json'):
            assert c.pin(c.MAIN,c.MAIN/name)==p, name
    h=hashlib.sha256();remaining=before['REQUESTS.jsonl']['bytes']
    with (c.MAIN/'REQUESTS.jsonl').open('rb') as f:
        while remaining:
            block=f.read(min(4*1024**2,remaining));assert block
            h.update(block);remaining-=len(block)
    assert h.hexdigest()==before['REQUESTS.jsonl']['sha256']
    attempts=c.s.read(c.MAIN/'ATTEMPTS.json')
    old=c.s.read(Path('D:/rtx151-archives/main-day1-increment/snapshot/ATTEMPTS.json'))
    assert attempts[:len(old)]==old and len(attempts)==14
    assert all(a['status']=='COMPLETE' and a['cleanup_verified'] and a['attempt_index']==0 for a in attempts)
    print('PUBLIC_AUDIT_AND_ANALYSIS_START',flush=True)
    analysis=c.s.analyze(c.DESIGN,c.MAIN);audit=analysis['audit']
    out.mkdir(parents=True)
    c.save(out/'AUDIT.json',audit);c.save(out/'ANALYSIS.json',analysis)
    assert not audit['failures'] and audit['selected_record_count']==1288 and audit['records_received']==1288
    assert not audit['missing_slot_ids'] and audit['status']=='CPU_AUDIT_COMPLETE'
    for family,state in audit['families'].items():
        assert state['eligible'] and not state['errors'],(family,state)
        assert state['selected_counts']=={'qualification':98,'warmup':42,'formal':504}
    assert analysis['qualified_performance'] is not None and all(v is not None for v in analysis['results'].values())
    day=[a for a in attempts if a['date_slot']==2]
    assert [a['unit_id'] for a in day]==['formal/d2/s0/Qwen','formal/d2/s0/SmolLM2','formal/d2/s1/Qwen','formal/d2/s1/SmolLM2']
    counts=Counter();payloads=[];per_family={};gaps={}
    for a in day:
        unitroot=c.MAIN/'attempts'/a['attempt_id'];rows=c.s.lines(unitroot/'REQUESTS.jsonl')
        assert len(rows)==91 and Counter(r['stage'] for r in rows)=={'formal':84,'warmup':7}
        grouped=defaultdict(dict)
        for r in rows:
            assert r['status']=='COMPLETE' and r['actual_date']=='2026-11-01'
            counts[r['stage']]+=1
            grouped[(r['stage'],r['input_id'])][r['arm']]=r
            for p in [r['raw_native_record'],*r['raw_vectors']]:
                c.s.payload(c.MAIN,p);payloads.append({'slot_id':r['slot_id'],**p})
        for group in grouped.values():
            assert len(group)==7
            for prefix in ('M','C'):
                for field in ('cycles','target_final_kv','draft_final_kv'):
                    assert group[prefix+'_PQ'][field]==group[prefix+'_QB'][field]
        for name in ('PROCESS.json','stdout.log','stderr.log'):
            dest=out/a['attempt_id']/name;dest.parent.mkdir(exist_ok=True)
            shutil.copyfile(unitroot/name,dest)
    assert counts=={'formal':336,'warmup':28}
    for family in c.s.FAMILIES:
        own=[a for a in day if a['family']==family]
        assert len(own)==2 and len({a['pid'] for a in own})==2
        start=min(c.s.utc(a['process_start_utc']) for a in own)
        previous=min(c.s.utc(a['process_start_utc']) for a in old if a['date_slot']==1 and a['family']==family)
        gaps[family]=(start-previous).total_seconds();assert gaps[family]>=72000
        per_family[family]={'formal':168,'warmup':14}
    gaps['daily_first']=(min(c.s.utc(a['process_start_utc']) for a in day)-min(c.s.utc(a['process_start_utc']) for a in old if a['date_slot']==1)).total_seconds()
    assert gaps['daily_first']>=72000
    local=c.s.read(c.MAIN/'LOCAL_PATHS.json')
    for family,identity in binding['families'].items():
        exe=Path(local[family]['executable']);build=exe.parent.parent
        assert c.sha(exe)==identity['executable_sha256']
        assert c.sha(build/'core/src/libllama.a')==identity['core_sha256']
        assert c.sha(build/'BUILD.json')==identity['build_receipt_sha256']
        assert {p.name for p in exe.parent.glob('*.dll')}==set(identity['numerical_modules'])
        for name,digest in identity['numerical_modules'].items():assert c.sha(exe.parent/name)==digest
    c.s.save_lines(out/'RETAINED_PAYLOADS.jsonl',payloads)
    c.save(out/'PREFLIGHT.json',c.s.read(c.REPO/'work/day2-preflight.json'))
    status={'status':'COMPLETE_DATE_AUDITED','date_slot':2,'actual_date':'2026-11-01','audit_utc':c.now().isoformat(),
      'calendar_dates':binding['calendar_dates'],'source_binding_commit':c.s.read(c.MAIN/'FREEZE_COMMIT.json')['commit'],
      'requests':364,'formal_measurements':336,'warmups':28,'per_family':per_family,
      'processes':[{k:a[k] for k in ('unit_id','pid','process_start_utc','process_end_utc','cleanup_verified')} for a in day],
      'first_session_gap_seconds':gaps,'historical_endpoints_match':True,'pq_qb_canonical_states_equal':True,
      'shared_audit_failures':[],'full_study_status':'COMPLETE','qualified_performance':audit['qualified_performance'],
      'qualification_requests_retained':196,'previous_main_requests_retained':924,'previous_requests_prefix_sha256':h.hexdigest(),
      'previous_attempt_receipts_unchanged':True,'frozen_source_design_calendar_exe_core_dlls_unchanged':True,
      'primary_requests_completed':1288,'technical_retry_requests':0,'llama_diagnostic_requests_retained':54,
      'new_llama_diagnostic_requests':0,'remaining_formal_measurements':0,'remaining_warmups':0,
      'next_unit':None,'next_shanghai_date':None,'raw_archival':'LOCAL_RETAINED_INCREMENT_PENDING',
      'requests_file':c.pin(c.MAIN,c.MAIN/'REQUESTS.jsonl'),'attempts_file':c.pin(c.MAIN,c.MAIN/'ATTEMPTS.json')}
    c.save(out/'DAY2_STATUS.json',status)
    print(json.dumps(status),flush=True)
