"""Independent data-only replay of anonymously downloaded Q32 public material.

No native executable, private capture, GPU, or original analysis code is used.
Public byte integrity is distinct from independent numerical qualification.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import lzma
import math
from pathlib import Path
import tempfile


def sha(b):
    return hashlib.sha256(b).hexdigest()


def read(p):
    return json.loads(p.read_text())


def near(a, b):
    assert math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-10), (a, b)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--directory', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    d = args.directory
    manifest = read(d / 'FILES.json')
    for item in manifest['files']:
        b = (d / item['file']).read_bytes()
        assert len(b) == item['bytes'] and sha(b) == item['sha256'], item['file']
    bundle = read(d / 'archive/BUNDLE.json')
    index = read(d / 'archive/TEXT_INDEX.json')['files']
    selected = {}
    index_by_path = {}
    qualification_records = defaultdict(int)
    compressed_hash = hashlib.sha256()
    compressed_bytes = 0
    with tempfile.TemporaryFile() as packed:
        for item in bundle['ordered_parts']:
            b = (d / 'archive' / item['file']).read_bytes()
            assert len(b) == item['bytes'] and sha(b) == item['sha256']
            compressed_hash.update(b)
            compressed_bytes += len(b)
            packed.write(b)
        assert compressed_bytes == bundle['bytes']
        assert compressed_hash.hexdigest() == bundle['sha256']
        packed.seek(0)
        count = 0
        with lzma.open(packed, 'rt', encoding='utf8') as expanded:
            for line in expanded:
                item = json.loads(line)
                entry = index[count]
                assert item['path'] == entry['path']
                text = item['text'].encode('utf8')
                assert len(text) == entry['public_bytes']
                assert sha(text) == entry['public_sha256']
                assert item['path'] not in index_by_path
                index_by_path[item['path']] = entry
                path = item['path']
                for group in ('qualification-08/geometry-checks', 'qualification-08/comparisons',
                              'closure-09/capacity-checks', 'closure-09/EOG-cap-checks',
                              'closure-09/negative-checks'):
                    if path.startswith('work/' + group + '/') and path.endswith('.json'):
                        assert json.loads(item['text'])['passed'], path
                        qualification_records[group] += 1
                if (path.startswith('work/panel-01/') or path in (
                    'work/ledger.jsonl', 'work/INHERITED_ACCOUNTING.json',
                    'work/BUDGET_REGISTRATION_V2.json',
                    'work/PANEL_COST_MODEL_CORRECTION_V3.json',
                    'work/closure-09/QUALIFICATION_COMPLETE.json',
                    'work/qualification-08/CORE_GATES_COMPLETE.json',
                )):
                    selected[path] = item['text']
                count += 1
        assert count == len(index) == bundle['records']

    def obj(path):
        return json.loads(selected['work/' + path])

    def raw_sha(path):
        return index_by_path['work/' + path]['raw_sha256']

    plan = obj('panel-01/PLAN.json')
    freeze = obj('panel-01/FROZEN.json')
    assert obj('panel-01/COMPLETE.json')['passed']
    assert obj('qualification-08/CORE_GATES_COMPLETE.json')['passed']
    assert obj('closure-09/QUALIFICATION_COMPLETE.json')['passed']
    assert qualification_records['closure-09/capacity-checks'] == 6
    assert qualification_records['closure-09/EOG-cap-checks'] == 12
    assert qualification_records['closure-09/negative-checks'] == 5
    assert raw_sha('panel-01/PLAN.json') == freeze['plan']['sha256']
    assert len(plan['workers']) == 24
    assert plan['measured'] == plan['primers'] == 96
    assert obj('BUDGET_REGISTRATION_V2.json')['new_request_ceiling'] == 640
    assert obj('PANEL_COST_MODEL_CORRECTION_V3.json')['formal_not_started']
    measured, warmups = {}, {}
    totals, warm_totals = defaultdict(float), defaultdict(float)
    caller_totals, worker_totals = defaultdict(float), defaultdict(float)
    physical = defaultdict(Counter)
    for worker in plan['workers']:
        base = 'panel-01/runs/' + worker['id'] + '/'
        job_path = 'panel-01/' + worker['job']
        assert raw_sha(job_path) == worker['job_sha256']
        job = obj(job_path)
        assert job['target_output_reserve'] == 32 and job['k'] == 3
        assert job['cuda_graphs'] is False and len(job['inputs']) == 8
        arm = worker['arm']
        host = obj(base + 'HOST.json')
        assert host['status'] == 'COMPLETE'
        worker_totals[arm] += host['worker_wall_s']
        caller_totals[arm] += obj(base + 'CALLER_COST.json')['caller_inclusive_wall_s']
        for i in range(0, 8, 2):
            first, second = job['inputs'][i:i+2]
            assert first['name'] == 'warm-' + second['name']
            assert second['name'].startswith('root-')
            assert first['input'] == second['input']
            assert first['capture'] is second['capture'] is False
            assert second['input']['cap'] == 128
            pair = []
            for entry in (first, second):
                receipt_path = base + 'native/' + entry['name'] + '/receipt.json'
                v = obj(receipt_path)
                assert v['capture'] is False
                assert v['target_output_reserve'] == 32 and v['k'] == 3
                assert all(x == 0 for x in v['observed_API_calls_within_service'].values())
                root = entry['input']['id']
                want = plan['expected_endpoints'][root]
                assert {k: v[k] for k in ('ids', 'eog', 'stop_reason')} == want
                hist = Counter(str(x['width']) for x in v['executions'])
                assert dict(hist) == v['target_physical_width_hist']
                assert all(0 < x['width'] <= 32 and x['active_cells'] ==
                           x['position'] + x['width'] <= 1024 for x in v['executions'])
                key = (worker['round'], arm, root)
                row = dict(round=key[0], arm=arm, root=root,
                           service_s=v['service_seconds'], receipt_sha256=raw_sha(receipt_path))
                if entry['name'].startswith('warm-'):
                    assert key not in warmups
                    warmups[key] = row
                    warm_totals[arm] += v['service_seconds']
                else:
                    assert key not in measured
                    measured[key] = row
                    totals[arm] += v['service_seconds']
                    physical[arm].update(hist)
                pair.append(v)
            for key in ('ids', 'eog', 'stop_reason', 'target_physical_width_hist',
                        'draft_physical_width_hist'):
                assert pair[0][key] == pair[1][key]
    assert len(measured) == len(warmups) == 96
    archived = read(d / 'archive/ANALYSIS.json')
    audit = read(d / 'audit/STATISTICAL_REPLAY.json')
    assert archived['complete'] and audit['complete']
    for previous in archived['rows']:
        key = (previous['round'], previous['arm'], previous['root'])
        assert previous['service_s'] == measured[key]['service_s']
        assert previous['receipt_sha256'] == measured[key]['receipt_sha256']
    for arm, total in totals.items():
        near(total, archived['total_service_s'][arm])
        near(total, audit['measured_service_s'][arm])
        near(warm_totals[arm], audit['warmup_service_s'][arm])
        near(caller_totals[arm], audit['complete_caller_total_s'][arm])
        near(worker_totals[arm], audit['native_worker_total_s'][arm])
    contrasts = []
    candidate = 'L_REF1G_D4'
    for arm in plan['orders'][0]:
        if arm == candidate:
            continue
        ratios = [z['service_s'] / measured[(rnd, arm, root)]['service_s']
                  for (rnd, a, root), z in measured.items() if a == candidate]
        assert len(ratios) == 16
        ratio = totals[candidate] / totals[arm]
        geo = math.exp(sum(map(math.log, ratios)) / len(ratios))
        old = next(x for x in audit['contrasts'] if x['baseline'] == arm)
        near(ratio, old['aggregate_time_ratio'])
        near(geo, old['paired_geomean_ratio'])
        contrasts.append(dict(baseline=arm, aggregate_time_ratio=ratio,
                              time_reduction_fraction=1-ratio, paired_geomean_ratio=geo))
    ledger = [json.loads(x) for x in selected['work/ledger.jsonl'].splitlines()]
    reserved = [x for x in ledger if x['event'] == 'RESERVE']
    inherited = obj('INHERITED_ACCOUNTING.json')
    requests = inherited['requests'] + sum(x['requests'] for x in reserved)
    rows = inherited['rows'] + sum(x['rows'] for x in reserved)
    assert requests <= 640 and rows <= 2000000
    costs = read(d / 'audit/FULL_COSTS.json')
    assert costs['cumulative'] == dict(requests=requests, reserved_rows=rows)
    result = dict(passed=True, performance_complete=True,
                  independent_statistical_replay_passed=True,
                  public_files=len(manifest['files']), public_text_records=count,
                  bundle_sha256=bundle['sha256'], measured=96, warmups=96,
                  measured_service_s=dict(totals), warmup_service_s=dict(warm_totals),
                  complete_caller_total_s=dict(caller_totals),
                  native_worker_total_s=dict(worker_totals), contrasts=contrasts,
                  measured_target_physical_width_hist={k: dict(v) for k, v in physical.items()},
                  cumulative=dict(requests=requests, reserved_rows=rows),
                  archived_qualification_passed_flags_verified=dict(qualification_records),
                  native_requests_started=0,
                  limitations=['Descriptive exposed-root deployment, no population inference',
                               'Public hashes and text replay do not independently rerun private numerical captures',
                               'Two D4 arms change lowering and projection together',
                               'Different model size, quantization and graph policy from prior8B work'])
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(passed=True, measured=96, warmups=96, cumulative=result['cumulative'])))


if __name__ == '__main__':
    main()
