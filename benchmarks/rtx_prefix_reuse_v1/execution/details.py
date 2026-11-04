"""Read-only descriptive contrasts and complete attempted-slot accounting."""
from analyze import *
from datetime import datetime,timezone

def main():
    panel=read(ROOT/'common-panel.json');policy=read(ROOT/'COMMON_POLICY.json')
    result=read(ROOT/'analysis.json');rows=read(ROOT/'results.json')['records']
    measured={(r['id'],r['session'],r['arm']):r for r in rows if r['kind']=='measure'}
    def geo(v):return math.exp(statistics.mean(map(math.log,v)))
    def ratio(a,b,field='seconds'):
        byroot=[]
        for x in panel['test']:
            rs=[measured[x['id'],s,a][field]/measured[x['id'],s,b][field] for s in range(4)]
            byroot.append(dict(id=x['id'],root_id=x['root_id'],ratio=geo(rs)))
        return dict(numerator=a,denominator=b,geometric_ratio=geo([x['ratio'] for x in byroot]),root_rows=byroot,session_ratios=[geo([measured[x['id'],s,a][field]/measured[x['id'],s,b][field] for x in panel['test']]) for s in range(4)],inference='descriptive; no extra hypothesis test')
    summaries={};ids={r['id']:i for i,r in enumerate(panel['test'])}
    for x in measured.values():
        p=ROOT/f"main-cost-s{x['session']}/i{ids[x['id']]:02}/{x['arm']}/measure/receipt.json"
        r=read(p);x['append_from_receipt_s']=r['append_from_receipt_s'];x['import_s']=r['import_s'];x['state_bytes']=r['state_bytes']
    for arm in study.ARMS:
        v=[r for r in measured.values() if r['arm']==arm]
        summaries[arm]={f:dict(mean=statistics.mean(x[f] for x in v),median=statistics.median(x[f] for x in v),geomean=geo([x[f] for x in v])) for f in ('seconds','append_from_receipt_s','import_s','state_bytes')}
    entries=[];allreceipts=[]
    for path in sorted(ROOT.glob('*/launch.json')):
        d=path.parent;launch=read(path);inp=read(d/'input.json');units=inp.get('units',[]);slots=[]
        for u in units:
            receipt=d/u['id']/'receipt.json'
            slots.append(dict(id=u['id'],completed=receipt.exists(),state_mode='import' if 'state' in u else 'producer',head=u['head']))
            if receipt.exists():allreceipts.append((d.name,u,read(receipt)))
        entries.append(dict(path=d.name,reserved=launch['requests'],completed=sum(x['completed'] for x in slots),incomplete=sum(not x['completed'] for x in slots),slots=slots,exit=read(d/'exit.json') if (d/'exit.json').exists() else None,failure=read(d/'failure.json') if (d/'failure.json').exists() else None))
    best=min(study.FIXED,key=lambda a:summaries[a]['seconds']['geomean'])
    saving=statistics.mean(measured[x['id'],s,best]['seconds']-measured[x['id'],s,'AUTO']['seconds'] for x in panel['test'] for s in range(4))
    # Paired root resampling preserves all four sessions. Descriptive 95% CI
    # for arithmetic service saving is separate from the primary family CI.
    roots=[statistics.mean(measured[x['id'],s,best]['seconds']-measured[x['id'],s,'AUTO']['seconds'] for s in range(4)) for x in panel['test']]
    import random
    rng=random.Random(20261104);boot=[statistics.mean(roots[rng.randrange(32)] for _ in range(32)) for _ in range(10000)]
    cal=policy['calibration_total_seconds'];ci=[study.quantile(boot,.025),study.quantile(boot,.975)]
    aligned={}
    for a in study.FIXED:
        rr=[read(ROOT/f'aligned-cost-s{s}/i{i:02}/{a}/measure/receipt.json') for s in range(2) for i in range(8)]
        aligned[a]=dict(measurements=len(rr),mean_service_seconds=statistics.mean(x['service_s'] for x in rr),geomean_service_seconds=geo([x['service_s'] for x in rr]))
    out=dict(utc=datetime.now(timezone.utc).isoformat(),fixed_service_contrasts=[ratio('WB-cut','QB'),ratio('WB-rechunk','QB')],descriptive_append_contrasts=[ratio(a,'AUTO','append_from_receipt_s') for a in study.FIXED],phase_summaries=summaries,phase_semantics='Append interval includes request receipt, file read/index/reset/lookup/import and append. Import interval is cumulative from receipt, not an additive isolated phase. No phase subtraction or kernel-cost attribution.',break_even=dict(fastest_fixed_by_geomean=best,mean_service_saving_seconds=saving,secondary_paired_root95_saving_interval=ci,calibration_seconds=cal,point_requests=cal/saving if saving>0 else None,interval_requests=[cal/ci[1],cal/ci[0]] if ci[0]>0 else None,unbounded_or_no_positive_saving=ci[0]<=0,observed_main_measured_AUTO_requests=128,observed_main_measured_requests_per_root_per_arm=4,postselection_descriptive=True),aligned_control=aligned,slot_accounting=entries,total_reserved=sum(x['reserved'] for x in entries),total_completed=sum(x['completed'] for x in entries),total_reserved_without_receipt=sum(x['incomplete'] for x in entries),observed_trace=dict(completed_service_seconds=sum(r['service_s'] for _,u,r in allreceipts),completed_prefix_producer_seconds=sum(r['producer_or_file_read_s'] for _,u,r in allreceipts if 'state' not in u and u['head']>0),producer_service_overlap='For positive-head producer requests, producer and service windows are disjoint. Empty-prefix producer work is already inside service and not added.',all_completed_model_load_seconds=sum(read(p)['seconds'] for p in ROOT.glob('*/load.json')),completed_import_requests=sum('state' in u for _,u,r in allreceipts),completed_producer_requests=sum('state' not in u for _,u,r in allreceipts),main_cache_hit_fraction=1.0,main_import_bytes=sum(read(ROOT/f"main-cost-s{r['session']}/i{ids[r['id']]:02}/{r['arm']}/{r['kind']}/receipt.json")['state_bytes'] for r in rows),service_diagnostics_include_heavy_observer_io=True,unfinished_process_time='Retained launch/failure/interruption receipts and full campaign wall windows; absent receipts are not treated as zero cost.'),unmeasured=['kernel mask/join duration','native graph reuse hit counters','production request distribution','cross-date variability'])
    put(ROOT/'DETAILS.json',out);print(json.dumps({k:out[k] for k in ('total_reserved','total_completed','total_reserved_without_receipt','break_even')},indent=2))
if __name__=='__main__':main()
