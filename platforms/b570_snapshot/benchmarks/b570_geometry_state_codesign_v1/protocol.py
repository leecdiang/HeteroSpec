"""CPU-only study specification. Does not load models or launch a native process."""
from __future__ import annotations
import argparse
import dataclasses
import hashlib
import json
import math
import random
from pathlib import Path
from typing import Any

STUDY = 'b570-geometry-state-codesign-v1'
BASE_MAIN = 'f5b7b8e9a6d02b228cb0e7b7b3932e89327cfb63'
DOMAINS = ('code', 'math')
BINS = ((64, 127), (128, 255), (256, 512))
SENTINELS = ('GSM8K/test/1248', 'GSM8K/test/831', 'GSM8K/test/1011', 'GSM8K/test/1249')
VOCAB = 128256
EOG = {128001, 128008, 128009}


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def encode(obj: Any) -> bytes:
    return (json.dumps(obj, sort_keys=True, ensure_ascii=False, allow_nan=False,
                       separators=(',', ':')) + '\n').encode('utf-8')


def digest(obj: Any) -> str:
    return hashlib.sha256(encode(obj)).hexdigest()


def file_sha(path: Path) -> str:
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def read_json(path: Path) -> Any:
    def unique(pairs):
        out = {}
        for k, v in pairs:
            require(k not in out, f'duplicate JSON key: {k}')
            out[k] = v
        return out
    return json.loads(path.read_text(encoding='utf-8-sig'), object_pairs_hook=unique,
                      parse_constant=lambda s: (_ for _ in ()).throw(ValueError('nonfinite JSON: ' + s)))


