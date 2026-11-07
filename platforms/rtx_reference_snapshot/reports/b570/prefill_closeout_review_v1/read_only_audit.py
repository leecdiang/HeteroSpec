"""Read existing evidence; write only a new, explicitly selected review receipt."""
from pathlib import Path
import argparse
import collections
import csv
import datetime as dt
import hashlib
import json
import math
import subprocess
import time
import zipfile

REFERENCE = '51febaddcf49bb18565e568cf964a6e5c78876c9'
ATTEMPT2 = 'e44c4df04c895b55ef734ee7b0659189158f95ab'
REVIEWED_HEAD = '60b7d6a9301557c9a26c7d89acbe1b9d122bb53d'
PREFIX = 'benchmarks/b570_prefill_closeout_v1/'
ENDPOINT = ['ids', 'eog', 'length', 'terminal_id', 'stop_reason']


def check(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def geometric(values):
    values = list(values)
    check(values and all(math.isfinite(x) and x > 0 for x in values), 'Nonfinite/nonpositive cost')
    return math.exp(math.fsum(math.log(x) for x in values) / len(values))


def same_output(a, b, speculative):
    for key in ENDPOINT + (['cycles'] if speculative else []):
        check(a[key] == b[key], 'Endpoint/state mismatch: ' + key)


def audit(repo, native):
    began = time.perf_counter()
    package = repo / PREFIX
    hashes = {}

    def file_digest(path):
        path = Path(path)
        key = str(path.resolve())
        if key not in hashes:
            h = hashlib.sha256()
            with path.open('rb') as f:
                for block in iter(lambda: f.read(8 * 1024**2), b''):
                    h.update(block)
            hashes[key] = h.hexdigest()
        return hashes[key]

    def identity(row):
        p = Path(row['path'])
        check(p.stat().st_size == row['bytes'] and file_digest(p) == row['sha256'], 'Hash/size drift: ' + str(p))

    def git_json(commit, path):
        return json.loads(subprocess.check_output(['git', 'show', commit + ':' + path], cwd=repo))

    payload = read(package / 'PACKAGE_MANIFEST.json')
    check(payload['count'] == len(payload['files']) == 100, 'Sealed payload inventory changed')
    for row in payload['files']:
        identity(dict(row, path=str(package / row['path'])))
    # Bind all original package bytes, including its manifest/check receipt, to the reviewed Git commit.
    listing = subprocess.check_output(['git', 'ls-tree', '-r', '--format=%(objectname) %(path)', REVIEWED_HEAD, '--', PREFIX], cwd=repo, text=True)
    objects = [line.split(' ', 1) for line in listing.splitlines()]
    stream = subprocess.check_output(['git', 'cat-file', '--batch'], cwd=repo,
                                    input=''.join(oid + '\n' for oid, path in objects).encode())
    offset = 0
    for oid, path in objects:
        end = stream.index(b'\n', offset)
        size = int(stream[offset:end].split()[2]); offset = end + 1
        check(stream[offset:offset+size] == (repo / path).read_bytes(), 'Reviewed Git blob differs: ' + path)
        offset += size + 1

    reg = read(package / 'REGISTRATION.json')
    frozen = read(package / 'FROZEN_FILES.json')
    check(file_digest(package / 'FROZEN_FILES.json') == reg['frozen_files_sha256'], 'Frozen manifest binding')
    for row in frozen:
        identity(row)
    original = Path('C:/hs/b570-formal-request-20261020')
    prior = Path('C:/hs/b570-draft-prefill-submit-20261020-r2')
    bridge = Path('C:/hs/b570-spec-bridge-20261020200000')
    old_manifest = git_json(REFERENCE, 'benchmarks/b570_formal_request_v1/RAW_LOGITS_MANIFEST.json')
    bridge_manifest = git_json(REFERENCE, 'benchmarks/b570_spec_request_bridge_v1/RAW_LOGITS_MANIFEST.json')
    panel = read(package / 'INPUT_PANEL.json')
    check(panel == git_json(REFERENCE, 'benchmarks/b570_formal_request_v1/INPUT_PANEL.json'), 'Input reference replaced')
    for row in old_manifest:
        identity(dict(row, path=str(original / row['path'])))
    for row in bridge_manifest:
        identity(dict(row, path=str(bridge / row['path'])))
    old_map = {row['path'].replace('\\', '/'): row for row in old_manifest}
    bridge_map = {row['path'].replace('\\', '/'): row for row in bridge_manifest}
    check(len(old_map) == 914 and len(bridge_map) == 78, 'Historical inventories')
    prior_manifest = git_json(ATTEMPT2, 'benchmarks/b570_draft_prefill_submission_v1/attempt2/RAW_LOGITS_MANIFEST.json')
    for row in prior_manifest:
        identity(dict(row, path=str(prior / row['path'])))
    check(len(prior_manifest) == 346, 'Prior numerical qualification count')
    original_models = git_json(REFERENCE, 'benchmarks/b570_formal_request_v1/MODEL_IDENTITY.json')
    check(read(package / 'MODEL_RECHECK.json') == original_models, 'Model/tokenizer identity differs from committed PR134')
    for row in original_models:
        identity(row)
    original_build = git_json(REFERENCE, 'benchmarks/b570_formal_request_v1/BUILD_MANIFEST.json')
    original_dlls = {Path(row['path']).name: row for row in original_build['files'] if Path(row['path']).suffix == '.dll'}
    copied_dlls = read(package / 'RUNTIME_MANIFEST.json')
    check(len(copied_dlls) == len(original_dlls) == 5, 'Numerical DLL inventory')
    for row in copied_dlls:
        old = original_dlls[Path(row['path']).name]
        check((row['bytes'], row['sha256']) == (old['bytes'], old['sha256']), 'Numerical DLL differs from committed PR134')
        identity(row)
        identity(dict(row, path=str(native / 'build/Release' / Path(row['path']).name)))

    compact_row = read(package / 'COMPACT_MANIFEST.json')
    local_raw = read(package / 'LOCAL_RAW_ARCHIVE.json')
    identity(dict(compact_row, path=str(package / 'COMPACT_EVIDENCE.zip')))
    identity(local_raw)
    identity(dict(read(package / 'HISTORICAL_COMPACT_MANIFEST.json'), path=str(package / 'HISTORICAL_COMPACT.zip')))
    compact = zipfile.ZipFile(package / 'COMPACT_EVIDENCE.zip')
    vectors = zipfile.ZipFile(local_raw['path'])
    check(compact.testzip() is None, 'Compact archive CRC failure')
    raw_members = set(vectors.namelist())
    check(len(raw_members) == len(vectors.namelist()) == 976, 'Raw archive inventory/duplicates')
    expected_raw = set()
    captured_counts = collections.Counter()
    all_records = []
    cost_windows = []
    ledger = read(package / 'BUDGET_LEDGER.json')
    check(len(ledger['sessions']) == ledger['worker_starts'] == 9, 'Native process accounting')
    previous_exit = None
    envelopes = []
    endpoints = [(64, 'CAP'), (53, 'EOG'), (41, 'EOG'), (64, 'CAP')]
    for step, recorded in enumerate(ledger['sessions']):
        mode = 'E0' if step == 0 else ('E1' if step < 5 else 'E2')
        index = 0 if step == 0 else (step - 1) % 4
        name = f'{mode}-{index}'
        rc = read(package / (name + '.PROCESS_RECEIPT.json'))
        data = read(package / name / 'result.json')
        check(rc == recorded, 'Ledger/receipt mismatch: ' + name)
        check((package / name / 'result.json').read_bytes() == (native / name / 'result.json').read_bytes() == compact.read(name + '/result.json'), 'Native/compact/Git result mismatch')
        check(rc['status'] == 'PROCESS_COMPLETED' and rc['exit_code'] == 0 and rc['exit_observed'] and rc['job_kill_on_close'] and rc['capture_complete'], 'Incomplete worker receipt')
        check(data['status'] == mode + '_PASS' and data['normal_cleanup_returned'] and rc['normal_cleanup_returned'], 'Native worker failure')
        check(rc['completed_requests'] == len(data['requests']) == (4 if mode == 'E0' else (6 if mode == 'E1' else 32)), 'Request count')
        start = dt.datetime.fromisoformat(rc['started_utc'])
        exit_time = dt.datetime.fromisoformat(rc['exit_observed_utc'])
        check(previous_exit is None or start > previous_exit, 'Overlapping model processes')
        previous_exit = exit_time
        check(0 < rc['charged_seconds'] < rc['deadline_seconds'] == reg['worker_timeouts_seconds'][mode], 'Process safety time')
        check(abs((exit_time - dt.datetime.fromisoformat(rc['spawned_utc'])).total_seconds() - rc['charged_seconds']) < 1, 'Wall-clock/charge disagreement')
        commit_time = subprocess.check_output(['git', 'show', '-s', '--format=%cI', rc['freeze_commit']], cwd=repo, text=True).strip()
        check(dt.datetime.fromisoformat(commit_time) < start, 'Freeze occurred after execution')
        check(subprocess.check_output(['git', 'show', rc['freeze_commit'] + ':' + PREFIX + 'closeout.cpp'], cwd=repo) == (package / 'closeout.cpp').read_bytes(), 'Frozen source drift')
        check(subprocess.check_output(['git', 'show', rc['freeze_commit'] + ':' + PREFIX + 'REGISTRATION.json'], cwd=repo) == (package / 'REGISTRATION.json').read_bytes(), 'Frozen registration drift')
        service_sum = sum(r['service_seconds'] for r in data['requests'])
        check(service_sum + data['model_load_seconds'] <= rc['charged_seconds'] + .1, 'Cost windows exceed supervised envelope')
        envelopes.append({'worker': name, 'service_sum': service_sum, 'model_load_seconds': data['model_load_seconds'], 'supervised_charge': rc['charged_seconds']})
        cost_windows.extend([{'kind': k, 'process': name, 'slot': '', 'seconds': value} for k, value in [
            ('model_load', data['model_load_seconds']), ('worker_wall', rc['charged_seconds']), ('wrapper_total_including_preflight', rc['total_wrapper_seconds'])]])
        captures = {}
        for position, record in enumerate(data['requests']):
            check(math.isfinite(record['service_seconds']) and record['service_seconds'] >= record['request_seconds'] > 0, 'Invalid timer')
            phase_sum = sum(record['target_decode_seconds'].values()) + sum(record['draft_decode_seconds'].values())
            check(phase_sum <= record['request_seconds'] + 1e-5, 'Phase sum exceeds request window')
            inp = panel['warmup'] if mode == 'E0' else next(x for x in panel['inputs'] if x['id'] == record['input_id'])
            inp_index = None if mode == 'E0' else panel['inputs'].index(inp)
            speculative = record['label'] != 'R'
            reference_data = read(bridge / 'results/result.json') if mode == 'E0' else read(original / f'qual-{inp_index}/result.json')
            same_output(reference_data['requests'][2 if speculative else 0], record, speculative)
            if mode != 'E0':
                check((record['length'], record['stop_reason']) == endpoints[inp_index], 'Endpoint changed')
            expected_calls = 0 if not speculative else (1 if record['label'] == 'SUBMIT' else len(inp['prompt_ids']))
            check(record['draft_prefill_api_calls'] == expected_calls, 'Submission label/count mismatch')
            check(record['capture'] == record['observers_installed'], 'Observer flag discrepancy')
            if not record['capture']:
                check(not record['actual_signatures'] and record['draft_prefill_q_node_observations'] == 0, 'Observer present in noncapture request')
            else:
                old_prefix = 'results/QB/' if mode == 'E0' else f"qual-{inp_index}/{'qual-2' if speculative else 'qual-0'}/"
                inventory = bridge_map if mode == 'E0' else old_map
                old_root = bridge if mode == 'E0' else original
                expected = {path[len(old_prefix):]: row for path, row in inventory.items() if path.startswith(old_prefix)}
                new_prefix = name + '/' + record['raw_dir'] + '/'
                check({p[len(new_prefix):] for p in raw_members if p.startswith(new_prefix)} == set(expected), 'Capture vector set differs')
                for relative, old_row in expected.items():
                    member = new_prefix + relative
                    raw = vectors.read(member)
                    check(len(raw) == old_row['bytes'] and digest_bytes(raw) == old_row['sha256'], 'Original-byte mismatch: ' + member)
                    check(raw == (old_root / (old_prefix + relative)).read_bytes() == (native / member).read_bytes(), 'Archive/local/original vector mismatch')
                    expected_raw.add(member)
                captured_counts[mode] += len(expected)
                if speculative:
                    member = name + '/' + record['raw_dir'] + '/prefill-events.json'
                    event_bytes = compact.read(member)
                    check(event_bytes == (native / member).read_bytes(), 'Geometry archive mismatch')
                    events = json.loads(event_bytes)
                    check(events['prompt_ids'] == inp['prompt_ids'] and events['last_token_logits_only'], 'Prefill inputs/flags')
                    check(events['draft_kv_max'] == events['target_kv_max'] == len(inp['prompt_ids']) - 1, 'Prefill KV endpoint')
                    check(len(events['qk']) == len(events['masks']) == len(inp['prompt_ids']) * 28, 'Missing physical layer/ubatch observation')
                    check(all(x['ne'][1] == 1 for x in events['qk']), 'Physical q is not1')
                    for token in range(len(inp['prompt_ids'])):
                        check(len({x['name'] for x in events['qk'][token*28:(token+1)*28]}) == 28, 'Missing layer within physical token')
                    captures[record['label']] = events
            if mode in ['E0', 'E1'] and position % 2 == 1:
                check(record['category'] == 'count' and data['requests'][position-1]['category'] == 'capture', 'Capture/count order')
                same_output(data['requests'][position-1], record, speculative)
            all_records.append((mode, index, inp_index, record))
            for key in ['service_seconds', 'request_seconds']:
                cost_windows.append({'kind': key, 'process': name, 'slot': record['slot'], 'seconds': record[key]})
            for model in ['target', 'draft']:
                for phase, value in record[model + '_decode_seconds'].items():
                    cost_windows.append({'kind': model + '_' + phase, 'process': name, 'slot': record['slot'], 'seconds': value})
        if mode in ['E0', 'E1']:
            check(captures['BASE'] == captures['SUBMIT'], 'Ordered q/key/mask evidence differs')
    check(expected_raw == raw_members and dict(captured_counts) == {'E0': 62, 'E1': 914}, 'Raw capture total')
    compact.close(); vectors.close()

    independent_order = []
    arms = ['R', 'BASE_A', 'BASE_B', 'SUBMIT']
    for session in range(4):
        for j in range(4):
            i = (j + session) % 4; offset = (session + i) % 4
            for arm in arms[offset:] + arms[:offset]:
                for category in ['warmup', 'measured']:
                    independent_order.append({'slot': f'B570/{session}/Qwen3/{i}/{arm}/{category}', 'session': session,
                                              'family': 'Qwen3', 'input_index': i, 'arm': arm, 'category': category})
    check(independent_order == read(package / 'ORDER.json'), 'Registered order deviates from balanced matrix')
    timed = [(session, i, row) for mode, session, i, row in all_records if mode == 'E2']
    check(len(timed) == len(independent_order) == 128, 'Timing matrix incomplete')
    normalized = read(package / 'NORMALIZED_RECORDS.json')
    measured = {}
    for (session, i, row), planned, norm in zip(timed, independent_order, normalized):
        check(row['slot'] == planned['slot'] and row['label'] == planned['arm'] and row['category'] == planned['category'] and i == planned['input_index'], 'Order or paired-warmup mismatch')
        check(not row['capture'] and not row['observers_installed'], 'Timed observer enabled')
        check(norm == dict(planned, seconds=row['service_seconds'], qualified=True, exit_ok=True, request_seconds=row['request_seconds']), 'Raw-to-normalized mismatch')
        if row['category'] == 'measured': measured[session, i, row['label']] = row
    slots = read(package / 'REGISTERED_SLOTS.json')
    check(len(slots) == len({r['slot'] for r in slots}) == 156 == len(all_records), 'Registered request uniqueness/completeness')
    check({r['slot'] for r in slots} == {r['slot'] for m, s, i, r in all_records}, 'Foreign/missing request')
    actual_disposition = read(package / 'SLOT_DISPOSITION.json')
    check(len(actual_disposition) == 156 and all(r['status'] == 'NATIVE_RECORD_COMPLETE' for r in actual_disposition), 'Disposition completeness')
    ratios, economics, base_economics, aa = [], [], [], []
    for session in range(4):
        for i in range(4):
            t = {arm: measured[session, i, arm]['service_seconds'] for arm in arms}
            baseline = (t['BASE_A'] + t['BASE_B']) / 2
            ratios.append((session, i, t['SUBMIT'] / baseline))
            economics.append(t['SUBMIT'] / t['R']); base_economics.append(baseline / t['R'])
            aa.append((i, t['BASE_A'] / t['BASE_B']))
    primary = geometric(r for s, i, r in ratios)
    imbalance = max(abs(geometric(r for j, r in aa if j == i) - 1) for i in range(4))
    session_ratios = [geometric(r for j, i, r in ratios if j == s) for s in range(4)]
    reconstructed = {'candidate_over_dual_control': primary, 'candidate_over_R': geometric(economics),
                     'dual_control_over_R': geometric(base_economics), 'aa_max_input': imbalance,
                     'session_ratios': session_ratios,
                     'practical_screen_pass': 1-primary > max(.02, imbalance) and all(r < 1 for r in session_ratios)}
    for name in ['INDEPENDENT_ANALYSIS.json', 'TOOLKIT_ANALYSIS.json']:
        result = read(package / name)
        for key, value in reconstructed.items():
            if isinstance(value, list): check(all(abs(a-b) < 1e-12 for a, b in zip(value, result[key])), name + ':' + key)
            elif isinstance(value, bool): check(result[key] == value, name + ':' + key)
            else: check(abs(result[key] - value) < 1e-12, name + ':' + key)
    with (package / 'TIMING_TABLE.csv').open(newline='', encoding='utf-8') as f:
        csv_rows = list(csv.DictReader(f))
    check(len(csv_rows) == 128, 'Timing CSV count')
    for (_, _, row), table in zip(timed, csv_rows):
        check(table['slot'] == row['slot'] and float(table['service_seconds']) == row['service_seconds'] and float(table['request_seconds']) == row['request_seconds'], 'Timing CSV differs from native')
    with (package / 'ALL_COST_WINDOWS.csv').open(newline='', encoding='utf-8') as f:
        cost_rows = list(csv.DictReader(f))
    check(len(cost_rows) == len(cost_windows), 'Cost-window inventory')
    for raw, table in zip(cost_windows, cost_rows):
        check(all(table[k] == raw[k] for k in ['kind', 'process', 'slot']) and float(table['seconds']) == raw['seconds'], 'Cost window differs from native/receipt')
    charge = math.fsum(r['charged_seconds'] for r in ledger['sessions'])
    check(abs(charge - ledger['charged_worker_seconds']) < 1e-8, 'Whole-worker ledger sum')
    resource = read(package / 'RESOURCE_RECEIPT.json')
    check(resource['other_process_descendant_count'] is None and resource['other_process_count_independently_reconciled'] is False, 'Auxiliary-process uncertainty hidden')
    check(reg['budget']['other_processes'] == resource['other_process_reservation'] == 128, 'Auxiliary reservation retrospectively changed')
    with zipfile.ZipFile(package / 'HISTORICAL_COMPACT.zip') as z:
        entry = 'b570-draft-prefill-submit-20261020-r2/time-1/result.json'
        historical = json.loads(z.read(entry))
        check(z.read(entry) == (prior / 'time-1/result.json').read_bytes(), 'Prior unreceipted timing altered')
        check(len(historical['requests']) == 5 and historical['status'] == 'STARTED' and not (prior / 'time-1.PROCESS_RECEIPT.json').exists(), 'Historical uncertainty changed')
    return {'status': 'PASS_WITH_DECLARED_LIMITATIONS', 'reviewed_head': REVIEWED_HEAD,
            'read_only_inputs': True, 'sealed_payload_files': 100, 'reviewed_git_blobs': len(objects),
            'frozen_files_rechecked': len(frozen), 'original_reference_vectors': len(old_manifest),
            'original_model_files_rechecked': len(original_models), 'original_numerical_dlls_rechecked': len(copied_dlls),
            'original_bridge_vectors': len(bridge_manifest), 'prior_attempt2_vectors': len(prior_manifest),
            'new_raw_vectors_rechecked': dict(captured_counts), 'raw_archive_sha256': local_raw['sha256'],
            'native_requests': len(all_records), 'native_worker_receipts': 9, 'warmups': 64, 'measurements': 64,
            'reconstructed': reconstructed, 'worker_envelopes': envelopes, 'whole_worker_charge_seconds': charge,
            'primary_timer_source_review': 'Outer C++ request call includes fresh context construction and destructors before return; model load, reference comparisons and result writes are outside.',
            'secondary_timer_limit': 'Per-decode synchronized sums exclude batch construction/loop overhead and cannot replace complete service or establish GPU time.',
            'supervised_worker_charge_limit': 'Wrapper stopwatch includes process start, up-to-0.5s exit polling, result parsing and job cleanup; it is not an exact OS-process lifetime or active CPU/GPU time.',
            'auxiliary_process_limit': '128 is a prospective reservation, not an observed count; helper descendants were neither completely metered nor capped by this wrapper. Full process-budget compliance cannot be certified retrospectively.',
            'fully_protocol_resource_compliant': False,
            'merge_recommendation': 'MERGE_AS_LIMITED_NEGATIVE_CLOSEOUT; not full resource-budget compliance or a new optimized baseline',
            'reproduction_limit': 'Original audit.py regenerates outputs; verify_delivery.py writes/copies DELIVERY_CHECK.json. Use this separate read-only audit for review, leaving original receipts and archives intact.',
            'raw_access_limit': 'Original bytes were locally authenticated against committed references; a remote reviewer needs the author-supplied raw archive. No third-party certification.',
            'review_duration_seconds': time.perf_counter() - began,
            'finished_utc': dt.datetime.now(dt.timezone.utc).isoformat()}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--native-root', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    check(not args.out.exists(), 'Review receipt exists; choose a new output path')
    result = audit(args.repo.resolve(), args.native_root.resolve())
    result['auditor_sha256'] = digest_bytes(Path(__file__).read_bytes())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x', encoding='utf-8') as f:
        json.dump(result, f, indent=2); f.write('\n')
    print(json.dumps(result, indent=2))
