"""Offline full-panel reconstruction. Missing/failed/invalid coordinates are retained."""
import itertools
import pathlib
from panel_common import HERE,RUN,MODES,STAGES,load,save,need,sha,modules
from controller import events
from native_audit import audit_raw,audit_lifecycle
from analyzer import analyze_files,compare
from run_panel import load_reference

def reconstruct(run=RUN):
    plan=load(HERE/'PLAN.json');wire=load(HERE/'WIRES.json');inputs={x['id']:x for x in load(HERE/'INPUTS.json')}
    expected=load(HERE/'EXPECTED_GRAPHS.json');records=[];good={};lives={};cache={};owned=0.;calls=0;started=[];inventory_errors=[]
    f0=load(HERE/'F0.json') if (HERE/'F0.json').exists() else None
    ledger=events(run/'LEDGER.jsonl',partial=True) if (run/'LEDGER.jsonl').exists() else []
    attempts=[x['slot']['id'] for x in ledger if x['event']=='ATTEMPT'];attempt_set=set(attempts)
    for slot,w in zip(plan['slots'],wire):
        folder=run/slot['id'];record=dict(slot=slot,status='UNSTARTED')
        if folder.exists() or slot['id'] in attempt_set:
            started.append(slot['id']);record['status']='FAILED_OR_INVALID'
            try:
                raw=events(folder/'raw.jsonl',partial=True);calls+=sum(e['event']=='GRAPH_START' for e in raw)
                life=load(folder/'LIFECYCLE.json');lives[slot['id']]=life;owned_before=owned;owned+=life['owned_wall_s']
                need(raw==events(folder/'raw.jsonl'),'completed raw must parse in full')
                request=load(folder/'REQUEST.wire')
                need(sha(folder/'REQUEST.wire')==w['sha256'] and request==load(HERE/w['path']),'exact planned wire')
                need(f0 is not None,'frozen F0 required for native reconstruction')
                record['lifecycle_audit']=audit_lifecycle(life,raw,f0,owned_before)
                need(slot['kind']=='census' or records[0]['status']=='COMPLETE_AUDITED','complete census before graph')
                need(life['request_sha256']==sha(folder/'REQUEST.wire') and life['raw_sha256']==sha(folder/'raw.jsonl'),'lifecycle byte identity')
                audit=audit_raw(raw,request,life['pid'],expected)
                record['native_audit']=audit
                if slot['kind']=='graph':
                    item=inputs[slot['input_id']];need(sha(item['path'])==item['sha256'],'input identity')
                    if item['id'] not in cache:cache[item['id']]=load_reference(item['id'])
                    analysis,vectors=analyze_files(request,audit['graph'],folder,pathlib.Path(item['path']).read_bytes(),cache[item['id']])
                    record['analysis']=analysis;good[slot['input_id'],slot['mode'],slot['repeat']]=vectors
                record['status']='COMPLETE_AUDITED'
            except Exception as e:record['error']=str(e)
        records.append(record)
    relations=[];control_failures=[]
    for item in inputs.values():
        ident=item['id'];q=item['cell']['geometry']['q']
        for mode in MODES:
            left,right=(ident,mode,0),(ident,mode,1)
            if left in good and right in good:
                a=next(s for s in plan['slots'] if s.get('input_id')==ident and s.get('mode')==mode and s.get('repeat')==0)
                b=next(s for s in plan['slots'] if s.get('input_id')==ident and s.get('mode')==mode and s.get('repeat')==1)
                la,lb=lives[a['id']],lives[b['id']]
                independent=(la['pid'],la['creation_FILETIME'])!=(lb['pid'],lb['creation_FILETIME'])
                relation=compare(good[left],good[right]);relations.append(dict(kind='INDEPENDENT_REPEAT',input=ident,mode=mode,independent=independent,relation=relation))
                if not independent or not relation['all_stages_bitwise_equal']:control_failures.append(dict(input=ident,mode=mode,reason='REPEAT_CONTROL'))
        for repeat in (0,1):
            for left,right in itertools.combinations(MODES,2):
                keys=(ident,left,repeat),(ident,right,repeat)
                if all(k in good for k in keys):
                    relation=compare(good[keys[0]],good[keys[1]])
                    relations.append(dict(kind='CROSS_REPRESENTATION',input=ident,q=q,left=left,right=right,repeat=repeat,relation=relation))
                    if q==1 and not relation['all_stages_bitwise_equal']:control_failures.append(dict(input=ident,left=left,right=right,reason='Q1_COMMON_PATH'))
    if (run/'LEDGER.jsonl').exists():
        if not (attempts==[s['id'] for s in plan['slots'][:len(attempts)]] and len(attempts)==len(set(attempts))):inventory_errors.append('attempts are not ordered non-repeated prefix')
        if set(attempts)!=set(started):inventory_errors.append('ledger and actual folders disagree')
    elif started:inventory_errors.append('missing attempt ledger')
    all_complete=all(r['status']=='COMPLETE_AUDITED' for r in records) and not control_failures and not inventory_errors
    return dict(run_id=plan['run_id'],status='COMPLETE_BOUNDED_NUMERICAL_PANEL' if all_complete else 'INCOMPLETE_OR_UNSTARTED',
        planned_hosts=161,planned_graph_calls=160,attempts=len(started),observed_graph_calls=calls,owned_wall_s=owned,
        missing_lifecycles=[s for s in started if s not in lives],owned_time_complete=all(s in lives for s in started),
        records=records,unstarted=[r['slot']['id'] for r in records if r['status']=='UNSTARTED'],
        failed_or_invalid=[r['slot']['id'] for r in records if r['status']=='FAILED_OR_INVALID'],control_failures=control_failures,
        inventory_errors=inventory_errors,relations=relations,full_domain_execution_inventory_complete=all_complete,numerical_qualification='No scalar tolerance-based PASS or automatic S2/S3 qualification',
        ordinary_finite_q_gt1_differences='Retained without tolerance selection; do not invalidate merely for FP64 rounding',
        S2_S3='NOT_ADMITTED',end_to_end_speedup=None)

if __name__=='__main__':
    need(RUN.exists(),'new panel has not started; no dynamic reconstruction data')
    save(RUN/'INDEPENDENT_RECONSTRUCTION.json',reconstruct())
