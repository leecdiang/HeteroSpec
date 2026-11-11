"""Compact receipts and coverage-aware observed costs; performs no GPU work."""
from host_rtx import *
import sqlite3
DEST=HERE/'host_evidence'
def write(p,x):
    p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(x,indent=2),encoding='utf8');os.replace(tmp,p)
def main():
    for p in ROOT.glob('*.json'):
        if p.name in ('PARENT_SOURCE_BINDING.json','SOURCE_ADAPTATION.json','NATIVE_REVISION_2.json'):continue
        write(DEST/'host'/p.name,read(p))
    for p in ROOT.glob('*-QUALIFICATION.json'):write(DEST/'qualification'/p.name,read(p))
    for name in ('R1-STRUCT','R2'):
        for p in (ROOT/name).glob('*.json'):
            if p.name.endswith('.MODEL.json'):continue
            write(DEST/name/p.name,read(p))
    db=sqlite3.connect(ROOT/'ledger.sqlite');db.row_factory=sqlite3.Row;attempts=[dict(r) for r in db.execute('select * from attempts order by started')];db.close();rows=[];calls=[]
    for a in attempts:
        out=ROOT/'runs'/a['id'];entry=dict(ledger=a,path=str(out))
        for n,k in [('exit.json','host_exit'),('COMPLETE.json','completion'),('failure.json','failure')]:
            if (out/n).exists():entry[k]=read(out/n)
        meta=out/'native/result.json'
        if meta.exists():
            native=prior.native_fields(meta,['status','trajectories','token_rows','model_load_s','pool_setup_s','total_observed_API_calls','requests'])
            entry['native_observed']={k:v for k,v in native.items() if k!='requests'}
            for r in native.get('requests',[]):
                p=out/'native'/r['record'];raw=read(p)
                calls.append(dict(attempt=a['id'],name=r['name'],receipt=str(p),receipt_sha256=sha(p),service_s=raw.get('service_seconds'),append_s=raw.get('append_ms')/1000 if raw.get('append_ms') is not None else None,preparation_s=raw.get('preparation_s'),reset_s=raw.get('setup_seconds'),teardown_s=raw.get('teardown_seconds'),planning_s=raw.get('planning_s'),output_copy_s=raw.get('output_copy_s'),target_phases=raw.get('target_phases'),draft_phases=raw.get('draft_phases'),capture=raw.get('capture'),draft_enabled=raw.get('draft_enabled'),graphs_built=raw.get('graphs_built'),graphs_reused=raw.get('graphs_reused')))
        rows.append(entry)
    reserved={k:sum(a[k] for a in attempts) for k in LIMITS};complete={k:sum(r.get('completion',{}).get('actual_work',{}).get(k,0) for r in rows) for k in LIMITS}
    measured=[r['service_s'] for r in calls if r['service_s'] is not None]
    write(DEST/'UNIFIED_COSTS.json',dict(as_of_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),limits=LIMITS,reserved=reserved,confirmed_complete=complete,attempts=rows,request_components=calls,request_service=dict(total_s=sum(measured) if len(measured)==complete['requests'] else None,observed_sum_s=sum(measured),measured_requests=len(measured),present_request_receipts=len(calls),expected_logical_requests=complete['requests']),host_attempt_wall_s=sum(r.get('host_exit',{}).get('seconds',0) for r in rows),scope='Append/preparation are not whole service. Forced diagnostic requests have complete host attempt wall but no separate service clock. Missing components stay null; parent/child clocks are never added twice. Failed reservations are never refunded.',unresolved_attempts=[r['ledger']['id'] for r in rows if 'completion' not in r],inherited_costs='INHERITED_REFERENCE_COSTS.json; parent ledgers and payload identities retained, no historical timing pooled'))
    commands=[]
    for base in (ROOT,Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/phase192-clean-v1')):
        for p in base.rglob('*.json'):
            if any(x in p.relative_to(base).parts for x in ('source','snapshots','native-v1','native-v2','compiler-cache','runs','reference-payloads','freezes')):continue
            try:r=read(p)
            except (ValueError,OSError):continue
            if isinstance(r,dict) and all(k in r for k in ('argv','code','seconds')):commands.append(dict(path=str(p),sha256=sha(p),**r))
    transport={}
    for name in ('ARTIFACT_DELIVERY.json','ARTIFACT_READBACK.json'):
        if (ROOT/name).exists():transport[name]=read(ROOT/name)
    write(DEST/'ENGINEERING_COSTS.json',dict(commands=commands,recorded_command_wall_s=sum(r['seconds'] for r in commands),unmetered_initial_CPU_preparation_wall_s=None,offline_reader_failure_retained='host/QUALIFICATION_READER_FAILURE-1.json',complete_total_engineering_wall_s=None,transport=transport,clock_scope='No missing clock is zero. Build/validation/transfer clocks are separate from and may overlap native wall.'))
    print('Collected',len(attempts),'native attempts;',reserved,'reserved;',complete,'confirmed',flush=True)
if __name__=='__main__':main()
