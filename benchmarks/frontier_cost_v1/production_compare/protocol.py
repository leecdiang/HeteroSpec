"""Finite original-entry preparation; this schema never admits a speedup claim."""
from collections import Counter
import hashlib
import json
from pathlib import Path

PUBLIC_COMMIT = 'd6053addcd973e503ebeaae495b3326d6bf99bd4'
JOB_MANIFEST_SHA = '067ebcface1d5c4ac8ca816892c07f1d81551ed41c97fd09d11c07061f631401'
TARGET_SHA = '408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6'
DRAFT_SHA = '9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031'
WORKER_SHA = '05e395aa3082b08229946139c1f0d298bfc1c3064f001ba5c10aefcc9487eecb'
ENTRY_SHA = 'bf301356f7707a3af3327e71102f20834c5b81ee1bcceee4b2879222b96ccae2'
HELPER_SHA = '8602ac1e2ad93972d36ff8fc3f7dca5e16c0a8385ac058bd1b367331f6c2f62f'
HOST_RUNNER_SHA = 'd10df8f66e5d2a31301445037b0bc8f3c5135e5086b29074e06cd38949299a8f'
INPUTS_CANONICAL_SHA = '83ece672eb2cd73eadbdff4c4895bf6a4f7d2f7178fb246d9922848860d8bcfc'
CAP = 16
K = 7
VOCAB = 151936
PROCESS_SECONDS = 1800
PROMPT_SHA = ['2d0b8c32dc9f1df44525f5b25ec0140877c8eac6a8142d90d0ff0dc81846b2c4',
              '46d5fb4d5d6c9428f19f579d394f716d332ca3c699bf8d23ffb430dc962dc1cc']
