"""Compact native evidence and complete observed/reserved costs; no GPU calls."""
from host import *
import sqlite3,datetime
DEST=HERE/'host_evidence'

def write(p,x):
    p.parent.mkdir(parents=True,exist_ok=True);temporary=p.with_suffix(p.suffix+'.tmp');temporary.write_text(json.dumps(x,indent=2),encoding='utf8');os.replace(temporary,p)

def collect():
    for p in ROOT.glob('*.json'):
        if not p.name.startswith('STORAGE-'):write(DEST/'host'/p.name,json.loads(p.read_bytes()))
    for name in ['SIMPLE','LOCAL','R-Qwen','R-Smol','profiles','profiles-final']:
        base=ROOT/name
        for p in base.rglob('*.json'):
            if any(x in p.relative_to(base).parts for x in ('source','core')):continue
            try:r=json.loads(p.read_bytes())
            except (ValueError,OSError):continue
            if p.name in ('BUILD.json','CORE_BUILD.json','PROFILE_SOURCE_BINDING.json','SOURCE_MANIFEST.json') or isinstance(r,dict) and all(k in r for k in ('argv','code','seconds')):write(DEST/'build'/name/p.relative_to(base),r)
    db=sqlite3.connect(ROOT/'ledger.sqlite');db.row_factory=sqlite3.Row;attempts=[dict(r) for r in db.execute('select * from attempts order by started')];db.close();rows=[];services=[]
    for a in attempts:
        matches=[p/a['id'] for p in [ROOT/'runs',Path('E:/rtx188/runs')] if (p/a['id']).exists()];assert len(matches)==1;out=matches[0]
        record=dict(ledger=a,path=str(out));exit=out/'exit.json'
        if exit.exists():record['host_exit']=json.loads(exit.read_bytes())
        done=out/'COMPLETE.json'
        if done.exists():record['actual_work']=json.loads(done.read_bytes())['actual_work']
        result=out/'native/result.json'
        if result.exists():
            native=native_fields(result,['model_load_s','pool_setup_s','model_load_seconds','pool_setup_seconds','resident_initial_plan_compile_s','total_observed_API_calls','model_structure','trajectories','token_rows','requests']);record['native_setup']={k:v for k,v in native.items() if k in ('model_load_s','pool_setup_s','model_load_seconds','pool_setup_seconds','resident_initial_plan_compile_s','total_observed_API_calls','model_structure')}
            if 'actual_work' not in record:record['incomplete_native_lower_bound']={k:native.get(field,0) for k,field in [('requests','trajectories'),('token_rows','token_rows')]}
            for item in native.get('requests',[]):
                file=out/'native'/item['record'];r=json.loads(file.read_bytes());name=item.get('name',item.get('slot_id',file.stem));kind='storage-recovery-history' if name.startswith('recovery-') else name.rsplit('-',1)[-1] if '-' in name else 'historical-bridge'
                s=dict(attempt=a['id'],slot=name,kind=kind,service_s=r.get('service_seconds'),request_s=r.get('request_seconds'),reset_setup_s=r.get('setup_seconds'),target_phases=r.get('target_phases'),draft_phases=r.get('draft_phases'),planning_s=r.get('planning_s'),output_copy_s=r.get('output_copy_s'),first_call_plan_s=r.get('first_call_plan_s'),output_length=len(r['ids']),stop_reason=r['stop_reason'],observed_API_calls=r.get('observed_API_calls_within_service'),native_record=str(file));services.append(s)
        failure=out/'failure.json'
        if failure.exists():record['failure']=json.loads(failure.read_bytes())
        rows.append(record)
    costs=dict(as_of_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),limits=LIMITS,reserved={k:sum(a[k] for a in attempts) for k in LIMITS},confirmed_complete={k:sum(r.get('actual_work',{}).get(k,0) for r in rows) for k in LIMITS},unresolved_failed_attempts=[r['ledger']['id'] for r in rows if 'actual_work' not in r],host_attempt_wall_s=sum(r.get('host_exit',{}).get('seconds',0) for r in rows),recorded_request_service_s=sum(r['service_s'] or 0 for r in services),attempts=rows,services=services,scope='All reservations retained, including failures. Setup, service and phase components are nested in host attempt wall, never additive to it. Teacher/controlled diagnostic service without a separate clock is unknown as a component; its complete attempt wall is retained. Historical PR186 bank costs are inherited resources, not relabeled as new GPU work or free production work.',historical_reference_costs='Parent PR186 host_evidence/UNIFIED_COSTS.json and original frozen raw-reference receipts',unknown_component_times_are_not_zero=True)
    costs['actual_lower_bound_including_failed_native']={k:sum(r.get('actual_work',r.get('incomplete_native_lower_bound',{})).get(k,0) for r in rows) for k in LIMITS}
    write(DEST/'UNIFIED_COSTS.json',costs)
    for p in (ROOT/'confirmation').glob('*.json'):
        if p.name.startswith('COORDINATOR-') or p.name.endswith('.MODEL.json') or p.name in ['SOURCE_SELECTION.json','Qwen-PANEL.json','Smol-PANEL.json','PANELS.json','PLAN.json','SCHEDULE.json','FREEZE.json','PUBLISHED.json','COMPLETE.json','CLOSED_NUMERICAL_FAILURE.json','RESULTS.json']:
            write(DEST/'confirmation'/p.name,json.loads(p.read_bytes()))
    commands=[]
    for p in ROOT.rglob('*.json'):
        if any(x in p.relative_to(ROOT).parts for x in ('source','core','runs','evidence-cas','compiler-cache')):continue
        try:r=json.loads(p.read_bytes())
        except (ValueError,OSError):continue
        if isinstance(r,dict) and all(k in r for k in ('argv','code','seconds')):commands.append(dict(path=str(p),sha256=sha(p),**r))
    storage_costs=[]
    for p in [ROOT/'COLD_ARCHIVE_RECEIPT.json',ROOT/'COLD_ARCHIVE_RELOCATION.json',*ROOT.glob('smol-engineering-*.json'),*ROOT.glob('FINAL_MATRIX_STORAGE-*.json')]:
        if p.exists():storage_costs.append(dict(path=str(p),**json.loads(p.read_bytes())))
    write(DEST/'ENGINEERING_COSTS.json',dict(recorded_command_wall_s=sum(r['seconds'] for r in commands),commands=commands,lossless_storage_recovery=storage_costs,other_engineering_time_not_assumed_zero=True))
    print('Collected',len(attempts),'attempts;',costs['reserved'],'reserved;',len(services),'service records',flush=True)

if __name__=='__main__':collect()
