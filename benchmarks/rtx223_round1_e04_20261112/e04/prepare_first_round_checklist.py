"""Bind unchanged first-round expectations; no native execution entry."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parents[1] / 'rtx223-round1-resume-20261112-e03'
PARENT_HEAD = '7a4f2ca75923066c6eaac02a5e9ae885a846d688'
PUBLIC_PREFIX = 'benchmarks/rtx223_round1_e03_20261112/'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, value):
    if path.exists():
        raise FileExistsError(path)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')

def main():
    dest = HERE / 'qualification'
    dest.mkdir()
    refs = ['RESOURCE_PLAN.json', 'RESEARCH_QUESTION.md', 'qualification/CASES.json',
            'qualification/FALLBACK_ALLOWLIST.json', 'request/PROTOCOL.md',
            'native/OPERATOR_PREPARATION.json', 'OPERATOR_RAW_PAIRS.json',
            'continuation/NEXT_NATIVE_ENTRY.md', 'e03/RESULT.json',
            'e03/review/FINAL_REVIEW.json', 'e03/PREPARATION_FAILURES.json',
            'e03/dedup/OWNER_STEPS_ZH.md']
    save(dest / 'INHERITED_REFERENCES.json', {
        'parent_head': PARENT_HEAD,
        'files': [{'path': name, 'local_read_only': str(PARENT / name),
                   'sha256': digest(PARENT / name),
                   'url': f'https://github.com/leecdiang/HeteroSpec/blob/{PARENT_HEAD}/{PUBLIC_PREFIX}{name}'}
                  for name in refs],
        'history_is_not_current_native_observation': True})
    cases = json.loads((PARENT / 'qualification/CASES.json').read_bytes())
    (dest / 'CASES.json').write_bytes((PARENT / 'qualification/CASES.json').read_bytes())
    cells = [{'case': c['id'], 'arm': a, 'frozen_expectation': expectation,
              'status': 'NOT_RUN', 'reason': 'Native admission closed'}
             for c in cases['cases'] for a, expectation in c['arms'].items()]
    if len(cells) != 66:
        raise ValueError('22x3 frozen qualification cells required')
    save(dest / 'NATIVE_STATUS.json', {'utc': datetime.now(timezone.utc).isoformat(),
                                     'cases_sha256': digest(dest / 'CASES.json'),
                                     'native_cells': 66, 'executed': 0, 'cells': cells})
    plan = json.loads((PARENT / 'RESOURCE_PLAN.json').read_bytes())
    save(dest / 'STOP_RULES.json', {
        'schema': 'heterospec.e04.first-round-stops.v1',
        'round': 1, 'native_execution_enabled': False, 'new_allowance': False,
        'limits': plan['maximums'],
        'request_allocations': plan['request_allocations'],
        'kernel_allocations': plan['kernel_launch_allocations'],
        'warmup_included_not_added': plan['warmup_included_not_additional'],
        'must_all_precede_any_DLL_initialization': [
            'Content-bound original execution-turn terminal evidence; no pending worker/lease',
            'Fresh trusted host scope immediately before any admitted launch',
            'Original authorization/window still valid, same canonical ledger and owned lock',
            'Whole-lifecycle finite physical-kernel bound plus pre-submission enforcement',
            'Initialization, module/library load, model transfer and teardown covered or refused',
            'Frozen source/dependency/EXE/DLL manifest independently bound',
            'Original authorized device, model/vocab/producer/KV/graph/resource contract'],
        'stages_in_order': [
            {'id': 'Q0', 'action': 'Capture one actual q8 projection from a frozen real eight-token input; original-path replay',
             'requirements': ['Exact original descriptor and original-path full output', 'No slicing a q32 capture',
                              'Complete quantized activation including padding', 'All output F32 bytes, identities and geometry']},
            {'id': 'Q1', 'action': 'Execute all applicable frozen22x3 qualification cells',
             'requirements': ['Distinct pre-execution rejection / qualified fallback / post-execution owner invalidation',
                              'Always-on clean guard distinct from capture observer',
                              'A/B/C dtype, shape, stride, placement, dispatch, output mask and graph policy',
                              'Requested full vectors; target/draft untrimmed and committed active states; owner generation']},
            {'id': 'Q2', 'action': 'Paired operator screening only after Q0/Q1 pass',
             'frozen_operator_protocol': 'two own-path repeats/arm, three warmups/arm, six balanced three-arm timing blocks',
             'standalone_prospective_launches': 119,
             'standalone_bound_is_not_model_lifecycle_bound': True,
             'measure_separately': ['kernel-only', 'shared quantizer plus synchronization complete operator'],
             'attribution': ['A-to-B grid/launch organization', 'B-to-C mechanism plus register/shared/parallelism costs'],
             'DRAM_L2_without_counters': 'unknown'},
            {'id': 'Q3', 'action': 'One real complete bonus-seed-fifth-reject-L4-correction-trim-pending-continuation chain',
             'requirements': ['Real logits select actual bonus and correction seeds',
                              'No forced token37, sameKV or argmax substitute',
                              'All requested vectors, accepted, CAP/EOG and exact termination reason',
                              'No natural coverage means NOT_COVERED; constructed fixture separately labeled']},
            {'id': 'Q4', 'action': 'Matched full resident-service endpoint and strongest qualified frozen fixed control',
             'requirements': ['Fair applicable lazy-tail/cap/buffer reuse',
                              'Include controller, reset/prefill/draft/verify/sync/planning/guard/reconciliation/state/fallback',
                              'No sum of overlapping spans or pieces from different requests/panels',
                              'Different-semantic target-only/runtime reported separately']}],
        'immediate_stop': [
            'Missing admission proof or unknown kernel bound: before any CUDA/runtime DLL initialization',
            'Any critical byte/state/identity/guard failure: no subsequent timing, invalidate owner after execution',
            'Unknown actual on child failure/timeout: retain conservative reservation, no refund/retry',
            'Original quota/deadline reached or next operation cannot fit proven bound',
            'Gate fails or paired/complete-cost evidence is adverse: no sample expansion to chase positive sign'],
        'unresolved_feasibility': 'No proved complete model launch bound exists. Frozen bucket sizes and standalone119 do not establish feasibility under4096.',
        'Go_requires_all': ['Qualified exactness', 'Interpretable paired improvement over current packed',
                            'Real consumer coverage', 'Complete service costs with realistic net-benefit space'],
        'no_round2_execution_or_recommendation_from_CPU_or_link': True})
    print(json.dumps({'native_cells_NOT_RUN': 66, 'case_hash': digest(dest / 'CASES.json'), 'native_enabled': False}))

if __name__ == '__main__':
    main()
