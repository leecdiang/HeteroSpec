"""Read-only phase coverage and actual persistent-worker cost aggregation."""
from host_rtx import *
from receipts import saved_costs

def main():
    assert (ROOT/'R2/COMPLETE.json').exists()
    workers=read(ROOT/'R2/WORKERS.json');records=read(ROOT/'R2/RECORDS.json');lookup={w['worker_id']:w for w in workers};panels={kind:dict(families={'Qwen':dict(roots=[],arms={})}) for kind in ('measurement','primer')};host={};signed=[]
    for record in records:
        w=lookup[record['worker_id']];arm=w['arm'];a=host.setdefault(arm,dict(workers=[],model_setup_s=0.,test_burst_wall_s=0.,worker_wall_s=0.,wrapper_wall_s=0.,first_any_result_s=[],first_test_result_s=[],peak_device_bytes=0))
        for key in ('model_setup_s','test_burst_wall_s','worker_wall_s','wrapper_wall_s'):a[key]+=record[key]
        a['workers'].append(record['worker_id']);a['first_any_result_s'].append(record['launch_to_first_result_s']);a['first_test_result_s'].append(record['launch_to_first_test_result_s']);a['peak_device_bytes']=max(a['peak_device_bytes'],record['peak_device_bytes'])
        for call in record['requests']:
            r=read(call['native_receipt']);kind=call['kind'];f=panels[kind]['families']['Qwen'];rows=f['arms'].setdefault(arm,dict(rows=[]))['rows']
            if call['root'] not in f['roots']:f['roots'].append(call['root'])
            row=dict(root=call['root'],session=w['session'],status='COMPLETE',service_s=r['service_seconds'],planning_s=r.get('planning_s'),output_copy_s=r.get('output_copy_s'),reset_s=r.get('setup_seconds'),teardown_s=r.get('teardown_seconds'),target_phases=r.get('target_phases'),draft_phases=r.get('draft_phases'),phase_measurement_status={'target_phases':{},'draft_phases':{}})
            executed={'target_phases':dict(PREFILL=True,ORDINARY=not r['draft_enabled'] and len(r['ids'])>1,VERIFY=r['draft_enabled'] and bool(r['cycles'])),'draft_phases':dict(PREFILL=r['draft_enabled'],DRAFT_SYNC=r['draft_enabled'] and bool(r['cycles']),PROPOSE=r['draft_enabled'] and bool(r['cycles']))}
            for role,phases in executed.items():
                for phase,ran in phases.items():
                    if not ran:row['phase_measurement_status'][role][phase]='NOT_EXECUTED'
                    elif phase in (row[role] or {}):row['phase_measurement_status'][role][phase]='MEASURED'
                    # An expected but absent clock stays unknown/null.
            components=[row[k] for k in ('planning_s','output_copy_s','reset_s','teardown_s')]
            phase_values=[(row[role] or {}).get(p) for role,ps in executed.items() for p,ran in ps.items() if ran]
            residual=None if any(v is None for v in components+phase_values) else row['service_s']-sum(components+phase_values)
            row['other_service_s']=residual if residual is not None and residual>=0 else None
            if residual is not None and residual<0:signed.append(dict(receipt=call['native_receipt'],derived_signed_residual_s=residual,not_clamped=True))
            rows.append(row)
    dest=ROOT/'R2'
    for kind,data in panels.items():
        p=dest/(kind.upper()+'-COST-INPUTS.json');put(p,data);put(dest/(kind.upper()+'-COST-COVERAGE.json'),saved_costs(p,expected_sessions=4))
    put(dest/'ACTUAL_HOST_COSTS.json',dict(arms=host,worker_count=len(records),signed_residuals=signed,scope='Actual markers/process observations, not setup/N. First-result clocks include startup and the indicated primers. Test burst starts at second-primer result and ends at last test result; worker completion includes original2s supervisor observation granularity. Wrapper includes offline integrity and after-process verification. Inclusive clocks overlap. Device memory is global2s-sampled observed peak, not per-process high-water. Other-service residual is calculated, not a separate measured clock.'))
    print('Complete R2 measured/primer coverage and actual host costs retained',flush=True)

if __name__=='__main__':main()
