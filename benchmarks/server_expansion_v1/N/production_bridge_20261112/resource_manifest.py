"""Expand the pinned prior request graph with bounded, unapproved bridge costs."""
import copy
import hashlib
import json
from pathlib import Path
from resource_domain import canonical, resource_manifest, DomainDenied, MiB, GiB

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / 'admission_controller_20261112/CPU_EVIDENCE/resources-01/FROZEN_MANIFEST.json'
PRIOR_SHA = '29849931de2b2f5eaa9e14648f681cb1ab7123f5941fd64b59e2f479a069be63'
PRIOR_BYTES = 154234


def load_execution_manifest(prior_path=PRIOR):
    raw = Path(prior_path).read_bytes()
    if len(raw) != PRIOR_BYTES or hashlib.sha256(raw).hexdigest() != PRIOR_SHA:
        raise DomainDenied('Pinned prior operation/resource manifest differs')
    prior = json.loads(raw)
    value = copy.deepcopy(prior)
    prior_fingerprint = value.pop('manifest_sha256')
    if hashlib.sha256(canonical(value)).hexdigest() != prior_fingerprint:
        raise DomainDenied('Prior manifest canonical identity differs')
    if len(value['requests']) != 72 or sum(op['row_limit'] for op in value['requests'].values()) != 69354 or len(value['workers']) != 8 or len(value['deployments']) != 10:
        raise DomainDenied('Frozen request/worker/deployment graph differs')
    if (value['limits']['requests'], value['limits']['rows'], value['limits']['required_disk_bytes']) != (76, 85738, 553094505923):
        raise DomainDenied('Frozen global resource limits differ')
    value.update(schema='hs.N1a.production-bridge.execution.not-admitted.v1',
                 mode='CPU_MOCK_ONLY', run_id=None, approval=None, native_execution_authorized=False,
                 prior_manifest_sha256=prior_fingerprint,
                 prior_frozen_file=dict(bytes=PRIOR_BYTES, sha256=PRIOR_SHA),
                 resource_domain=resource_manifest())
    value['bridge_overhead'] = dict(
        immutable_records_max=128, immutable_record_bytes_max=32768,
        immutable_record_bytes_product=128 * 32768,
        compact_descriptor_bytes_max=4096, compact_descriptors_max=128,
        compact_descriptor_bytes_product=128 * 4096,
        placement_in_old_pool='bridge_receipts_bytes, carved from old controller_state_indices_bytes',
        old_native_RPC_source_bound=value['RPC_budget']['native_RPC_upper_bound'],
        extra_bridge_transition_allowance=128,
        conservative_RPC_plus_bridge=199196 + 128,
        shared_commands_ceiling=250000, shared_journal_bytes=512 * MiB,
        shared_journal_records=250100, shared_journal_record_bytes=2048,
        domain_snapshots='At most4096 bounded records in a bounded log, never one unbounded file per RPC',
        known_old_archive_entries=2471, new_bridge_domain_archive_entries_max=512,
        archive_entries_total_bound=2471 + 512, archive_entries_ceiling=4096)
    value['build_selection'] = dict(
        status='BLOCKED_COMPLETE_SELECTION_NOT_MEASURED', ceiling_bytes=7 * GiB,
        measured_logical_bytes=None, measured_unique_inode_bytes=None,
        partial_known_selected_bytes=1715339140,
        partial_components=dict(prior_native_pair=446211136, numerical_archives_12=452090090,
                                parser_objects_6=13657192, dynamic_dependencies_6=803380722),
        exclusions=['model GGUF stays in independently identified existing model store',
                    'all unrelated historical worktrees and results',
                    'unselected upstream/build trees'],
        required_selection=[
            dict(role='prior reference ELF', bytes=222813032, sha256=None),
            dict(role='prior loop4 ELF', bytes=223398104, sha256=None),
            dict(role='new reference frontend ELF', bytes=None, sha256=None),
            dict(role='new loop4 frontend ELF', bytes=None, sha256=None),
            dict(role='fixed std-only CPU launcher and worker', bytes=None, sha256=None),
            dict(role='frozen numeric archives/parser objects/dynamic library subset', bytes=None, sha256=None),
            dict(role='selected reconstructable source/compile receipts', bytes=None, sha256=None)],
        rule='Measure the exact selected files and resolved inodes; absent/oversize total blocks. No full historical buildtree is assumed to fit.')
    for worker in value['workers']:
        worker.update(domain_binding_sha256=None, immutable_job_sha256=None,
                      launcher_executable_sha256=None,
                      actual_cgroup_activation='NOT_RUN', atomic_domain_spawn='NOT_IMPLEMENTED_OR_ADMITTED')
    value['production_bridge_sources'] = {}
    for name in ('resource_domain.py', 'cpu_resource_fixture.py', 'resource_manifest.py'):
        b = (HERE / name).read_bytes()
        value['production_bridge_sources'][name] = dict(bytes=len(b), sha256=hashlib.sha256(b).hexdigest())
    value['admission_gaps'] = [
        'No approved GPU lease, new budget or five-hour window',
        'Kernel cgroup body is source-only behind unconditional denial; no actual activation',
        'Atomic clone3 domain launch not executed; no numeric-PID attach fallback',
        'Full retained build/source selection is unmeasured',
        'No native runtime peak/placement or numerical lifecycle evidence',
        'CPU synthetic leases and ordinary-file limits grant no hardware authority']
    value['manifest_sha256'] = hashlib.sha256(canonical(value)).hexdigest()
    return value


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--out', required=True)
    args = p.parse_args()
    with Path(args.out).open('x') as output:
        json.dump(load_execution_manifest(), output, indent=2, sort_keys=True)
        output.write('\n')
