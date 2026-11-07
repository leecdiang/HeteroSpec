"""Summarize passive power/resource samples over each settled timing session."""
import argparse, datetime, hashlib, json, pathlib

def rows(p):
    return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x]

def timestamp(s):
    return datetime.datetime.fromisoformat(s.replace('Z', '+00:00'))

def main(root, operations, out):
    root, operations, out = map(pathlib.Path, (root, operations, out))
    assert not out.exists(), 'fresh audit output required'
    power_path = operations/'CONFIRM03_POWER.jsonl'
    resources_path = operations/'CONFIRM03_TELEMETRY.jsonl'
    power, resources = rows(power_path), rows(resources_path)
    ledger = rows(root/'LEDGER.jsonl')
    report = []
    for i in range(4):
        name = f'formal_s{i}'
        events = [x for x in ledger if x['unit'] == name]
        assert len(events) == 2 and [x['event'] for x in events] == ['START', 'END'], 'unsettled timing session'
        start, end = map(lambda x: timestamp(x['utc']), events)
        assert timestamp(power[0]['utc']) <= start and timestamp(power[-1]['utc']) >= end, 'power monitor does not cover session'
        assert timestamp(resources[0]['utc']) <= start, 'resource monitor started after session'
        ps = [x for x in power if start <= timestamp(x['utc']) <= end]
        rs = [x for x in resources if start <= timestamp(x['utc']) <= end]
        assert ps and rs, 'no timing samples'
        gpu = [x['gpu_csv'].split(',') for x in rs if x.get('exit_code') == 0]
        gaps = lambda xs: max((timestamp(b['utc'])-timestamp(a['utc'])).total_seconds() for a,b in zip(xs,xs[1:])) if len(xs)>1 else None
        report.append(dict(session=i, start=events[0]['utc'], end=events[1]['utc'],
            power_samples=len(ps), resource_samples=len(rs),
            all_AC=all(x['status_read'] and x['ACLineStatus']==1 for x in ps),
            battery_percent_range=[min(x['battery_percent'] for x in ps),max(x['battery_percent'] for x in ps)],
            power_schemes=sorted({x['active_scheme'] for x in ps}),
            power_read_errors=sum(not x['status_read'] or x['scheme_error']!=0 for x in ps),
            resource_read_errors=sum(x.get('exit_code')!=0 for x in rs),
            resource_monitor_brackets_session=timestamp(resources[-1]['utc'])>=end,
            unsampled_resource_tail_seconds=max(0,(end-timestamp(resources[-1]['utc'])).total_seconds()),
            min_available_RAM_bytes=min(x['available_ram'] for x in rs),
            min_GPU_free_MiB=min(float(x[2]) for x in gpu),
            max_GPU_temperature_C=max(float(x[3]) for x in gpu),
            GPU_UUIDs=sorted({x[0].strip() for x in gpu}),
            max_power_sample_gap_seconds=gaps(ps), max_resource_sample_gap_seconds=gaps(rs)))
    result=dict(status='PASSIVE_ENVIRONMENT_SUMMARY',sessions=report,
        sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (power_path,resources_path)},
        limitation='Approximately ten-second passive samples, not continuous peak guarantees. Monitor began during original-reference generation; complete formal-session coverage is checked separately. No power setting was changed by this monitor.')
    with out.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('operations');p.add_argument('out');a=p.parse_args();main(a.root,a.operations,a.out)
