"""B570 boundary-0 KV subset interventions; no new native math or speculative path.

Python >=3.11. CPU preparation/analysis are portable; GPU execution uses the
byte-pinned PR101 Windows worker and its existing identity/endpoint audits.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib
import importlib.util
import json
import math
import os
from pathlib import Path
import random
import struct
import subprocess
import sys
import time
from datetime import datetime, timezone

BASELINE_COMMIT = '26706c9fb4818ec3465e45acea029c4ab88a390f'
CASES = ('GSM8K/test/1248', 'GSM8K/test/831', 'GSM8K/test/1011', 'GSM8K/test/1249')
SOURCE_BLOBS = {
    'code/common98.py': '3d29edaabd837532e17bcd16623cfc40bf136b63',
    'code/controller100.py': '3bc67b5d46e1cf1d957e44612161310c1656866e',
    'code/verify100.py': '65f9079ad39472dd1578ccabf71b9bccc3b90e91',
    'DONORS.json': 'b97792c02121f622555825917f8fa3ad741bc72f',
    'INPUTS.json': 'a4d62e3bae72ac75812d7d69c4a17b69328df3dc',
    'PLAN.json': 'e216856d79dfb54f399dc2664bcdd5f37fb71693',
    'KV_LOGITS_CROSS.json': '67ac93758a1719b26f7b33ab462c5aafb215e1e7',
}
SELECTORS = ('K_all', 'V_all', 'K_layer0', 'V_layer0', 'KV_layer0',
             'KV_early', 'KV_middle', 'KV_late', 'KV_prefix128', 'KV_tail128')


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def encoded(value) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + '\n').encode()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_hash(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_new(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(encoded(value)); stream.flush(); os.fsync(stream.fileno())


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def pin(path: Path) -> dict:
    return {'path': str(path.resolve()), 'bytes': path.stat().st_size, 'sha256': file_hash(path)}


def checked_payload(root: Path, value: dict) -> bytes:
    path = (root / value['path']).resolve()
    require(path.is_relative_to(root.resolve()), 'payload escapes its root')
    data = path.read_bytes()
    require(len(data) == value['bytes'] and digest(data) == value['sha256'], 'payload pin mismatch')
    return data


def layout(data: bytes, n: int) -> dict:
    """Exact PR101 parse_kv wire contract, extended only with byte spans.

    This is NOT a general llama.cpp state parser. Reject other models, KV dtypes,
    sequence IDs, positions, magic values, crop/extension and unexpected layouts.
    """
    require(type(n) is int and 0 < n <= 768, 'invalid cell count')
    cursor = 0

    def take(fmt: str):
        nonlocal cursor
        size = struct.calcsize('<' + fmt)
        require(cursor + size <= len(data), 'truncated state header')
        result = struct.unpack_from('<' + fmt, data, cursor)[0]
        cursor += size
        return result

    require(take('I') == 0xaf143cd8 and take('i') == 0, 'unsupported state magic/type')
    require(take('I') == 1 and take('I') == n, 'expected one stream and full prompt cells')
    for position in range(n):
        require((take('i'), take('I'), take('i')) == (position, 1, 0), 'position/sequence metadata mismatch')
    transposed = take('I')
    require(transposed in (0, 1) and take('I') == 32, 'unsupported value layout/layer count')
    tensors = []
    metadata = []
    previous = 0
    for role in ('K', 'V'):
        for layer in range(32):
            require(take('i') == 1, 'only F16 KV is admitted')
            if role == 'V' and transposed:
                require(take('I') == 2 and take('I') == 1024, 'invalid transposed V extent')
            else:
                require(take('Q') == 2048, 'invalid F16 row width')
            metadata.append((previous, cursor))
            size = n * 2048
            require(cursor + size <= len(data), 'truncated tensor')
            tensors.append({'role': role, 'layer': layer, 'offset': cursor,
                            'bytes': size, 'transposed': role == 'V' and bool(transposed)})
            cursor += size
            previous = cursor
    require(cursor == len(data), 'extra state bytes')
    return {'n': n, 'tensors': tensors, 'metadata': metadata, 'v_transposed': bool(transposed)}


def finite_kv(data: bytes, description: dict) -> bool:
    # IEEE binary16 exponent ==31 means NaN or infinity, irrespective of sign.
    return all((byte & 0x7c) != 0x7c for t in description['tensors']
               for byte in data[t['offset'] + 1:t['offset'] + t['bytes']:2])


def selection(name: str, n: int) -> tuple[set[str], range, range]:
    require(name in SELECTORS or name in ('ALL', 'EMPTY'), 'unknown selector')
    roles = {'K'} if name.startswith('K_') else ({'V'} if name.startswith('V_') else {'K', 'V'})
    layers = range(0, 1) if name.endswith('layer0') else range(32)
    if name == 'KV_early': layers = range(0, 8)
    if name == 'KV_middle': layers = range(8, 24)
    if name == 'KV_late': layers = range(24, 32)
    positions = range(n)
    if name == 'KV_prefix128': positions = range(min(128, n))
    if name == 'KV_tail128': positions = range(min(128, n), n)
    if name == 'EMPTY': positions = range(0)
    return roles, layers, positions


def spans(description: dict, name: str):
    roles, layers, positions = selection(name, description['n'])
    if not positions:
        return
    lo, hi = positions.start, positions.stop
    for tensor in description['tensors']:
        if tensor['role'] not in roles or tensor['layer'] not in layers:
            continue
        offset = tensor['offset']
        if tensor['transposed']:
            for feature in range(1024):
                yield offset + 2 * (feature * description['n'] + lo), offset + 2 * (feature * description['n'] + hi)
        else:
            yield offset + 2048 * lo, offset + 2048 * hi


def splice(recipient: bytes, donor: bytes, n: int, name: str) -> tuple[bytes, dict]:
    left, right = layout(recipient, n), layout(donor, n)
    require(left == right, 'wire geometry differs')
    require(all(recipient[a:b] == donor[a:b] for a, b in left['metadata']), 'metadata differs; not a byte-only intervention')
    output = bytearray(recipient)
    count = changed = 0
    for a, b in spans(left, name):
        count += b - a
        changed += sum(x != y for x, y in zip(recipient[a:b], donor[a:b]))
        output[a:b] = donor[a:b]
    result = bytes(output)
    require(layout(result, n) == left, 'splice damaged layout')
    return result, {'selector': name, 'selected_bytes': count, 'changed_bytes': changed,
                    'recipient_sha256': digest(recipient), 'donor_sha256': digest(donor),
                    'mixed_sha256': digest(result), 'metadata_unchanged': True,
                    'value_layout': 'feature-major' if left['v_transposed'] else 'token-major'}


def endpoint(value: dict) -> dict:
    keys = ('ids', 'eog', 'length', 'terminal_id', 'stop_reason', 'cap')
    return {key: value[key] for key in keys}


def first_difference(left: list, right: list):
    return next((i for i, (a, b) in enumerate(zip(left, right)) if a != b),
                min(len(left), len(right)) if len(left) != len(right) else None)


def classify(actual: dict, recipient: dict, full_cross: dict, changed: int) -> str:
    if actual == recipient:
        return 'STRUCTURAL_NULL' if changed == 0 else 'VALID_ENDPOINT_NULL'
    return 'DONOR_ENDPOINT_REPRODUCED' if actual == full_cross else 'VALID_ALTERNATIVE_TRAJECTORY'


def store_payload(out: Path, data: bytes, suffix: str) -> dict:
    rel = 'payloads/' + digest(data) + suffix
    path = out / 'baseline/pr99' / rel
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream: stream.write(data)
    require(file_hash(path) == digest(data), 'existing CAS object changed')
    return {'path': rel, 'bytes': len(data), 'sha256': digest(data)}


def prepare(baseline: Path, out: Path, seed: int = 20261014) -> None:
    baseline, out = baseline.resolve(), out.resolve()
    require(not out.exists() and not out.is_relative_to(baseline), 'use a new output directory outside the inherited archive')
    for name, expected in SOURCE_BLOBS.items():
        body = (baseline / name).read_bytes()
        blob = hashlib.sha1(b'blob ' + str(len(body)).encode() + b'\0' + body).hexdigest()
        require(blob == expected, 'PR101 source mismatch: ' + name)
    old_donors = read(baseline / 'DONORS.json')
    cases = {x['id']: x for x in read(baseline / 'INPUTS.json')['cases']}
    inherited = {x['task']: x['full_cells'] for x in read(baseline / 'KV_LOGITS_CROSS.json')['rows']}
    require(all(key in cases and key in inherited for key in CASES), 'missing frozen case')
    out.mkdir(parents=True)
    for name in ('payloads', 'operator_payloads', 'records', 'raw'): (out / name).mkdir()
    donors, requests, reconstruction, expected = {}, [], [], {}
    rng = random.Random(seed)
    for task in CASES:
        n = len(cases[task]['prompt_ids'])
        expected[task] = {key: endpoint(value) for key, value in inherited[task].items()}
        require(all(key in expected[task] for key in ('AA', 'AB', 'BA', 'BB')), 'missing full state/logits cross')
        states = {}
        for side in ('A', 'B'):
            original = old_donors[task + '|' + side]
            state = checked_payload(baseline / 'baseline/pr99', original['KV'])
            logits = checked_payload(baseline / 'baseline/pr99', original['logits'])
            require(len(logits) == 128256 * 4 and all(math.isfinite(x[0]) for x in struct.iter_unpack('<f', logits)), 'invalid initial logits')
            description = layout(state, n)
            require(finite_kv(state, description), 'nonfinite source KV')
            states[side] = state
            donors[task + '|' + side] = {'KV': store_payload(out, state, '.seqkv.bin'),
                                      'logits': store_payload(out, logits, '.logits.f32')}
        for recipient in ('A', 'B'):
            donor = 'B' if recipient == 'A' else 'A'
            for selector in ('EMPTY', 'ALL', *SELECTORS):
                mixed, audit = splice(states[recipient], states[donor], n, selector)
                sham, _ = splice(states[recipient], states[recipient], n, selector)
                require(sham == states[recipient], 'own-source reconstruction not byte-identical')
                label = recipient + '-' + selector
                donors[task + '|' + label] = {'KV': store_payload(out, mixed, '.seqkv.bin')}
                reconstruction.append({'task': task, 'recipient': recipient, 'donor': donor,
                                       'own_source_sham_byte_equal': True, **audit})
                for repeat in range(2):
                    slot = {'task': task, 'recipient': recipient, 'donor': donor,
                            'selector': selector, 'repeat': repeat, 'restore_label': label,
                            'stage': 'control' if selector in ('EMPTY', 'ALL') else 'cross',
                            'audit': audit}
                    slot['id'] = digest(encoded({k: v for k, v in slot.items() if k != 'audit'}))[:24]
                    requests.append(slot)
    for stage in ('control', 'cross'):
        stage_rows = [x for x in requests if x['stage'] == stage]
        rng.shuffle(stage_rows)
        for index, row in enumerate(stage_rows): row['order'] = index
    arm = copy.deepcopy(read(baseline / 'PLAN.json')['arms']['A'])
    require(arm['ub'] == 512 and arm['capacity'] == 1 and not arm['spec'], 'wrong inherited receiver')
    plan = {'schema': 1, 'study': 'b570-kv-subset-v1', 'baseline_commit': BASELINE_COMMIT,
            'baseline': str(baseline), 'seed': seed, 'requests': requests, 'arms': {'A': arm},
            'cases': {key: cases[key] for key in CASES}, 'expected': expected,
            'limits': {'whole_requests': 192, 'owned_seconds': 21600},
            'primary_selectors': ['K_layer0', 'V_layer0', 'KV_layer0'],
            'claim_scope': 'Finite boundary-0 state-subset interventions, not projection-kernel mediation or natural reachability'}
    require(len(requests) == 192, 'unexpected request budget')
    write_new(out / 'PLAN.json', plan)
    write_new(out / 'DONORS.json', donors)
    write_new(out / 'RECONSTRUCTION.json', reconstruction)
    for name in ('COUNTER_SEMANTICS.json', 'ASSET_PREFLIGHT.json'):
        (out / name).write_bytes((baseline / name).read_bytes())
    runtime = [baseline / name for name in SOURCE_BLOBS]
    runtime += [p for p in (baseline / 'build/Release').iterdir() if p.suffix.lower() in ('.dll', '.exe')]
    runtime += [baseline / 'build/Release/COUNTER_HASH.txt']
    runtime += [Path(x['path']) for x in read(out / 'ASSET_PREFLIGHT.json')['models'] if x['role'] == 'target']
    runtime += list(Path(__file__).parent.glob('*.py'))
    bindings = [pin(p) for p in runtime]
    inputs = [pin(out / name) for name in ('PLAN.json', 'DONORS.json', 'COUNTER_SEMANTICS.json', 'ASSET_PREFLIGHT.json', 'RECONSTRUCTION.json')]
    write_new(out / 'FREEZE.json', {'schema': 1, 'created_utc': utc(), 'new_gpu_forwards': 0,
                                  'runtime': bindings, 'inputs': inputs})
    print('PREPARED: 32 control + 160 subset requests; no GPU inference. Commit FREEZE.json before run.')


def verify_freeze(out: Path, repo: Path, commit: str, registration: str) -> None:
    require(not sys.flags.optimize, 'legacy audited code must not run with python -O')
    require(len(commit) == 40 and all(c in '0123456789abcdef' for c in commit), 'full freeze commit required')
    frozen = subprocess.check_output(['git', 'show', f'{commit}:{registration}'], cwd=repo)
    require(frozen == (out / 'FREEZE.json').read_bytes(), 'registration bytes not in specified commit')
    remote = subprocess.check_output(['gh', 'api', 'repos/leecdiang/HeteroSpec/contents/' + registration + '?ref=' + commit, '-H', 'Accept: application/vnd.github.raw+json'], cwd=repo)
    require(remote == frozen, 'authenticated remote registration differs')
    value = read(out / 'FREEZE.json')
    for item in value['runtime'] + value['inputs']:
        path = Path(item['path'])
        require(path.stat().st_size == item['bytes'] and file_hash(path) == item['sha256'], 'frozen file changed: ' + str(path))


def load_auditor(baseline: Path):
    spec = importlib.util.spec_from_file_location('b570_inherited_verify100', baseline / 'code/verify100.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_record(out: Path, plan: dict, slot: dict, record: dict, auditor) -> dict:
    raw = checked_payload(out, {'path': record['raw_path'], 'bytes': (out / record['raw_path']).stat().st_size, 'sha256': record['raw_sha256']})
    value = json.loads(raw)
    case = plan['cases'][slot['task']]
    require(record['slot'] == slot['id'] and record['task'] == slot['task'], 'record coordinate mismatch')
    auditor.endpoint100(value, case['prompt_ids'], 512, record['owned_pid'], restored=True)
    trace = json.loads(checked_payload(out, {'path': record['evidence_path'], 'bytes': (out / record['evidence_path']).stat().st_size, 'sha256': record['evidence_sha256']}))
    auditor.geometry100(trace, value, case['prompt_ids'], 512, [])
    proof = value['restore100']
    donor = read(out / 'DONORS.json')[slot['task'] + '|' + slot['recipient']]
    require(proof['post_restore_KV_sha256'] == slot['audit']['mixed_sha256'], 'native imported KV differs from prescribed intervention')
    require(proof['post_restore_logits_sha256'] == donor['logits']['sha256'], 'receiver initial logits changed')
    require(proof['extra_forward_calls'] == 0 and proof['clean_context_and_scheduler'], 'receiver not clean/no-forward restore')
    require(proof['KV_min'] == 0 and proof['KV_max'] == len(case['prompt_ids']) - 1, 'KV position change')
    require(not trace['memory']['violation'], 'memory gate failed')
    for sample in trace['memory']['samples']:
        auditor.memory(sample, record['owned_pid'])
    return endpoint(value)


def run_stage(out: Path, repo: Path, commit: str, registration: str, stage: str) -> None:
    require(os.name == 'nt', 'GPU execution requires the PR101 Windows/B570 runtime')
    require(not os.environ.get('VK_INSTANCE_LAYERS'), 'unset Vulkan instrumentation layers for this study')
    verify_freeze(out, repo, commit, registration)
    plan = read(out / 'PLAN.json'); baseline = Path(plan['baseline'])
    if stage == 'cross':
        controls = analyze(out)
        require(controls['control_gate'] == 'PASS', 'all controls must pass before any subset cross')
    # Only new output/accounting bindings are replaced. Native identity, module,
    # memory, request and endpoint guards remain the audited PR101 implementation.
    sys.path.insert(0, str(baseline / 'code'))
    common = importlib.import_module('common98')
    module = importlib.import_module('controller100')
    module.ROOT = common.ROOT = out
    module.PLAN = plan
    module.EXE = baseline / 'build/Release/b570-boundary-worker.exe'
    module.TARGET = next(Path(x['path']) for x in read(out / 'ASSET_PREFLIGHT.json')['models'] if x['role'] == 'target')
    def source_gate():
        verify_freeze(out, repo, commit, registration)
        return commit
    module.source_gate = source_gate
    auditor = load_auditor(baseline)

    def charge(kind, slot_id):
        rows = module.rows()
        require(not any(x.get('slot') == slot_id and x['event'] == 'REQUEST_STARTED' for x in rows), 'started slots are immutable; no automatic retry')
        require(sum(x['event'] == 'REQUEST_STARTED' for x in rows) < 192, 'request cap')
        require(module.owned() < 21600 - 305, 'owned time budget')
        require(sum(p.stat().st_size for p in out.rglob('*') if p.is_file()) < 4 * 1024**3, '4 GiB study disk cap')
        common.event(event='REQUEST_STARTED', kind=kind, slot=slot_id)

    module.charge = charge
    lock = out / 'EXECUTION.lock'
    with lock.open('x') as stream: stream.write(str(os.getpid()))
    try:
        for slot in sorted((x for x in plan['requests'] if x['stage'] == stage), key=lambda x: x['order']):
            receipt = out / 'receipts' / (slot['id'] + '.json')
            if receipt.exists():
                previous = read(receipt)
                require(previous['status'] == 'COMPLETED', 'previous failure requires explicit new study, not retry')
                validate_record(out, plan, slot, previous['record'], auditor)
                continue
            block = {'name': slot['id'], 'phase': stage, 'arm': 'A', 'repeat': slot['repeat'],
                     'observation_mode': 'heavy', 'own_bind_sham': False}
            case = dict(plan['cases'][slot['task']], schedule=[], restore_donors=[slot['restore_label'], slot['recipient']])
            worker = None
            try:
                worker = module.Worker(block)
                record = worker.request(slot['id'], case)
                result = validate_record(out, plan, slot, record, auditor)
                write_new(receipt, {'status': 'COMPLETED', 'slot': slot, 'endpoint': result, 'record': record})
            except BaseException as error:
                if not receipt.exists(): write_new(receipt, {'status': 'FAILED', 'slot': slot, 'error': repr(error), 'utc': utc()})
                raise
            finally:
                if worker is not None: worker.close()
    finally:
        lock.unlink()
    result = analyze(out)
    write_new(out / ('ANALYSIS-' + stage + '.json'), result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def analyze(out: Path) -> dict:
    require(not sys.flags.optimize, 'legacy audit must not run with python -O')
    plan = read(out / 'PLAN.json')
    for name, expected in SOURCE_BLOBS.items():
        body = (Path(plan['baseline']) / name).read_bytes()
        require(hashlib.sha1(b'blob ' + str(len(body)).encode() + b'\0' + body).hexdigest() == expected, 'inherited audit/source changed: ' + name)
    auditor = load_auditor(Path(plan['baseline']))
    frozen = read(out / 'FREEZE.json')
    for item in frozen['inputs']:
        require(file_hash(Path(item['path'])) == item['sha256'], 'frozen input changed')
    donors = read(out / 'DONORS.json')
    checked_mixes = set()
    for slot in plan['requests']:
        mix_key = (slot['task'], slot['restore_label'])
        if mix_key in checked_mixes: continue
        checked_mixes.add(mix_key)
        n = len(plan['cases'][slot['task']]['prompt_ids'])
        a = donors[slot['task'] + '|' + slot['recipient']]['KV']
        b = donors[slot['task'] + '|' + slot['donor']]['KV']
        original = checked_payload(out / 'baseline/pr99', a)
        source = checked_payload(out / 'baseline/pr99', b)
        rebuilt, audit = splice(original, source, n, slot['selector'])
        require(audit == slot['audit'], 'prescribed splice audit mismatch')
        actual = checked_payload(out / 'baseline/pr99', donors[slot['task'] + '|' + slot['restore_label']]['KV'])
        require(actual == rebuilt, 'mixed bytes differ from frozen selection')
    rows, errors, missing = [], [], []
    for slot in plan['requests']:
        path = out / 'receipts' / (slot['id'] + '.json')
        if not path.exists(): missing.append(slot['id']); continue
        receipt = read(path)
        if receipt['status'] != 'COMPLETED': errors.append({'slot': slot['id'], 'error': receipt.get('error')}); continue
        try:
            require(receipt['slot'] == slot, 'slot receipt mismatch')
            actual = validate_record(out, plan, slot, receipt['record'], auditor)
            recipient, donor = slot['recipient'], slot['donor']
            target = plan['expected'][slot['task']]
            own = target[recipient + recipient]
            full = target[donor + recipient]
            expected_control = own if slot['selector'] == 'EMPTY' else full
            rows.append({'slot': slot['id'], 'task': slot['task'], 'selector': slot['selector'],
                         'recipient': recipient, 'repeat': slot['repeat'], 'stage': slot['stage'],
                         'endpoint_sha256': digest(encoded(actual)), 'changed_bytes': slot['audit']['changed_bytes'],
                         'control_pass': actual == expected_control if slot['stage'] == 'control' else None,
                         'classification': classify(actual, own, full, slot['audit']['changed_bytes']),
                         'first_difference_from_recipient': first_difference(actual['ids'], own['ids'])})
        except (ValueError, AssertionError, KeyError, OSError) as error:
            errors.append({'slot': slot['id'], 'error': repr(error)})
    controls = [r for r in rows if r['stage'] == 'control']
    passed = len(controls) == 32 and all(r['control_pass'] for r in controls)
    repeats = {}
    for row in rows:
        if row['stage'] == 'cross':
            key = '|'.join((row['task'], row['recipient'], row['selector']))
            repeats.setdefault(key, []).append(row['endpoint_sha256'])
    repeatable = len(repeats) == 80 and all(len(v) == 2 and v[0] == v[1] for v in repeats.values())
    complete = passed and len(rows) == 192 and not errors and not missing and repeatable
    return {'status': 'COMPLETE_FINITE_STATE_INTERVENTIONS' if complete else 'PENDING_OR_BLOCKED',
            'control_gate': 'PASS' if passed else 'BLOCKED', 'complete_repeatability': repeatable,
            'valid_rows': len(rows), 'missing_slots': missing, 'errors': errors, 'rows': rows,
            'projection_kernel_mediation': 'NOT_ESTABLISHED',
            'mixed_state_natural_reachability': 'NOT_ESTABLISHED',
            'zero_or_partial_effect_is_valid_result': True, 'paper_or_release_authorized': False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--baseline', type=Path, required=True); prep.add_argument('--out', type=Path, required=True)
    prep.add_argument('--seed', type=int, default=20261014)
    run = commands.add_parser('run')
    run.add_argument('--out', type=Path, required=True); run.add_argument('--repo', type=Path, required=True)
    run.add_argument('--freeze-commit', required=True); run.add_argument('--registration', required=True)
    run.add_argument('--stage', choices=('control', 'cross'), required=True)
    analysis = commands.add_parser('analyze'); analysis.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'prepare': prepare(args.baseline, args.out, args.seed)
    elif args.command == 'run': run_stage(args.out.resolve(), args.repo, args.freeze_commit, args.registration, args.stage)
    else: print(json.dumps(analyze(args.out.resolve()), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