ORDER = [('capture-eager', 0, True), ('capture-deferred', 1, True),
         ('clean-r0-eager', 0, False), ('clean-r0-deferred', 1, False),
         ('clean-r1-deferred', 1, False), ('clean-r1-eager', 0, False)]


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def identity(path):
    path = Path(path).resolve()
    return {'bytes': path.stat().st_size, 'sha256': digest(path)}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def write_new(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def histogram(length, width):
    result = Counter({str(width): length // width})
    if length % width:
        result[str(length % width)] += 1
    return +result


def validate_inputs(data):
    if hashlib.sha256(canonical(data)).hexdigest() != INPUTS_CANONICAL_SHA:
        raise ValueError('Frozen full-prompt input document changed')
    if data.get('schema') != 'heterospec.production-pair-inputs.v1':
        raise ValueError('Unknown input schema')
    if data.get('source_manifest_sha256') != JOB_MANIFEST_SHA:
        raise ValueError('Original full-prompt provenance absent')
    if data.get('target_sha256') != TARGET_SHA or data.get('draft_sha256') != DRAFT_SHA:
        raise ValueError('Actual Qwen target/draft identities required; fixtures are not admitted')
    cases = data['inputs']
    if len(cases) != 2 or [case['name'] for case in cases] != ['diagnostic-0', 'diagnostic-1']:
        raise ValueError('Exactly two fixed input names required')
    if [case['original_id'] for case in cases] != ['APPS/train/169', 'APPS/train/199']:
        raise ValueError('Frozen lexicographic full-prompt selection differs')
    for index, case in enumerate(cases):
        tokens = case['prompt_ids']
        if not isinstance(tokens, list) or not 1 <= len(tokens) <= 512:
            raise ValueError('Bounded nonempty full prompt required')
        if any(type(token) is not int or not 0 <= token < VOCAB for token in tokens):
            raise ValueError('Token ID out of authenticated vocabulary')
        if case['cap'] != CAP or case['original_cap'] != 96 or case['k'] != K:
            raise ValueError('The cap16/k7 diagnostic is immutable')
        if hashlib.sha256(canonical(tokens)).hexdigest() != case['prompt_sha256'] or case['prompt_sha256'] != PROMPT_SHA[index]:
            raise ValueError('Prompt content binding differs')
    return cases


def ceiling(case):
    p = len(case['prompt_ids'])
    cycles = CAP - 1
    return {'requests': 1, 'cycles': cycles,
            'target_decode_calls': (p + 31) // 32 + cycles,
            'draft_decode_calls': 1 + (K + 1) * cycles,
            'target_physical_microbatches': (p + 31) // 32 + cycles,
            'draft_physical_microbatches': (p + 3) // 4 + (K + 1) * cycles,
            'target_rows': p + (K + 1) * cycles,
            'draft_rows': p + (K + 1) * cycles}


def storage_ceiling(cases):
    # Qwen3 native structures are pinned by the original full-GGUF identities.
    # Allow 1 MiB for sequence metadata in addition to the F16 K/V payload.
    sidecar = total = 0
    per_request = []
    for case in cases:
        rows = len(case['prompt_ids']) + CAP + K + 1
        target = rows * 36 * (1024 + 1024) * 2 + 1024**2
        draft = rows * 28 * (1024 + 1024) * 2 + 1024**2
        c = CAP - 1
        own = (c + 2) * target + (2 * c + 2) * draft + 16 * 1024**2
        entire = own + (c + 2) * target + (3 + (2 * K + 2) * c) * VOCAB * 4 + 16 * 1024**2
        sidecar += own
        total += entire
        per_request.append({'name': case['name'], 'maximum_active_rows': rows,
                            'target_state_bytes_ceiling': target, 'draft_state_bytes_ceiling': draft})
    return {'sidecar_bytes_per_process': sidecar, 'all_capture_bytes_per_process': total,
            'minimum_free_disk_bytes': 2 * total + 4 * 64 * 1024**2,
            'metadata_allowance_bytes_per_state': 1024**2,
            'model_structure_binding': {'target': {'layers': 36, 'K_elements': 1024, 'V_elements': 1024},
                                        'draft': {'layers': 28, 'K_elements': 1024, 'V_elements': 1024}},
            'requests': per_request}


def make_plan(data):
    cases = validate_inputs(data)
    per_process = Counter()
    for case in cases:
        per_process.update(ceiling(case))
    jobs = [{'name': name, 'deferred': mode, 'capture': capture,
             'binary': ('capture_' if capture else 'clean_') + str(mode),
             'request_names': [case['name'] for case in cases],
             'context_creation_ceiling': 2, 'model_load_ceiling': 2,
             'work_ceiling': dict(per_process)} for name, mode, capture in ORDER]
    return {'schema': 'heterospec.production-pair-plan.v1',
            'purpose': 'Original-entry preparation and instrumented diagnostic qualification only',
            'public_dependency_commit': PUBLIC_COMMIT,
            'inputs_sha256': hashlib.sha256(canonical(data)).hexdigest(),
            'jobs': jobs, 'processes': len(jobs), 'request_ceiling': 12,
            'context_creation_ceiling': 12, 'model_load_ceiling': 12,
            'work_ceiling': {key: value * len(jobs) for key, value in per_process.items()},
            'process_seconds': PROCESS_SECONDS,
            'capture_storage_ceiling': storage_ceiling(cases),
            'historical_R_bridge': 'OPEN_NOT_PROVIDED',
            'clean_full_vector_state_bridge': 'OPEN_NOT_OBSERVABLE_AT_THIS_ENTRY',
            'performance_admitted': False,
            'service_scope': 'Original worker service_seconds; excludes model/pool load, result-file I/O, text tokenization, networking and queueing.',
            'early_stop': 'Any malformed, incomplete, unexpected, over-budget or unequal capture result stops later jobs. No retries or replacement roots.'}


def actual_work(receipt, case, mode):
    """Independent successful-request accounting from literal cycle decisions."""
    p = len(case['prompt_ids'])
    cycles = receipt['cycles']
    if len(cycles) > CAP - 1:
        raise ValueError('Cycle ceiling exceeded')
    if any(type(cycle['accepted']) is not int or not 0 <= cycle['accepted'] <= K for cycle in cycles):
        raise ValueError('Invalid accepted count')
    for field in ('target_calls','draft_calls','draft_tail_skipped','draft_tail_recovered'):
        if type(receipt[field]) is not int or receipt[field] < 0:
            raise ValueError('Invalid native integer counter')
    for field in ('target_physical_width_hist','draft_physical_width_hist'):
        if any(type(value) is not int or value <= 0 for value in receipt[field].values()):
            raise ValueError('Invalid physical width counter')
    recoveries = sum(cycle['accepted'] == K for cycle in cycles)
    skips = len(cycles) - recoveries
    draft_steps = (K + 1) * len(cycles) if mode == 0 else K * len(cycles) + recoveries
    target_hist = histogram(p, 32)
    target_hist[str(K + 1)] += len(cycles)
    draft_hist = histogram(p, 4)
    draft_hist['1'] += draft_steps
    expected = {'target_decode_calls': (p + 31) // 32 + len(cycles),
                'draft_decode_calls': 1 + draft_steps,
                'target_physical_microbatches': sum(target_hist.values()),
                'draft_physical_microbatches': sum(draft_hist.values()),
                'target_rows': p + (K + 1) * len(cycles), 'draft_rows': p + draft_steps}
    if receipt['target_calls'] != expected['target_decode_calls'] or receipt['draft_calls'] != expected['draft_decode_calls']:
        raise ValueError('Decode-call accounting differs from the literal request')
    if Counter(receipt['target_physical_width_hist']) != +target_hist or Counter(receipt['draft_physical_width_hist']) != +draft_hist:
        raise ValueError('Observed physical prefill/verification widths differ')
    if receipt['draft_tail_skipped'] != (skips if mode else 0) or receipt['draft_tail_recovered'] != (recoveries if mode else 0):
        raise ValueError('Deferred materialization accounting differs')
    return expected
