"""Frozen Windows high-resolution monotonic QPC clock, verified at runtime."""
import time

def require_clock():
    info=time.get_clock_info('perf_counter')
    assert info.monotonic and not info.adjustable
    assert info.implementation=='QueryPerformanceCounter()'
    assert round(info.resolution*1e9)==100,'frozen QPC clock resolution drift'
    return vars(info)|dict(source='time.perf_counter_ns',units='nanoseconds',resolution_ns=100)

def clock_ns():return time.perf_counter_ns()
