"""Prospective work and worker schedules. This module never launches a model."""
from __future__ import annotations
import argparse
import hashlib
import json
import random
import re
from pathlib import Path

SEED = 2026110601
FACTOR = ('W_L4', 'W_P', 'L_L4', 'L_P')
BURST = ('W_M_TARGET_ONLY', 'L_M_TARGET_ONLY', 'L_M_MATCHED', 'L_D4')
WILLIAMS = ((0, 1, 3, 2), (1, 2, 0, 3), (2, 3, 1, 0), (3, 0, 2, 1))
ROOT_FIELDS = {'root', 'content_sha256', 'domain', 'prompt_tokens'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def seed_for(*parts):
    return int.from_bytes(hashlib.sha256('|'.join(map(str, (SEED,) + parts)).encode()).digest()[:8], 'little')


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf8', newline='\n') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def validate_roots(rows, count=16):
    require(isinstance(rows, list) and len(rows) == count, f'Expected {count} roots')
    names, texts = set(), set()
    for row in rows:
        require(set(row) == ROOT_FIELDS, 'Only input identity, domain and native token length are accepted')
        require(isinstance(row['root'], str) and row['root'].strip() and row['root'] not in names, 'Empty/duplicate root')
        h = row['content_sha256']
        require(isinstance(h, str) and re.fullmatch('[0-9a-f]{64}', h) is not None and h not in texts, 'Invalid/duplicate text hash')
        require(row['domain'] in ('math', 'code'), 'Unknown domain')
        require(type(row['prompt_tokens']) is int and 1 <= row['prompt_tokens'] <= 896, 'C1024/cap128 token admission failed')
        names.add(row['root']); texts.add(h)
    require(sum(r['domain'] == 'math' for r in rows) == count // 2, 'Balanced math/code roots required')
    return rows


def panel(candidates, exposed_roots, exposed_hashes):
    """Rank input identities, then admit length; do not pass outcomes to this API.

    Tokenization is offline. Freeze source order/exclusions before candidate forwards.
    The executing host records every rejected identity and reason.
    """
    require(isinstance(candidates, list), 'Candidate list required')
    for row in candidates:
        require(set(row) == ROOT_FIELDS, 'Outcome fields are forbidden')
        require(isinstance(row['root'], str) and row['root'].strip(), 'Invalid root')
        require(isinstance(row['content_sha256'], str) and re.fullmatch('[0-9a-f]{64}', row['content_sha256']) is not None, 'Invalid hash')
        require(row['domain'] in ('math', 'code') and type(row['prompt_tokens']) is int, 'Invalid native input metadata')
    ordered = sorted(candidates, key=lambda r: (hashlib.sha256(f"{SEED}|{r['root']}|{r['content_sha256']}".encode()).hexdigest(), r['root']))
    used_roots, used_hashes = set(exposed_roots), set(exposed_hashes)
    chosen, rejected = [], []
    counts = {'math': 0, 'code': 0}
    for row in ordered:
        reason = None
        if row['root'] in used_roots or row['content_sha256'] in used_hashes:
            reason = 'EXPOSED_OR_DUPLICATE'
        elif not 1 <= row['prompt_tokens'] <= 896:
            reason = 'TOKEN_CAPACITY'
        elif counts[row['domain']] >= 8:
            reason = 'DOMAIN_QUOTA'
        if reason:
            rejected.append(dict(row, reason=reason)); continue
        used_roots.add(row['root']); used_hashes.add(row['content_sha256'])
        counts[row['domain']] += 1; chosen.append(row)
    validate_roots(chosen)
    return {'selected': chosen, 'not_selected': rejected, 'status': 'INPUT_SELECTION_ONLY', 'seed': SEED}


def stamp(jobs):
    for index, row in enumerate(jobs):
        row['slot_id'] = f"{row['stage']}-{index:05d}"
        row['status'] = 'PLANNED_NOT_RUN'
    return jobs


def structural(platform):
    require(platform in ('rtx', 'b570'), 'Unknown platform')
    jobs = []
    families = ('Qwen', 'Smol') if platform == 'rtx' else ('Smol',)
    caps = ((1024, 768),) if platform == 'rtx' else ((1024, 768), (4096, 3072))
    widths = (4, 8, 32) if platform == 'rtx' else (2, 4, 32)
    arms = FACTOR if platform == 'rtx' else ('REFERENCE_CONTINUATION', 'SIMPLE', 'LOCAL')
    repeats = 2 if platform == 'rtx' else 3
    for family in families:
        for capacity, boundary in caps:
            for width in widths:
                for relation in ('inside', 'crossing'):
                    head = boundary - (width if relation == 'inside' else 1)
                    cell = f'{family}-C{capacity}-q{width}-{relation}'
                    for repetition in range(repeats):
                        # Randomized cyclic order; the three-arm case is a Latin
                        # rotation, NOT a six-sequence Williams crossover.
                        order = list(arms); random.Random(seed_for(platform, cell)).shuffle(order)
                        order = order[repetition:] + order[:repetition]
                        for position, arm in enumerate(order):
                            for kind in ('warmup', 'measurement'):
                                jobs.append(dict(stage='R1_STRUCT' if platform == 'rtx' else 'B1_STRUCT', family=family, root=cell,
                                    capacity=capacity, boundary=boundary, head=head, width=width, relation=relation,
                                    requested_outputs='all' if platform == 'b570' and width <= 4 else 'last',
                                    arm=arm, session=repetition, arm_position=position, kind=kind,
                                    restore_before_each=True, window='append_after_valid_state'))
    return stamp(jobs)


def natural(cohorts):
    require(set(cohorts) == {'Qwen', 'Smol'}, 'R1 requires both named cohorts')
    jobs = []
    for family in ('Qwen', 'Smol'):
        roots = validate_roots(cohorts[family])
        for session in range(4):
            order = list(range(16)); random.Random(seed_for('natural', family, session)).shuffle(order)
            for i in order:
                for position, arm_index in enumerate(WILLIAMS[(session + i) % 4]):
                    for kind in ('warmup', 'measurement'):
                        jobs.append(dict(stage='R1_NATURAL', family=family, root=roots[i]['root'], root_index=i,
                            content_sha256=roots[i]['content_sha256'], arm=FACTOR[arm_index], session=session,
                            arm_position=position, kind=kind, window='complete_resident_service'))
    return stamp(jobs)


def burst(roots, primers):
    roots = validate_roots(roots)
    require(isinstance(primers, list) and len(primers) == 2 and len(set(primers)) == 2, 'Two distinct exposed primer IDs required')
    require(all(isinstance(p, str) and p.strip() for p in primers), 'Invalid primer ID')
    require(not set(primers) & {r['root'] for r in roots}, 'Primers must not overlap test roots')
    workers = []
    for session in range(4):
        order = list(range(16)); random.Random(seed_for('burst', session)).shuffle(order)
        for position, ai in enumerate(WILLIAMS[session]):
            arm = BURST[ai]
            requests = [dict(root=p, kind='primer') for p in primers]
            requests += [dict(roots[i], kind='measurement', root_index=i) for i in order]
            workers.append(dict(stage='R2_BURST', family='Qwen', worker_id=f'R2-s{session}-{arm}', session=session,
                arm=arm, arm_position=position, residency='matched' if arm in ('L_M_MATCHED', 'L_D4') else 'target_only',
                draft=arm == 'L_D4', draft_width=4 if arm == 'L_D4' else 1,
                requests=requests, reset_each_request=True, load_once=True, status='PLANNED_NOT_RUN'))
    return workers


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('task', choices=['rtx-struct', 'b570-struct', 'natural', 'burst'])
    p.add_argument('--inputs', type=Path); p.add_argument('--primers', nargs=2)
    p.add_argument('--out', type=Path, required=True); a = p.parse_args()
    if a.task.endswith('-struct'):
        result = structural(a.task.split('-')[0])
    else:
        require(a.inputs is not None, '--inputs required')
        data = json.loads(a.inputs.read_text(encoding='utf8'))
        result = natural(data) if a.task == 'natural' else burst(data['Qwen'], a.primers)
    write_new(a.out, result)
    print(json.dumps({'status': 'SCHEDULE_ONLY_NOT_EXECUTED', 'entries': len(result)}))

if __name__ == '__main__':
    main()
