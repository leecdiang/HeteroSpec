"""Pure observations and actual OS process metadata; never invoke nvidia-smi."""
import copy,sys
from common import V,load,save
from readiness_policy import validate_observation,validate_policy
import run_s1b as R

def main():
    old=load('D:/hs113-bridge/benchmarks/rtx_lowering_envelope_v1/s1a_bridge_v1/F0.json')
    p=dict(old['admission_policy'],contract='A_STRICT_IDLE_V1',maximum_utilization_percent=5,
           maximum_temperature_C=55,minimum_free_MiB=512,AC_required=1,attempts_per_slot=1,
           cooldown_or_retry=False,utilization_interpretation='sampled_environment_isolation_not_numerical_theorem')
    base=dict(gpu=p['gpu'],driver=p['driver'],total_MiB=p['total_MiB'],used_MiB=119,
              util=0,temperature_C=46,AC=1,power_scheme_guid=p['power_scheme_guid'])
    positive=[];negative=[]
    for label,delta in [('idle',{}),('at_util_ceiling',dict(util=5)),('fractional_idle',dict(util=4.9)),
                        ('at_temperature_ceiling',dict(temperature_C=55)),
                        ('exact_headroom',dict(used_MiB=p['total_MiB']-512))]:
        assert validate_observation(base|delta,p)['admitted'];positive.append(label)
    def reject(label,fn):
        try:fn()
        except (AssertionError,KeyError,TypeError,ValueError) as exc:negative.append(dict(label=label,error=repr(exc)));return
        raise AssertionError('negative accepted: '+label)
    cases=[('old32',dict(util=32)),('above5',dict(util=5.01)),('fully_busy',dict(util=100)),
           ('over_temperature',dict(temperature_C=55.01)),('low_VRAM',dict(used_MiB=p['total_MiB']-511)),
           ('wrong_GPU',dict(gpu='other')),('driver_drift',dict(driver='other')),('capacity_drift',dict(total_MiB=1)),
           ('battery',dict(AC=0)),('bool_AC',dict(AC=True)),('power_drift',dict(power_scheme_guid='other')),
           ('negative_util',dict(util=-1)),('excess_util',dict(util=101)),('NaN',dict(util=float('nan'))),
           ('infinity',dict(used_MiB=float('inf'))),('NA',dict(util='N/A')),('negative_memory',dict(used_MiB=-1))]
    for label,delta in cases:reject(label,lambda delta=delta:validate_observation(base|delta,p))
    for key in base:
        missing=dict(base);del missing[key];reject('missing_'+key,lambda missing=missing:validate_observation(missing,p))
    for key,value in [('maximum_utilization_percent',32),('contract','B_RELAXED'),('attempts_per_slot',2),('cooldown_or_retry',True)]:
        reject('policy_'+key,lambda key=key,value=value:validate_policy(p|{key:value}))
    # Production conflict enumerator uses only Win32 process executable metadata.
    R.owned_conflicts({'conflicting_owned_executables':[]})
    reject('actual_current_process_conflict',lambda:R.owned_conflicts({'conflicting_owned_executables':[sys.executable]}))
    save(V/'CPU_QPC_READINESS_TESTS.json',dict(status='PASS',positive=positive,negative=negative,
        actual_production_OS_conflict_check=True,replayed_observations_are_CPU_fixtures=True,
        old32_observation_still_rejected=True,new_GPU_queries=0,CUDA_loads=0,graph_computes=0,
        no_policy_B_or_automatic_retry_path=True))
    print('PASS',len(positive),'positive,',len(negative),'negative CPU readiness cases; no device query')
if __name__=='__main__':main()
