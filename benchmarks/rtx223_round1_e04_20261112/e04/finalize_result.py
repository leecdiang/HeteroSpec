"""Bind final CPU artifacts and explicit archive products. Never load a DLL."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

def read(path):
    return json.loads(path.read_bytes())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, value):
    if path.exists():
        raise FileExistsError(path)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')

def main():
    runtime = read(ROOT / 'runtime/STATUS.json')
    comp = read(ROOT / 'runtime/build-v2/BUILD.json')
    link = read(ROOT / 'runtime/link-v3/BUILD.json')
    freeze = read(HERE / 'freeze/v2/FREEZE.json')
    front = read(HERE / 'frontend/recovery-v1/BUILD.json')
    host = read(HERE / 'frontend/HOST_ARTIFACTS_v4.json')
    binding = read(HERE / 'frontend/DEPLOYMENT_BINDING_v2.json')
    modules = read(HERE / 'frontend/expected-modules-v1/MODULE_CLOSURE_v3.json')
    budget = read(HERE / 'budget/STATUS.json')
    preservation = read(HERE / 'PRESERVATION_FINAL.json')
    if comp['compile_failures'] or comp['dependency_closure'] != 'PASS' or link['link_returncode']:
        raise ValueError('Frozen numerical build not ready')
    if front['status'] != 'PASS_FROZEN_BUILD_NOT_NATIVE_QUALIFIED' or not preservation['passed']:
        raise ValueError('Frontend/preservation gate incomplete')
    if budget['native_proof_registry_entries'] != 0 or binding['numeric_DLL_OS_load'] != 'NOT_RUN':
        raise ValueError('Expected closed native admission')
    artifacts = []
    def add(path, kind, expected=None):
        path = Path(path).resolve(strict=True)
        if not path.is_relative_to(ROOT):
            raise ValueError('Product outside e04')
        h = sha(path)
        if expected and h != expected:
            raise ValueError('Product identity changed')
        artifacts.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': h,
                          'bytes': path.stat().st_size, 'kind': kind, 'published_in_Git': False})
    add(link['DLL_path'], 'NEW_NUMERICAL_DLL_NOT_LOADED_OR_NATIVE_QUALIFIED', link['DLL_sha256'])
    for output in front['outputs']:
        add(output['exe'], 'NEW_FRONTEND_' + output['core'].upper() + '_NOT_RUN', output['exe_sha256'])
    add(HERE / 'ledger-evidence/FAMILY_LEDGER_READONLY_SNAPSHOT.sqlite', 'READ_ONLY_AUDIT_COPY_NOT_NEW_CANONICAL_LEDGER', preservation['copy_sha256'])
    for base in (HERE / 'budget', HERE / 'review/lifecycle'):
        for path in sorted(base.rglob('*.sqlite')):
            if 'private' not in path.relative_to(ROOT).parts:
                add(path, 'OWN_CPU_MOCK_FIXTURE_NOT_PRODUCTION_GPU_LEDGER')
    allowlist = {'schema': 'heterospec.e04.explicit-archive-products.v1', 'files': artifacts,
                 'vendor_toolchain_DLL_bytes_excluded': True}
    if (HERE / 'BINARY_ALLOWLIST.json').exists():
        if read(HERE / 'BINARY_ALLOWLIST.json') != allowlist:
            raise ValueError('Explicit binary set changed; preserve old list and version before regenerating')
    else:
        save(HERE / 'BINARY_ALLOWLIST.json', allowlist)
    evidence_names = ['runtime/STATUS.json', 'runtime/AS_BUILT_BINDINGS.json', 'runtime/build-v2/BUILD.json',
                      'runtime/link-v3/BUILD.json', 'e04/freeze/v2/FREEZE.json',
                      'e04/frontend/STATUS_v2.json', 'e04/frontend/LATEST.json', 'e04/frontend/recovery-v1/BUILD.json',
                      'e04/frontend/HOST_ARTIFACTS_v4.json', 'e04/frontend/DEPLOYMENT_BINDING_v2.json',
                      'e04/frontend/expected-modules-v1/MODULE_CLOSURE_v3.json',
                      'e04/budget/STATUS.json', 'e04/budget/NATIVE_PREFLIGHT.json',
                      'e04/dedup/DEDUP_E04_RESULT.json', 'e04/PRESERVATION_FINAL.json',
                      'e04/qualification/STOP_RULES.json', 'e04/qualification/NATIVE_STATUS.json']
    save(HERE / 'RESULT.json', {
        'schema': 'heterospec.rtx223.e04.result.v1', 'UTC': datetime.now(timezone.utc).isoformat(),
        'client_timezone': 'Asia/Shanghai', 'epoch': 'rtx223-round1-resume-20261112-e04',
        'parent_head': '7a4f2ca75923066c6eaac02a5e9ae885a846d688',
        'decision': 'INCONCLUSIVE', 'round': 1, 'round2_started': False,
        'gates': {
            'original_execution_terminal_queued_worker_lease': 'BLOCKED_PENDING_USER',
            'reported_previous_host_snapshot': 'USER_REPORTED_TRANSIENT_NOT_TERMINAL_PROOF',
            'lifecycle_CPU_proof_reservation_simulated_enforcement': 'PASS_CPU_MOCK_ONLY',
            'usable_complete_lifecycle_physical_4096_budget': 'BLOCKED_NOT_IMPLEMENTED_NATIVE',
            'source_codegen_freeze_and_fresh_numeric_DLL_link': 'PASS_CONTROLLED_BUILD_INPUT_SCOPE',
            'frontend_two_fresh_frozen_codegen_links': 'PASS_SEPARATE_SESSIONS',
            'complete_archive_identity': 'PASS_CONSERVATIVE_WHOLE_CONTAINER_SCOPE',
            'ambiguous_exact_archive_member_selection': 'NOT_ATTESTED',
            'isolated_expected_modules_static_PE_name_closure': 'PASS_DISK_ONLY_NATIVE_UNQUALIFIED',
            'historical_VCOMP_identity_equivalence': 'UNKNOWN_PROPOSED_NEW_DEPENDENCY',
            'actual_loaded_modules_ABI_CUDA_route_identity': 'NOT_RUN',
            'native_qualification_22_by_3': 'NOT_RUN',
            'paired_kernel_operator_screen': 'NOT_RUN',
            'real_bonus_seed_L4_correction_closure': 'NOT_RUN',
            'full_resident_service_strong_fixed_control': 'NOT_RUN'},
        'usage': {'model_requests': 0, 'target_rows': 0, 'draft_rows': 0, 'CUDA_contexts': 0,
                  'GPU_kernel_launches': 0, 'native_GPU_seconds': 0, 'GPU_capture_bytes': 0,
                  'worker_EXE_runs': 0, 'normal_numeric_DLL_loads': 0},
        'same_family_original_limits': read(HERE / 'BUDGET_CONTINUITY.json')['original_limits'],
        'canonical_ledger': read(HERE / 'BUDGET_CONTINUITY.json')['canonical_ledger'],
        'new_allowance_or_window_reset': False,
        'canonical_ledger_reads_readonly': True, 'canonical_ledger_writes': 0,
        'native_complete_lifecycle_upper_bound': None, 'native_proof_registry_entries': 0,
        'native_budget_source_expected_return': -6, 'new_DLL_budget_export_actual_call': 'NOT_RUN',
        'native_release_from_CPU_or_self_signed_receipt': False,
        'new_CPU_budget_tests_per_mode': 26, 'new_CPU_budget_modes': ['ordinary', '-O'],
        'new_input_closure_fixtures_per_mode': 24,
        'old_e01_e02_e03_test_suites_rerun': False,
        'source': {'full_files': freeze['complete_source_files'], 'body_changes_from_e03_uniform': 0,
                   'all_h_headers': 297, 'frozen_input_files': freeze['input_files'],
                   'frozen_input_bytes': freeze['input_bytes']},
        'build': {'fresh_numeric_objects': 145, 'e03_or_failed_e04_v1_objects': 0,
                  'compile_session': 'runtime/build-v2', 'link_session': 'runtime/link-v3',
                  'uninterrupted_compile_link_freeze': False,
                  'frontend_header_dependencies_per_core': 1051, 'frontend_CPU_features_per_core': 117,
                  'frontend_complete_archive_containers_per_core': 33,
                  'frontend_input_count': host['frozen_input_count'], 'frontend_input_bytes': host['codegen_input_bytes'],
                  'compile_wall_seconds_not_service_latency': comp['wall_seconds'],
                  'link_wall_seconds_not_service_latency': link['link_wall_seconds_including_input_lock_hashes']},
        'DLL': {'path': link['DLL_path'], 'bytes': link['DLL_bytes'], 'sha256': link['DLL_sha256']},
        'frontends': [{'core': z['core'], 'exe': z['exe'], 'sha256': z['exe_sha256']} for z in front['outputs']],
        'fresh_resource_metrics': 'UNKNOWN; historical e03 compiler values not transplanted',
        'native_cells': {'total': 66, 'executed': 0, 'NOT_RUN': 66},
        'estimates': {'kernel_latency': None, 'operator_latency': None, 'service_latency': None,
                      'packed_increment': None, 'error_interval': None, 'DRAM_L2_change': 'UNKNOWN'},
        'preserved_original_manifest_files': sum(z['files'] for z in preservation['original_manifests']),
        'old_provider_sync_exception': 'Preserved in e03; exact old synchronization time remains unknown',
        'proof_limit': 'Recorded source/codegen input closure is frozen and hash-bound; Windows loader/OS and Python runtime/stdlib are not a globally immutable system image. No universal byte-identical rebuild or native correctness claim.',
        'independent_review': 'review/FINAL_REVIEW.json',
        'minimum_owner_steps': 'dedup/OWNER_STEPS_ZH.md',
        'minimum_native_coverage_steps': 'budget/NATIVE_CLOSURE_REQUIREMENTS.md',
        'evidence': [{'path': name, 'sha256': sha(ROOT / name)} for name in evidence_names],
        'Go_conditions_met': False, 'merge_release_paper_changes': False})
    print(json.dumps({'decision': 'INCONCLUSIVE', 'archive_explicit_products': len(artifacts),
                      'numeric_DLL_sha256': link['DLL_sha256'], 'native_usage_zero': True}))

if __name__ == '__main__':
    main()
