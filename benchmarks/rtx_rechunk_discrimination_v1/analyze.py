"""Read-only analysis of every frozen root/session; no GPU access."""
from audit import *
import math,statistics,itertools
ARMS=('QB','WB-cut','WB-rechunk')
PHASES=('lookup_import_ready_s','append_execution_s','continuation_s','service_s')
def compute(get):
    panel=get('coverage.json')['selected'];records=[];paired=[]
    for s,i,a in itertools.product(range(2),range(8),ARMS):
        r=get(f'science-session-{s}/{i:02}/{a}/measure/receipt.json')
        records.append(dict(session=s,index=i,root_id=panel[i]['root_id'],arm=a,**{k:r[k] for k in PHASES}))
    for numerator,denominator in [('WB-rechunk','QB'),('WB-cut','QB'),('WB-cut','WB-rechunk')]:
        for phase in PHASES:
            roots=[]
            for i in range(8):
                sessions=[]
                for s in range(2):
                    aa=next(x for x in records if (x['session'],x['index'],x['arm'])==(s,i,numerator))[phase]
                    bb=next(x for x in records if (x['session'],x['index'],x['arm'])==(s,i,denominator))[phase]
                    sessions.append(dict(session=s,numerator_s=aa,denominator_s=bb,ratio=aa/bb,difference_s=aa-bb))
                roots.append(dict(index=i,root_id=panel[i]['root_id'],sessions=sessions,geometric_ratio=math.exp(statistics.mean(math.log(x['ratio']) for x in sessions)),mean_difference_s=statistics.mean(x['difference_s'] for x in sessions)))
            paired.append(dict(numerator=numerator,denominator=denominator,phase=phase,geometric_ratio=math.exp(statistics.mean(math.log(x['geometric_ratio']) for x in roots)),mean_difference_s=statistics.mean(x['mean_difference_s'] for x in roots),roots=roots,session_geometric_ratios=[math.exp(statistics.mean(math.log(x['sessions'][s]['ratio']) for x in roots)) for s in range(2)]))
    return dict(scope='Descriptive conditional n=8; equal root/session weight; ratio>1 favors denominator; positive difference means numerator slower; no population inference',records=records,paired=paired)

def main():
    assert read(ROOT/'COMPLETE.json')['passed']
    result=compute(lambda p:read(ROOT/p));put(ROOT/'ANALYSIS.json',result)
    jobs=[]
    for p in sorted(ROOT.glob('*/launch.json')):
        launch=read(p);receipts=list(p.parent.rglob('receipt.json'));rs=[read(r) for r in receipts]
        jobs.append(dict(job=p.parent.name,stage=launch['stage'],reserved=launch['requests'],completed=len(rs),exit=read(p.parent/'exit.json') if (p.parent/'exit.json').exists() else None,model_load_s=read(p.parent/'load.json')['seconds'],context_init_s=read(p.parent/'context_init.json')['seconds'] if (p.parent/'context_init.json').exists() else None,service_sum_s=sum(r['service_s'] for r in rs),observer_io_sum_s=sum(r['observer_io_s'] for r in rs),reference_snapshot_producer_s=sum(r['producer_or_file_read_s'] for r in rs if r['arm']=='R')))
    put(ROOT/'COSTS.json',dict(jobs=jobs,reserved=sum(j['reserved'] for j in jobs),completed=sum(j['completed'] for j in jobs),scientific_reserved=sum(j['reserved'] for j in jobs if j['stage']=='scientific'),host_native_wall_s=sum(j['exit']['elapsed_s'] for j in jobs),service_sum_s=sum(j['service_sum_s'] for j in jobs),model_load_sum_s=sum(j['model_load_s'] for j in jobs),build_seconds=sum(read(p)['seconds'] for p in (ROOT/'candidate01').glob('build-*.json')),context_note='Original R and inherited old engineering worker do not separately record context initialization; their setup remains in unmodified host wall. New candidate records it separately.',cpu_cost_limit='Saved-data census/exposure audit and interactive preparation were not separately wall-metered; native launch wall, compile/link wall, all request/service/setup/snapshot costs and transport receipts are retained. No calibration was performed.',failures=[str(p.relative_to(ROOT)) for p in ROOT.rglob('*failure*.json')],inherited_PR174=dict(reserved=2026,completed=1957,uncompleted_reserved=69,calibration_host_wall_s=2038.781179),new_calibration_requests=0,auto_training_requests=0))
    for x in result['paired']:
        if x['phase'] in ('append_execution_s','service_s'):print(x['numerator'],x['denominator'],x['phase'],x['geometric_ratio'],x['mean_difference_s'],x['session_geometric_ratios'])
if __name__=='__main__':main()
