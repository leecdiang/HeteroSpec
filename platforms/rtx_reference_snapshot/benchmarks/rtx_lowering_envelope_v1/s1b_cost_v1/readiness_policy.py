"""Pure CPU admission contract. No process launch, NVML, CUDA or device APIs.

The 5% ceiling is retained prospectively as conservative environment isolation,
not asserted to be a mathematical requirement for bitwise CUDA results.
"""
import math

POLICY = 'A_STRICT_IDLE_V1'

def validate_policy(policy):
    assert policy['contract'] == POLICY, 'unreviewed readiness policy'
    assert policy['maximum_utilization_percent'] == 5, 'strict idle ceiling fixed'
    assert policy['maximum_temperature_C'] == 55
    assert policy['minimum_free_MiB'] == 512
    assert policy['AC_required'] == 1
    assert policy['attempts_per_slot'] == 1 and policy['cooldown_or_retry'] is False
    assert policy['utilization_interpretation'] == 'sampled_environment_isolation_not_numerical_theorem'

def validate_observation(result, policy):
    validate_policy(policy)
    assert result['gpu'] == policy['gpu'] and result['driver'] == policy['driver'], 'GPU/driver identity'
    for key in ('total_MiB', 'used_MiB', 'util', 'temperature_C'):
        value = result[key]
        assert type(value) in (int, float) and math.isfinite(value), 'missing/nonfinite telemetry: '+key
    assert result['total_MiB'] == policy['total_MiB'], 'device capacity identity'
    assert 0 <= result['used_MiB'] <= result['total_MiB'], 'invalid memory telemetry'
    assert 0 <= result['util'] <= 100 and 0 <= result['temperature_C'] <= 150, 'invalid telemetry range'
    assert type(result['AC']) is int and result['AC'] == policy['AC_required'], 'AC power required'
    assert result['power_scheme_guid'] == policy['power_scheme_guid'], 'power scheme drift'
    assert result['total_MiB']-result['used_MiB'] >= policy['minimum_free_MiB'], 'VRAM headroom'
    assert result['temperature_C'] <= policy['maximum_temperature_C'], 'temperature ceiling'
    assert result['util'] <= policy['maximum_utilization_percent'], 'strict idle ceiling; terminal, no retry'
    return {'admitted': True, 'contract': POLICY, 'continuous_isolation_proven': False,
            'numerical_qualification_established': False, 'performance_qualification_established': False}
