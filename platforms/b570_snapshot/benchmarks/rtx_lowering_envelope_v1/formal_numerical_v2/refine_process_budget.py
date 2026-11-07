"""CPU-measured console helper accounting; retain original GPU14 launch flags."""
from common import V,load,save
def main():
    b=load(V/'BUDGET.json');save(V/'PRE_HELPER_ACCOUNTING_BUDGET.json',b)
    b['counts']['explicit_controlled_launches']=1444;b['counts']['system_console_helper_processes_cap']=1442;b['counts']['controlled_process_starts']=2886
    b['limits']['job_active_process_limit']=2
    b['stages']['census'].update(explicit_controlled_launches=3,system_console_helpers_cap=2,controlled_starts=5,owned_bound_seconds=1800)
    b['stages']['numerical'].update(explicit_controlled_launches=1441,system_console_helpers_cap=1440,controlled_starts=2881,wall_seconds=1800,owned_bound_seconds=5400)
    nodes=[n for r in load(V/'CPU_GRAPH_EXPECTED.json') for n in r['nodes']]
    nonmeta=2*sum(not n['metadata_only'] for n in nodes)
    b['counts'].update(explicit_cudaDeviceSynchronize_calls=1440,explicit_GetSystemPowerStatus_calls=721,explicit_PowerGetActiveScheme_calls=721,
        numerical_backend_get_device_identity_calls=nonmeta,numerical_buft_get_device_identity_calls=nonmeta,
        internal_synchronization_and_driver_calls='UNKNOWN: API-internal queries/synchronization not equated with explicit registered calls')
    b['monitoring']='Original CREATE_NO_WINDOW|CREATE_SUSPENDED retained. CPU completion-port evidence shows one OS conhost helper. Job active limit2 and process/job commit constraints; exact new-PID events and helper image/SHA; bounded32KiB pipes; requested50ms wall/disk/private-commit polling and fail-closed lifetime reservation. Controller memory ceiling512MiB is sampled; native/job commit limits are OS enforced. Whole controller wall x3 per stage includes main child plus conhost;600x3+1800x3=7200seconds. Requested cadence is not a guaranteed maximum gap; readiness checkpoints are not periodic GPU sampling or continuous residency.'
    b['console_accounting']='1444 explicit experimental launches plus at most1442 automatically created pinned Windows conhost processes =2886 owned starts cap. No extra operator, model, probe or query. Helpers may be fewer; actual unique PID/job events retained. External terminal/Git/CPU delivery tooling is separate, not a whole-system process census.'
    (V/'BUDGET.json').write_text(__import__('json').dumps(b,separators=(',',':'))+'\n',encoding='utf-8')
    print('Prepared1444 explicit launches+1442 console helper cap; cumulative7200owned wallx3; original GPU launch flags unchanged')
if __name__=='__main__':main()