def write_new(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as f:
        f.write(encode(obj))


def valid_hash(h: Any) -> bool:
    return isinstance(h, str) and len(h) == 64 and all(c in '0123456789abcdef' for c in h)


@dataclasses.dataclass(frozen=True)
class Recipe:
    name: str
    producer: str
    continuation: str
    draft: bool
    runtime: str = 'new'
    capacity: int = 4
    k: int = 1

    def as_dict(self) -> dict:
        return dataclasses.asdict(self)


RECIPES = (
    Recipe('R', 'reference128', 'ordinary', False, runtime='old', capacity=1, k=0),
    Recipe('M_B_QB', 'bulk512', 'QB', False, k=0),
    Recipe('M_R_QB', 'reference128', 'QB', False, k=0),
    Recipe('C_B_MQ', 'bulk512', 'MQ', True),
    Recipe('C_B_PQ', 'bulk512', 'PQ', True),
    Recipe('C_B_QB', 'bulk512', 'QB', True),
    Recipe('C_R_MQ', 'reference128', 'MQ', True),
    Recipe('C_R_PQ', 'reference128', 'PQ', True),
    Recipe('C_R_QB', 'reference128', 'QB', True),
)
REFERENCE_SHADOW = Recipe('R_SHADOW', 'reference128', 'ordinary', False, runtime='new', capacity=1, k=0)
BY_NAME = {r.name: r for r in RECIPES + (REFERENCE_SHADOW,)}


def prompt_hash(ids: list[int]) -> str:
    return digest(ids)


def length_bin(n: int) -> int:
    for i, (lo, hi) in enumerate(BINS):
        if lo <= n <= hi:
            return i
    raise ValueError('prompt length outside declared bins')


def validate_case(case: dict) -> None:
    allowed = {'id', 'domain', 'prompt_ids', 'tokenizer_sha256', 'template_sha256', 'source_sha256'}
    require(set(case) == allowed, 'normalized input fields differ; no output/latency fields allowed')
    require(isinstance(case['id'], str) and case['id'], 'invalid input identity')
    require(case['domain'] in DOMAINS, 'unknown workload domain')
    ids = case['prompt_ids']
    require(isinstance(ids, list) and 64 <= len(ids) <= 512, 'prompt length outside64..512')
    require(all(type(i) is int and 0 <= i < VOCAB for i in ids), 'invalid direct token ID')
    for k in ('tokenizer_sha256', 'template_sha256', 'source_sha256'):
        require(valid_hash(case[k]), 'missing source/tokenizer/template binding: ' + k)


def select_holdout(inventory: list[dict], exposure: dict, seed: str = '20261015-v1') -> dict:
    """Only metadata/direct IDs are used. Exposure completeness is a host review duty."""
    require(set(exposure) == {'ids', 'prompt_sha256', 'scope_manifest_sha256', 'review_complete'}, 'exposure schema')
    require(exposure['review_complete'] is True, 'EXPOSURE_NOT_ESTABLISHED')
    require(valid_hash(exposure['scope_manifest_sha256']), 'missing reviewed exposure source manifest')
    require(all(valid_hash(h) for h in exposure['prompt_sha256']), 'bad exposure hash')
    seen_ids, seen_prompts = set(), set()
    buckets = {(d, b): [] for d in DOMAINS for b in range(3)}
    excluded = []
    ordered = sorted(inventory, key=lambda c: c.get('id', ''))
    for c in ordered:
        validate_case(c)
        require(c['id'] not in seen_ids, 'duplicate inventory ID')
        seen_ids.add(c['id']); ph = prompt_hash(c['prompt_ids'])
        if c['id'] in exposure['ids'] or ph in exposure['prompt_sha256']:
            excluded.append({'id': c['id'], 'reason': 'EXPOSED'}); continue
        if ph in seen_prompts:
            excluded.append({'id': c['id'], 'reason': 'DUPLICATE_PROMPT'}); continue
        seen_prompts.add(ph)
        rank = hashlib.sha256((seed + '\0' + c['id'] + '\0' + ph).encode()).hexdigest()
        buckets[c['domain'], length_bin(len(c['prompt_ids']))].append((rank, c))
    panel = []
    for key in buckets:
        values = sorted(buckets[key], key=lambda x: x[0])
        require(len(values) >= 4, 'INSUFFICIENT_INPUTS_IN_STRATUM:' + str(key))
        panel.extend(c for _, c in values[:4])
    require(len({c['tokenizer_sha256'] for c in panel}) == 1, 'mixed tokenizers')
    return {'panel': panel, 'excluded': excluded, 'seed': seed,
            'selection_uses_model_outputs': False,
            'exposure_manifest_sha256': exposure['scope_manifest_sha256'],
            'claim_scope': 'unseen relative to the reviewed complete exposure inventory, not training-data novelty'}


def plan_prefill(n: int, producer: str) -> dict:
    require(type(n) is int and 64 <= n <= 512, 'invalid prompt extent')
    require(producer in ('reference128', 'bulk512'), 'unknown producer')
    # New candidates submit one API caller. Original R inherits its actual old caller policy.
    width = 128 if producer == 'reference128' else 512
    widths = [min(width, n - i) for i in range(0, n, width)]
    return {'caller_lengths': [n], 'ubatch': width, 'expected_micrograph_widths': widths,
            'final_absolute_logits_position': n-1,
            'intermediate_logits_requested': False,
            'scope': 'planned physical partition; actual trace must validate it'}


def recipe_request(case: dict, recipe: Recipe, mode: str) -> dict:
    validate_case(case)
    require(mode in ('counts', 'diagnostic'), 'unknown observation channel')
    require(recipe == BY_NAME.get(recipe.name), 'changed recipe declaration')
    n = len(case['prompt_ids'])
    return {
        'study': STUDY, 'task': case['id'], 'prompt_ids': case['prompt_ids'],
        'prompt_sha256': prompt_hash(case['prompt_ids']), 'recipe': recipe.as_dict(),
        'producer_plan': plan_prefill(n, recipe.producer),
        'reference_caller_policy': 'INHERIT_FROZEN_ORIGINAL' if recipe.name=='R' else 'DECLARED_SINGLE_CALLER',
        'target_prefill_attention': 'MQ',
        'continuation_ubatch': 128 if recipe.name in ('R', 'R_SHADOW') else 4,
        'target_output_capacity': recipe.capacity, 'draft_prefill_policy': 'independent_ref128',
        'draft_continuation_ubatch': 1,
        'logical_batch': 512, 'context': 1024, 'threads': 10,
        'target': 'Meta-Llama-3.1-8B-Instruct-Q6_K.gguf',
        'draft': 'Llama-3.2-1B-Instruct-Q4_K_M.gguf' if recipe.draft else None,
        'kv_dtype': 'F16', 'flash_attention': False, 'sampler': 'native_greedy',
        'cap': 128, 'mode': mode, 'counts_off_phase_guard_required': True,
        'restore_external_state': False, 'teacher_forcing': False,
        'mid_request_policy_switch': False,
        'unapproved_backend_arithmetic_change': False,
    }


def build_plan(panel: list[dict], phase: str, seed: int = 20261015, selection: dict | None = None) -> dict:
    require(phase in ('pilot', 'confirm'), 'unknown phase')
    for c in panel: validate_case(c)
    require(len({c['id'] for c in panel}) == len(panel), 'duplicate input coordinate')
    require(len({prompt_hash(c['prompt_ids']) for c in panel}) == len(panel), 'duplicate prompt')
    require(len({c['tokenizer_sha256'] for c in panel}) == 1, 'mixed tokenizer')
    if phase == 'pilot':
        require(set(c['id'] for c in panel) == set(SENTINELS), 'pilot must retain all four sentinel inputs')
    else:
        require(len(panel) == 24, 'confirm requires24 unseen inputs')
        require(selection is not None and selection.get('panel')==panel and selection.get('selection_uses_model_outputs') is False
                and valid_hash(selection.get('exposure_manifest_sha256')), 'confirmation requires reviewed input-selection receipt')
        require(all(sum(c['domain'] == d and length_bin(len(c['prompt_ids'])) == b for c in panel) == 4
                    for d in DOMAINS for b in range(3)), 'unbalanced holdout strata')
    tasks = sorted(panel, key=lambda c: c['id']); random.Random(seed).shuffle(tasks)
    slots = []
    def append(c, r, session, mode, warmup=False, parent=None, stage=None):
        coordinate = {'study': STUDY, 'phase': phase, 'stage': stage or phase, 'task': c['id'],
                      'arm': r.name, 'session': session, 'mode': mode, 'warmup': warmup}
        s = dict(coordinate, slot=digest(coordinate)[:24], request=recipe_request(c, r, mode),
                 fresh_process=not warmup, process_parent=parent)
        # For confirmation the warmup and measured request share exactly one process;
        # assigned below. Both reset KV/pending/sampler before their own request.
        s['request_sha256'] = digest(s['request']); slots.append(s); return s
    if phase == 'pilot':
        # Statically enforce control precedence; do not leave reordering to the host.
        for rep in (0, 1):
            for c in tasks: append(c, BY_NAME['R'], rep, 'counts', stage='old_reference')
        for mode in ('counts', 'diagnostic'):
            for c in tasks:
                append(c, REFERENCE_SHADOW, 0, mode, stage='reference_shadow_'+mode)
        for mode in ('counts', 'diagnostic'):
            for j, c in enumerate(tasks):
                names=[r.name for r in RECIPES if r.name!='R']
                names=names[j%8:]+names[:j%8]
                if mode=='diagnostic': names=list(reversed(names))
                for name in names:
                    append(c, BY_NAME[name], 0, mode, stage='candidate_'+mode)
        for s in slots: s['process_group']=s['slot']
        budget = {'request_starts': 80, 'process_starts': 80, 'warmups': 0,
                  'owned_seconds': 7200, 'new_bytes': 4*1024**3}
    else:
        base = list(RECIPES); random.Random(seed+1).shuffle(base)
        for session in range(4):
            order = list(tasks); random.Random(seed+session+2).shuffle(order)
            for j, c in enumerate(order):
                rotation = (j+session) % len(base); arms = base[rotation:] + base[:rotation]
                if session % 2: arms = list(reversed(arms))
                for r in arms:
                    # Warmup is a separate start, deliberately uses the same direct prompt,
                    # with cache_prompt disabled and an independently verified fresh KV reset.
                    # It is not a new test input and is excluded from timing estimands.
                    warm = append(c, r, session, 'counts', True, stage='confirm')
                    measured = append(c, r, session, 'counts', False, warm['slot'], stage='confirm')
                    warm['process_group'] = measured['process_group'] = measured['slot']
                    warm['fresh_process'] = True; measured['fresh_process'] = False
        budget = {'request_starts': 1728, 'process_starts': 864, 'warmups': 864,
                  'owned_seconds': 43200, 'new_bytes': 8*1024**3}
    require(len(slots) == budget['request_starts'] and len({s['slot'] for s in slots}) == len(slots), 'budget/unique-slot error')
    return {'schema': 1, 'study': STUDY, 'phase': phase, 'seed': seed, 'panel': panel,
            'recipes': [r.as_dict() for r in RECIPES], 'slots': slots, 'budget': budget,
            'selection_receipt_sha256': digest(selection) if selection else None,
            'reference_is_original_runtime_in_all_confirmation_tasks': True,
            'native_ready': False, 'execution_f0': None,
            'host_gate': 'ISOLATED_NATIVE_INTEGRATION_AND_AUTHENTICATED_EXECUTION_F0_REQUIRED',
            'confirmation_requires_pilot_gate_and_author_go': True,
            'confirm_time_design': {'sessions': 4, 'date_blocks': 2,
                                    's1_after_s0_complete_seconds': 3600,
                                    's2_after_s0_start_seconds': 86400,
                                    's3_after_s2_complete_seconds': 3600},
            'no_hidden_starts_or_scientific_retry': True}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__); sub = p.add_subparsers(dest='cmd', required=True)
    sel = sub.add_parser('select'); sel.add_argument('--inventory', type=Path, required=True)
    sel.add_argument('--exposure', type=Path, required=True); sel.add_argument('--out', type=Path, required=True)
    bp = sub.add_parser('plan'); bp.add_argument('--panel', type=Path, required=True)
    bp.add_argument('--phase', choices=('pilot', 'confirm'), required=True); bp.add_argument('--out', type=Path, required=True)
    bp.add_argument('--selection', type=Path, help='required for confirm; exact receipt from select')
    args = p.parse_args()
    value = (select_holdout(read_json(args.inventory), read_json(args.exposure)) if args.cmd == 'select'
             else build_plan(read_json(args.panel), args.phase, selection=read_json(args.selection) if args.selection else None))
    write_new(args.out, value)
    print(json.dumps({'written': str(args.out), 'sha256': file_sha(args.out), 'native_started': 0}))

