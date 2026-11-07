from pathlib import Path
import json,time,statistics
R=Path(__file__).parent
a=[]
for p in (R/'raw').glob('*/RESULT.json'):
 j=json.loads(p.read_text());a.append((j['host_seconds']*1000-j['metrics']['whole_request_ms'],j['unit_id']))
print('host minus C++ whole ms smallest',sorted(a)[:8])
print('monotonic implementation',time.get_clock_info('monotonic'))
values=[]
for _ in range(1000):
 t=time.monotonic()
 while time.monotonic()==t:pass
 values.append((time.monotonic()-t)*1000)
print('empirical nonzero granularity ms min median max',min(values),statistics.median(values),max(values))
(R/'CPU_TIMER_AUDIT.json').write_text(json.dumps(dict(host_minus_cpp_ms=sorted(a),clock=str(time.get_clock_info('monotonic')),empirical_min_step_ms=min(values),empirical_median_step_ms=statistics.median(values),cpu_only=True),indent=2)+'\n')
