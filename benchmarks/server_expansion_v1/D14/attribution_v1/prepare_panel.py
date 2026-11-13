"""Freeze fresh same-round factorial or fixed-packed pair by time-only decision."""
from pathlib import Path
import argparse,datetime,sys

def main():
    p=argparse.ArgumentParser()
    for k in ('root','work','integration'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--panel',choices=('attribution','packed_pair'),required=True);p.add_argument('--source-commit',required=True);a=p.parse_args()
    sys.path.insert(0,str(a.integration));import integration_attribution as d
    d.load(a.root/'d14-runtime-02');read,save,need,sha=d.read,d.save,d.need,d.sha
    w=a.work;out=w/'panel-01';need(not out.exists(),'Fresh panel, never resume selected slots');q=read(w/'qualification-03/NATIVE_CHECKS_COMPLETE.json')
    need(q['passed'] and q['all_eight_controls'],'All four real D4 paths qualified against original14B R')
    cohort=read(a.root/'run-01/stage-04/authenticated-kit/samples/R2-INPUTS.json')['inputs'];primers=read(w/'inputs-01/PRIMERS.json')['inputs'];lookup={x['id']:x for x in cohort+primers}
    need(len(cohort)==16 and len(primers)==2 and len(lookup)==18,'Fixed original deployment roots and primers')
    study=read(Path(__file__).parent/'study.json');plan=d.shared.schedule(study,a.panel,[dict(root=x['id']) for x in cohort]);models=read(w/'inputs-01/MODELS.json')[d.FAMILY];structures=read(w/'MODEL_STRUCTURES.json')
    registered=study['panels'][a.panel].get('worker_order_rows')
    if registered is not None:
        by_id={x['worker_id']:x for x in plan['workers']}
        plan['workers']=[by_id[f'{study["id"]}-{a.panel}-s{session}-{arm}'] for session,row in enumerate(registered) for arm in row]
        plan.update(order_design='Prospective Williams4: every position and all12 directed within-round adjacencies exactly once',worker_order_rows=registered)
    rows=[]
    for s in range(4):rows.append([x['arm'] for x in plan['workers'] if x['session']==s])
    if a.panel=='attribution':
        need(all(sum(row[position]==arm for row in rows)==1 for position in range(4) for arm in plan['arms']),'Every arm appears once per position')
        pairs=[(a,b) for row in rows for a,b in zip(row,row[1:])];need(len(set(pairs))==len(pairs)==12,'Every within-round directed neighbor exactly once')
    else:need(rows==[['W_P_D4','L_P_D4'],['L_P_D4','W_P_D4']]*2,'Packed-pair AB/BA twice each')
    for worker in plan['workers']:
        core,cut,draft=d.ARMS[worker['arm']];need(draft,'D4 only attribution')
        keys=[x['id'] for x in primers]+worker['roots'];worker.update(id=worker['worker_id'],core=core,primers=keys[:2],job=worker['worker_id']+'.json')
        job=dict(models,residency='matched',draft=True,draft_width=4,lowering=cut,profile=False,capability_request=d.capability(models,structures,core,cut,True),inputs=[dict(name=f'request-{i:02d}',input=lookup[key],capture=False) for i,key in enumerate(keys)])
        save(out/worker['job'],job);worker['job_sha256']=sha(out/worker['job'])
    save(out/'PLAN.json',plan);save(out/'PROSPECTIVE_ORDER.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_commit=a.source_commit,plan_sha256=sha(out/'PLAN.json'),order_rows=rows,position_balanced=True,within_round_directed_neighbors='all12exactlyonce' if a.panel=='attribution' else 'ABandBAtwiceeach',between_round_edges_not_balanced=True,new_attribution_formal_outputs_seen=0,historical14B_results_already_exposed=True,no_historical_timing_pooling=True,selection_criterion='time only',qualification_summary_sha256=sha(w/'qualification-03/NATIVE_CHECKS_COMPLETE.json')))
    ledger=[__import__('json').loads(x) for x in (w/'ledger.jsonl').read_text().splitlines()];res=[x for x in ledger if x['event']=='RESERVE'];future=[d.host.reservation(read(out/x['job'])) for x in plan['workers']]
    req=sum(x['requests'] for x in res)+sum(x[0] for x in future);bounds=sum(x['rows'] for x in res)+sum(x[1] for x in future)
    need(req<=2560 and bounds<=12000000,'Whole future panel within unchanged new-study envelope')
    save(w/'PREPARED.json',dict(passed=True,source_commit=a.source_commit,panel=a.panel,plan_sha256=sha(out/'PLAN.json'),forecast_charged_plus_future_requests=req,forecast_charged_plus_future_reserved_rows=bounds,reserved_rows_are_bounds_not_physical_work=True,measurements=plan['measurements'],primers=plan['primers'],new_attribution_formal_outputs_seen=0,original_R_and_numerical_modules_unchanged=True))
    print('ATTRIBUTION_PROSPECTIVE_PLAN_FROZEN',a.panel,plan['measurements'],flush=True)
if __name__=='__main__':main()
