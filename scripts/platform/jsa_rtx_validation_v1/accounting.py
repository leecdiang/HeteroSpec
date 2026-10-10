"""Count full scientific requests, warmups and resident lifetimes from raw files."""
from common import *
from datetime import datetime
from collections import Counter

STAGES={'S_bridge':32,'S_formal':768,'new_core_bridge':16,'F_graph_proof':16,
        'E_engineering_Qwen':48,'E_engineering_SmolLM2':48,'F_discovery':504,
        'F_natural':2,'confirmation_Qwen':600,'confirmation_SmolLM2':1176}
def main():
    rows=[]
    for stage,planned in STAGES.items():
        root=LOCAL/'runs'/stage;records=[]
        for p in sorted(root.rglob('*.json')):
            a=read(p)
            if isinstance(a,dict) and 'response' in a and 'wall_ms' in a and ('slot' in a or ('case' in a and stage.startswith('E_engineering_'))):records.append((p,a))
        assert len(records)<=planned,(stage,len(records),planned)
        if stage.startswith('E_engineering_'):
            names=[a['case']['name'] for p,a in records];expected=[a['name'] for a in read(root/'PLAN.json')['cases']]
            assert len(names)==len(set(names)) and set(names)<=set(expected)
        warm=list(root.rglob('WARMUP.json'));lifetimes=[read(p) for p in root.rglob('LIFETIME.json')]
        starts=[read(p)['utc'] for p in root.rglob('COMMAND.json')];ends=[a['utc'] for a in lifetimes]
        ledger_name={'S_formal':'S','confirmation_Qwen':'Qwen','confirmation_SmolLM2':'SmolLM2'}.get(stage)
        statuses=dict(Counter(a['status'] for a in read(LOCAL/(ledger_name+'_SLOTS.json')).values())) if ledger_name else None
        assert ledger_name is None or (sum(statuses.values())==planned and statuses.get('COMPLETED',0)==len(records))
        rows.append({'stage':stage,'formal':ledger_name is not None,'planned_requests':planned,'completed_requests':len(records),'failed_or_missing':planned-len(records),'slot_statuses':statuses,'warmups':len(warm),'client_request_seconds_sum':sum(a['wall_ms']/1000 for p,a in records),'resident_process_lifetimes_seconds_sum':sum(a['seconds'] for a in lifetimes),'first_resident_command_utc':min(starts) if starts else None,'last_resident_teardown_utc':max(ends) if ends else None,'resident_span_seconds':(datetime.fromisoformat(max(ends))-datetime.fromisoformat(min(starts))).total_seconds() if starts and ends else None,'raw_records_sha256':{p.relative_to(LOCAL).as_posix():sha(p) for p,a in records}})
    full=sum(a['completed_requests'] for a in rows);warm=sum(a['warmups'] for a in rows)
    save(PUB/'EXECUTION_ACCOUNTING.json',{'status':'COMPLETE' if all(a['completed_requests']==a['planned_requests'] for a in rows) else 'INCOMPLETE','stages':rows,'formal_requests_unique':sum(a['completed_requests'] for a in rows if a['formal']),'nonformal_requests_unique':sum(a['completed_requests'] for a in rows if not a['formal']),'warmups':warm,'all_full_http_requests_including_warmups':full+warm,'diagnostic_auxiliary_decode_requests':read(PUB/'F_NATURAL_DIAGNOSTICS.json')['auxiliary_decodes'],'inside_E_fast_and_verify_decodes':'online work inside each full HTTP request, not extra external diagnostic requests','shared_F_E_matrix':'confirmation_SmolLM2 counted once','timing_scope':'client sum is measured scientific requests only; resident lifetimes include load/warmup/teardown and are not CUDA active-kernel time; resident spans include gaps/cooling. No active CUDA timing or energy was measured. Earlier preparation/failed builds are retained separately.','utc':now()})
    print('EXECUTION ACCOUNTING',full,warm,flush=True)
if __name__=='__main__':main()