def validate_plan(plan: dict) -> None:
    require(plan.get('study')==STUDY and plan.get('schema')==1, 'unknown plan')
    slots=plan['slots']; expected=80 if plan['phase']=='pilot' else 1728
    require(len(slots)==expected and len({s['slot'] for s in slots})==expected, 'missing/duplicate slot')
    require(plan['budget']['request_starts']==expected,'budget changed')
    cases={c['id']:c for c in plan['panel']}
    for c in cases.values(): validate_case(c)
    require(len(cases)==(4 if plan['phase']=='pilot' else 24),'case count')
    groups={}
    for s in slots:
        coordinate={k:s[k] for k in ('study','phase','stage','task','arm','session','mode','warmup')}
        require(s['slot']==digest(coordinate)[:24],'slot identity changed')
        require(s['request']==recipe_request(cases[s['task']],BY_NAME[s['arm']],s['mode']),'request regenerated from wrong coordinate')
        require(digest(s['request'])==s['request_sha256'],'request digest changed')
        groups.setdefault(s['process_group'],[]).append(s)
    if plan['phase']=='pilot':
        expected_groups=[('old_reference',8),('reference_shadow_counts',4),('reference_shadow_diagnostic',4),('candidate_counts',32),('candidate_diagnostic',32)]
        stages=[name for name,n in expected_groups for _ in range(n)]
        require([s['stage'] for s in slots]==stages,'pilot control precedence changed')
        require(len(groups)==80 and all(len(g)==1 and g[0]['fresh_process'] for g in groups.values()),'pilot process binding')
    else:
        expected_coords={(c['id'],r.name,s) for c in plan['panel'] for r in RECIPES for s in range(4)}
        measured=[s for s in slots if not s['warmup']]
        require({(s['task'],s['arm'],s['session']) for s in measured}==expected_coords and len(measured)==864,'confirmation grid changed')
        require(len(groups)==864,'confirmation process count')
        for g in groups.values():
            require(len(g)==2 and g[0]['warmup'] is True and g[1]['warmup'] is False,'warmup/measured order')
            require(g[0]['request']==g[1]['request'] and g[0]['fresh_process'] and not g[1]['fresh_process'],'process recipe/reset link')
            require(g[1]['process_parent']==g[0]['slot'],'process parent mismatch')
        require(valid_hash(plan['selection_receipt_sha256']),'missing selection binding')

if __name__ == '__main__': main()
