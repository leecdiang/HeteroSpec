"""Finalize additive e03 receipts; never initialize CUDA or write old ledgers."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT.parent / 'rtx223-round1-resume-20261112-e02'
E01 = ROOT.parent / 'rtx221-round1-20261112'

def read(path):
    return json.loads(path.read_bytes())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf8')

def main():
    utc = datetime.now(timezone.utc).isoformat()
    frozen = read(ROOT / 'qualification/CASES.json')
    cells = []
    for case in frozen['cases']:
        for arm, expected in case['arms'].items():
            cells.append({'case': case['id'], 'arm': arm,
                          'expected_decision': expected['expected_decision'],
                          'frozen_expectation': expected,
                          'expected_route': expected.get('expected_route'),
                          'native_result': 'NOT_RUN', 'numerical_result': 'NOT_RUN',
                          'clean_guard_result': 'NOT_RUN',
                          'reason': 'Original-thread/host clearance and usable complete physical-launch budget remain BLOCKED'})
    if len(cells) != 66:
        raise ValueError('Expected 22x3 frozen cells')
    write(ROOT / 'e03/NATIVE_QUALIFICATION.json', {
        'schema': 'heterospec.e03.native-qualification.v1', 'utc': utc,
        'frozen_cases_sha256': sha(ROOT / 'qualification/CASES.json'),
        'native_cells': 66, 'executed': 0, 'NOT_RUN': 66, 'cells': cells,
        'CPU_schema_fixture_count_is_not_native_qualification': True})
    preservation = []
    for folder in (PARENT, E01):
        manifest_path = folder / 'delivery/DELIVERY_MANIFEST.json'
        manifest = read(manifest_path)
        bad = [row['path'] for row in manifest['files']
               if not (folder / row['path']).is_file() or sha(folder / row['path']) != row['sha256']]
        preservation.append({'path': str(folder), 'files_checked': len(manifest['files']),
                             'manifest_sha256': sha(manifest_path), 'mismatches': bad})
    old = read(ROOT / 'e03/dedup/DEDUP_E03_RESULT.json')['old_file_checks']
    ledgers = []
    for row in old:
        actual = sha(Path(row['path']))
        ledgers.append({'path': row['path'], 'expected_sha256': row['sha256'],
                        'actual_sha256': actual, 'unchanged': actual == row['sha256']})
    snapshot = read(ROOT / 'e03/ledger-evidence/SNAPSHOT.json')
    family = Path(snapshot['source_canonical_ledger'])
    ledgers.append({'path': str(family), 'expected_sha256': snapshot['source_sha256'],
                    'actual_sha256': sha(family), 'unchanged': sha(family) == snapshot['source_sha256']})
    passed = not any(row['mismatches'] for row in preservation) and all(row['unchanged'] for row in ledgers)
    write(ROOT / 'e03/PRESERVATION_FINAL.json', {
        'utc': utc, 'original_text_manifests': preservation, 'old_and_family_ledgers': ledgers,
        'passed': passed, 'old_files_written': False, 'new_ledger': False})
    if not passed:
        raise ValueError('Original preservation check failed')
    result = {
        'schema': 'heterospec.rtx223.e03.result.v1', 'utc': utc,
        'decision': 'INCONCLUSIVE', 'round': 1, 'round2_started': False,
        'epoch': 'rtx223-round1-20261112-e03',
        'parent_head': '8f2585f90c40c81bca726c50647af650fd866e3f',
        'upstream221': 'af436df989570ad882db65bd8a4b265b9e8cfdae',
        'gates': {
            'old_material_and_budget_binding': 'PASS',
            'original_threads_and_host_scope': 'BLOCKED',
            'inherited_Windows_supervision_CPU': 'PASS_INHERITED_SCOPE_ONLY',
            'source_visible_shared_prelaunch_guard_CPU': 'PASS_LIMITED_SCOPE',
            'full_model_physical_4096_launch_enforcement': 'BLOCKED_NOT_QUALIFIED',
            'usable_complete_model_budget_profile': 'BLOCKED_NOT_PROVED',
            'numerical_C_DLL_compile_link': 'PASS',
            'frontend_profile_binding_CPU': 'PASS',
            'numerical_DLL_normal_load_actual_runtime_dispatch': 'NOT_RUN',
            'native_qualification_22_by_3': 'NOT_RUN',
            'paired_kernel_operator_timing': 'NOT_RUN',
            'real_bonus_seed_L4_correction_closure': 'NOT_RUN',
            'same_contract_resident_service_cost': 'NOT_RUN'},
        'usage': {'model_requests': 0, 'target_rows': 0, 'draft_rows': 0,
                  'CUDA_contexts': 0, 'GPU_kernel_launches': 0, 'native_GPU_seconds': 0,
                  'GPU_capture_bytes': 0},
        'family_usage': 'same zero totals; canonical ledger attempts=0, window_start=null',
        'limits': read(ROOT / 'e03/BUDGET_CONTINUITY.json')['original_limits'],
        'canonical_ledger': str(family), 'new_allowance': False,
        'native_configure_return': -6,
        'native_release_via_receipt_or_JSON': False,
        'qualification_cells': {'total': 66, 'PASS': 0, 'FAIL': 0, 'NOT_RUN': 66},
        'new_CPU_evidence': {
            'shared_counter_scenarios': 16, 'independent_counter_scenarios': 16,
            'source_transform_tests_normal_optimized': [6, 6],
            'frontend_schema_gate_fixtures': 22,
            'identity_reader_tests_normal_optimized': [6, 6],
            'CPU_standin_loader_cases': 4,
            'old_41_and_18_suites_rerun': False,
            'not_native_qualification': True},
        'numerical_DLL': read(ROOT / 'runtime/STATUS.json')['DLL'],
        'compiler_resources_not_measurement': read(ROOT / 'runtime/COMPILER_RESOURCES.json'),
        'estimates': {'kernel_latency': None, 'operator_latency': None, 'service_latency': None,
                      'paired_improvement_over_packed': None, 'error_interval': None,
                      'DRAM_L2_change': 'unknown', 'occupancy': 'unknown'},
        'source_reconstruction': read(ROOT / 'runtime/RECONSTRUCTION_V2_RECEIPT.json'),
        'as_built_provenance_limit': 'Provider source sync occurred during first batch at unknown exact time; superseded provider object excluded. No full per-invocation dependency-time snapshot or universal byte-identical DLL rebuild claim.',
        'independent_review': 'review/FINAL_REVIEW.json',
        'failures_preserved': 'PREPARATION_FAILURES.json',
        'required_host_evidence': 'dedup/OWNER_STEPS_ZH.md',
        'next_step_scope': 'First-round admission only; no larger sample or second round',
        'Go_conditions_met': False,
        'why_not_NO_GO': 'No admitted native numerical or paired/service evidence exists to reject the mechanism; unresolved access/coverage gates preclude a mechanism conclusion',
        'PR_merged': False, 'paper_modified': False}
    write(ROOT / 'e03/RESULT.json', result)
    print(json.dumps({'preserved': passed, 'native_NOT_RUN': len(cells), 'decision': result['decision']}))

if __name__ == '__main__':
    main()
