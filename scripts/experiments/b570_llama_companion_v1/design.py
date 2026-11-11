"""Fixed natural controls, balanced timing, and prospective panel selection."""
from collections import Counter
import hashlib
from common import digest, input_check, need

ARMS = ('R', 'M_PQ', 'M_QB', 'C_PQ', 'C_QB')
TIMING = ('R', 'M_PQ', 'M_QB', 'C_PQ_A', 'C_PQ_B', 'C_QB')
WILLIAMS = (0, 1, 5, 2, 4, 3)


def slot(x, arm, observer, stage, label, session=None):
    input_check(x)
    return {'id': label, 'input': x, 'arm': 'C_PQ' if arm.startswith('C_PQ') else arm,
            'label': arm, 'observer': observer, 'stage': stage, 'session': session,
            'probe_cycle': -1, 'trace': False}


def baseline(panel):
    out = []
    for i, x in enumerate(panel):
        for arm in ARMS:
            for obs in ('off', 'heavy'):
                out.append(slot(x, arm, obs, 'development', f'baseline/i{i}/{arm}/{obs}'))
    return out


def references(panel):
    return [slot(x, 'R', o, 'reference', f'reference/i{i}/{o}')
            for i, x in enumerate(panel) for o in ('off', 'heavy')]


def qualification(panel):
    return [slot(x, a, o, 'qualification', f'qual/i{i}/{a}/{o}')
            for i, x in enumerate(panel) for a in ARMS for o in ('off', 'heavy')]


def timing(panel, session):
    need(type(session) is int and 0 <= session < 6, 'six Williams periods')
    order = sorted(range(len(panel)), key=lambda i: digest(['b570-llama-v1', session, panel[i]['id']]))
    rows = []
    for i in order:
        shift = (int(digest(panel[i]['id'])[:8], 16) + session) % 6
        for n in WILLIAMS:
            arm = TIMING[(n + shift) % 6]
            for stage in ('warmup', 'measured'):
                rows.append(slot(panel[i], arm, 'off', stage, f'timing/s{session}/i{i}/{arm}/{stage}', session))
    return rows


def timing_balance(panel):
    for x in panel:
        seqs = [[s['label'] for s in timing(panel, k) if s['input']['id'] == x['id'] and s['stage'] == 'measured'] for k in range(6)]
        positions = Counter((a, i) for seq in seqs for i, a in enumerate(seq))
        pairs = Counter((a, b) for seq in seqs for a, b in zip(seq, seq[1:]))
        need(len(positions) == 36 and set(positions.values()) == {1}, 'position imbalance')
        need(len(pairs) == 30 and set(pairs.values()) == {1}, 'within-block ordered carryover imbalance')
        need(sum(seq.index('C_PQ_A') < seq.index('C_PQ_B') for seq in seqs) == 3, 'AA order imbalance')
    return True


def select(pool, exposed, count=24):
    need(count in (12, 24), 'count fixed prospectively to 12 or 24')
    excluded = {digest(v) for v in exposed}
    buckets = {(domain, band): [] for domain in ('code', 'math') for band in ('short', 'long')}
    seen = set()
    for x in pool:
        input_check(x)
        n = len(x['prompt_ids'])
        band = 'short' if 128 <= n <= 384 else 'long' if 512 <= n <= 768 else None
        if band is None or x.get('domain') not in ('code', 'math'):
            continue
        need(bool(x.get('source_revision')) and bool(x.get('text_sha256')), 'provenance fields missing')
        keys = [x['id'], x['text_sha256'], digest(x['prompt_ids'])]
        if any(digest(k) in excluded for k in keys) or keys[-1] in seen:
            continue
        seen.add(keys[-1])
        buckets[x['domain'], band].append(x)
    panel = []
    for key, candidates in sorted(buckets.items()):
        candidates.sort(key=lambda x: digest(['b570-unseen-v1', x['id'], x['text_sha256']]))
        need(len(candidates) >= count // 4, 'insufficient natural stratum; amend before outputs, never pad/truncate')
        panel += candidates[:count // 4]
    return panel


def compatible_contract(a, b):
    """Output agreement across GPUs is not a requirement. Raw state is not portable."""
    shared = ('target_sha256', 'draft_sha256', 'vocabulary_sha256', 'template_sha256',
              'n_ctx', 'kv_dtype', 'k', 'cap', 'greedy', 'panel_sha256')
    return {'same_model_request_contract': all(a.get(k) is not None and a.get(k) == b.get(k) for k in shared),
            'differences': {k: [a.get(k), b.get(k)] for k in shared if a.get(k) != b.get(k)},
            'execution_differences': {k: [a.get(k), b.get(k)] for k in ('source', 'backend', 'threads', 'target_gpu_layers', 'draft_gpu_layers') if a.get(k) != b.get(k)},
            'requires_CUDA_Vulkan_reference_equality': False,
            'opaque_checkpoint_transfer_allowed': False}
