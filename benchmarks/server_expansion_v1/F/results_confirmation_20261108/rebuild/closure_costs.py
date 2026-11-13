"""Post-run cost observer; preserve unknowns and every retained failure epoch."""
from pathlib import Path
import argparse,hashlib,json,datetime,math

def read(p):return json.loads(p.read_text())
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def save(p,x):
    with p.open('x') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();r=a.root
    assert read(r/'f-confirmation-audit-03/STATUS.json')['status']=='F_CONFIRMATION_COMPLETE_AND_ARCHIVED','Only after Llama closes'
    assert read(r/'d14-attribution-audit-01/STATUS.json')['status']=='COMPLETE_AND_ARCHIVED','Only after attribution closes'
    result=dict(observer_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),model_forwards=0,native_or_performance_reexecution=False,clock_types_overlap_do_not_add=True,reserved_rows_are_accounting_bounds_not_actual_physical_work=True,lanes={})
    for label,name in [('Llama','f-run-01'),('D14_original','d14-run-01'),('D14_attribution','d14-attribution-run-01')]:
        w=r/name;lp=w/'ledger.jsonl'
        if not lp.exists():continue
        ledger=[json.loads(x) for x in lp.read_text().splitlines()];reservations=[x for x in ledger if x.get('event')=='RESERVE'];phases={};hosts=[]
        for row in reservations:
            phase=phases.setdefault(row['phase'],dict(reserved_workers=0,reserved_requests=0,reserved_row_bounds=0,host_complete=0,host_failed=0,host_missing=0,worker_wall_known_s=0,worker_wall_unknown_count=0))
            phase['reserved_workers']+=1;phase['reserved_requests']+=row['requests'];phase['reserved_row_bounds']+=row['rows'];hp=Path(row['out'])/'HOST.json'
            if not hp.exists():phase['host_missing']+=1;continue
            h=read(hp);phase['host_complete' if h['status']=='COMPLETE' else 'host_failed']+=1
            if type(h.get('worker_wall_s')) in (int,float):phase['worker_wall_known_s']+=h['worker_wall_s']
            else:phase['worker_wall_unknown_count']+=1
            hosts.append(dict(expected_native_capability_negative='capability-negatives-' in str(Path(row['out']).relative_to(r)),logical_out=str(Path(row['out']).relative_to(r)),phase=row['phase'],status=h['status'],worker_wall_s=h.get('worker_wall_s'),wrapper_wall_s=h.get('wrapper_wall_s'),host_receipt_sha256=sha(hp)))
        lane=dict(ledger_sha256=sha(lp),reserved_requests=sum(x['requests'] for x in reservations),reserved_row_bounds=sum(x['rows'] for x in reservations),reserved_workers=len(reservations),phases=phases,all_actual_host_receipts=hosts)
        panel=w/'panel-01';checked=panel/'CHECKED.json'
        if checked.exists():
            plan=read(panel/'PLAN.json');workers={x['id']:x for x in plan['workers']};by_arm={};records=read(checked)
            for rec in records:
                worker=workers[rec['id']];arm=by_arm.setdefault(worker['arm'],dict(measurement_s=0.,primer_s=0.,measurements=0,primers=0,workers=0,clock_sums={},clock_measured_counts={},maximum_sampled_total_minus_free_bytes=None,minimum_sampled_free_bytes=None))
                arm['workers']+=1
                for i,c in enumerate(rec['requests']):
                    k='primer' if i<2 else 'measurement';arm[k+'_s']+=c['service_s'];arm['primers' if i<2 else 'measurements']+=1
                clocks=rec['actual_host_clocks']
                for k,v in clocks.items():
                    if type(v) in (int,float) and (k.endswith('_s') or k.endswith('_seconds')):
                        arm['clock_sums'][k]=arm['clock_sums'].get(k,0)+v;arm['clock_measured_counts'][k]=arm['clock_measured_counts'].get(k,0)+1
                for k,fn in [('maximum_sampled_total_minus_free_bytes',max),('minimum_sampled_free_bytes',min)]:
                    if clocks.get(k) is not None:arm[k]=clocks[k] if arm[k] is None else fn(arm[k],clocks[k])
            if (panel/'RESULTS.json').exists():
                totals=read(panel/'RESULTS.json')['totals']
                assert set(totals)==set(by_arm)
                for arm,total in totals.items():assert math.isclose(total,by_arm[arm]['measurement_s'],rel_tol=1e-12,abs_tol=1e-10)
            lane['formal']=dict(plan_sha256=sha(panel/'PLAN.json'),checked_sha256=sha(checked),actual_slot_status=read(panel/'ALL_SLOT_STATUS.json'),arms=by_arm,memory_scope='Selected-device total-minus-free includes reserved/unavailable;2s sampled lower bound on peak, not NVML memory.used or per-process high water',cold_clock_scope='Sums of independent native workers, each including model load, two primers and all formal requests; overlap with service/model-load/adapter clocks. First-result clocks refer to a completed request, not TTFT.')
        result['lanes'][label]=lane
    preps=[]
    for epoch in (1,2,3):
        audit=r/f'f-confirmation-audit-{epoch:02d}';start=audit/'prepare-START.json';end=audit/'prepare-EXIT.json'
        if not start.exists() or not end.exists():continue
        token=r/'f-run-01'/f'preparation-formal-tokenizer-{epoch:02d}';costs=[]
        if (token/'HELPER_COSTS.json').exists():costs+=read(token/'HELPER_COSTS.json')
        costs += [read(token/(role+'-COST.json')) for role in ('target','draft') if (token/(role+'-COST.json')).exists()]
        preps.append(dict(epoch=epoch,returncode=read(end)['returncode'],preparation_inclusive_s=read(end)['elapsed_s']-read(start)['elapsed_s'],helper_costs=costs,unmeasured_helper_roles=[x for x in ('target','draft') if x not in {y['role'] for y in costs}],model_forwards=0,context_creations=0,start_sha256=sha(start),exit_sha256=sha(end),failed_preparation_is_not_formal_measurement=True))
    result['Llama_retained_preparations']=preps
    byte=r/'f-tokenizer-byte-audit-03/CHECKED.json'
    if byte.exists():result['Llama_byte_regression']=dict(check_sha256=sha(byte),queries=read(byte)['queries'],helper_costs=read(byte)['helper_costs'],wall_s=read(byte)['wall_s'],model_forwards=0,context_creations=0)
    result['archive_clocks']={}
    for name in ('f-public-export-02','d14-public-export-02','f-public-export-05','d14-attribution-export-01'):
        path=r/name/'LOCAL_READBACK.json'
        if path.exists():result['archive_clocks'][name]=dict(receipt_sha256=sha(path),**read(path))
    result['attribution_steps']={}
    audit=r/'d14-attribution-audit-01'
    for label in ('qualification','prepare-panel','formal','archive'):
        start=audit/(label+'-START.json');end=audit/(label+'-EXIT.json')
        if start.exists() and end.exists():result['attribution_steps'][label]=dict(returncode=read(end)['returncode'],inclusive_s=read(end)['elapsed_s']-read(start)['elapsed_s'],start_sha256=sha(start),exit_sha256=sha(end))
    build=r/'f-vocabulary-build-03';result['vocabulary_observer_build']=dict(build_sha256=sha(build/'BUILD.json'),executable_sha256=read(build/'BUILD.json')['executable_sha256'],numeric_or_R_build_changed=False,phases={})
    for label in ('compile','link'):
        path=build/label/'command.json';j=read(path)
        result['vocabulary_observer_build']['phases'][label]=dict(receipt_sha256=sha(path),measured_clock_fields={k:v for k,v in j.items() if k in ('wall_s','elapsed_s','seconds','duration_s')},inclusive_build_wall_s=None,clock_coverage='Only recorded fields reported; no reconstruction from file timestamps')
    save(a.out,result);print('CLOSURE_COSTS_OBSERVED_NO_REEXECUTION',flush=True)
if __name__=='__main__':main()
