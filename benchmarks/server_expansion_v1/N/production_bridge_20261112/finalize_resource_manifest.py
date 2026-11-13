"""Pure CPU proposal finalizer; never loads or launches selected artifacts."""
import copy
import hashlib
import json
from pathlib import Path
from resource_domain import canonical, DomainDenied, GiB
from resource_manifest import load_execution_manifest

HERE = Path(__file__).resolve().parent


def finalize(measurement_path, archive_plan_path=HERE / 'RESOURCE_ARCHIVE_PLAN.json'):
    measurement_raw = Path(measurement_path).read_bytes()
    selection = json.loads(measurement_raw)
    plan_raw = Path(archive_plan_path).read_bytes()
    archive = json.loads(plan_raw)
    if (archive.get('schema') != 'hs.production-bridge.resource-archive-plan.v1'
            or archive.get('mode') != 'CPU_PROPOSAL_ONLY'
            or archive.get('approval') is not None or archive.get('native_execution_authorized') is not False
            or archive.get('public_cpu_archive', {}).get('whole_retained_build_selection_included') is not False):
        raise DomainDenied('Archive plan cannot grant native authority')
    if selection.get('schema') != 'hs.production-bridge.measured-retained-selection.v1' or selection.get('issues'):
        raise DomainDenied('Measured selected artifact receipt is incomplete or failed')
    for key in ('selected_path_logical_bytes', 'unique_resolved_inode_allocated_bytes', 'selected_path_count'):
        if type(selection.get(key)) is not int or selection[key] < 0:
            raise DomainDenied('Selected logical/physical byte measurement absent')
    if not isinstance(selection.get('files'), list) or len(selection['files']) != selection['selected_path_count']:
        raise DomainDenied('Selected file denominator differs')
    for row in selection['files']:
        if type(row.get('bytes')) is not int or row['bytes'] < 0 or not isinstance(row.get('sha256'), str) or len(row['sha256']) != 64:
            raise DomainDenied('Selected file byte identity absent')
    if sum(row['bytes'] for row in selection['files']) != selection['selected_path_logical_bytes']:
        raise DomainDenied('Selected file byte sum differs')
    raw = archive.get('raw_archive', {})
    required = dict(entry_ceiling=4096, relative_path_bytes_ceiling=256,
                    header_bytes_ceiling=16777216, raw_metadata_journal_restore_bytes=144739606528,
                    ancillary_export_bytes_ceiling=GiB, ancillary_strict_restore_bytes_ceiling=GiB,
                    archive_bytes_ceiling=147651175875)
    if any(raw.get(k) != v for k, v in required.items()):
        raise DomainDenied('Archive or restore limits were enlarged/changed')
    if (raw.get('status') != 'NOT_FROZEN_NO_NATIVE_DATA' or raw.get('deletion_required') is not False
            or not isinstance(raw.get('include_categories'), list)
            or not isinstance(raw.get('exclude_categories'), list)):
        raise DomainDenied('Unfrozen archive selection or no-deletion contract differs')
    # Retained artifacts and restored ancillary logs/records share the existing
    # seven-GiB pool. There is no extra restore or exported-source allowance.
    selected = max(selection['selected_path_logical_bytes'], selection['unique_resolved_inode_allocated_bytes'])
    selected_and_readback = selected + raw['ancillary_strict_restore_bytes_ceiling']
    if selected_and_readback > 7 * GiB:
        raise DomainDenied('Retained selection plus ancillary readback exceeds old artifact pool')
    archive_input = raw['raw_metadata_journal_restore_bytes'] + raw['ancillary_export_bytes_ceiling']
    if archive_input + raw['header_bytes_ceiling'] > raw['archive_bytes_ceiling']:
        raise DomainDenied('Raw archive plus bounded ancillary input does not fit')
    value = load_execution_manifest()
    base_sha = value.pop('manifest_sha256')
    complete = selection.get('status') == 'MEASURED_SELECTION_UNDER_CAP_NOT_ADMISSION' and not selection.get('pending_replacements')
    build = value['build_selection']
    build.update(status='MEASURED_SELECTED_SET_UNDER_CAP_NOT_ADMISSION' if complete else 'BLOCKED_FINAL_REPLACEMENTS_PENDING',
                 measured_logical_bytes=selection['selected_path_logical_bytes'],
                 measured_unique_inode_bytes=selection['unique_resolved_inode_allocated_bytes'],
                 measured_selected_file_count=selection['selected_path_count'],
                 selected_and_ancillary_readback_bytes=selected_and_readback,
                 old_pool_headroom_after_readback_bytes=7 * GiB - selected_and_readback,
                 selected_receipt=dict(file=Path(measurement_path).name, bytes=len(measurement_raw),
                                       sha256=hashlib.sha256(measurement_raw).hexdigest()),
                 archive_excluded_categories=raw['exclude_categories'],
                 raw_archive_inclusions=raw['include_categories'],
                 retained_selection_is_archive_allowlist=False)
    value['resource_archive_plan'] = copy.deepcopy(archive)
    value['resource_archive_plan_identity'] = dict(file=Path(archive_plan_path).name, bytes=len(plan_raw),
                                                  sha256=hashlib.sha256(plan_raw).hexdigest())
    value['base_unapproved_execution_manifest_sha256'] = base_sha
    value['archive_accounting'] = dict(
        max_payload_bytes_including_ancillary=archive_input,
        max_payload_plus_headers=archive_input + raw['header_bytes_ceiling'],
        archive_reserved_bytes=raw['archive_bytes_ceiling'],
        raw_restore_reserved_bytes=raw['raw_metadata_journal_restore_bytes'],
        ancillary_restore_charged_to_existing_artifact_pool=GiB,
        total_disk_bytes_unchanged=553094505923,
        raw_export_entries_status='NOT_FROZEN_NO_NATIVE_DATA',
        selected_build_entry_count_does_not_establish_raw_archive_entry_pass=True)
    if complete:
        value['admission_gaps'] = [s for s in value['admission_gaps']
                                   if s != 'Full retained build/source selection is unmeasured']
        value['admission_gaps'].append('Raw native-data export allowlist is not frozen; no native data were generated')
    value['finalization_source'] = dict(file='finalize_resource_manifest.py',
                                       sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    value['manifest_sha256'] = hashlib.sha256(canonical(value)).hexdigest()
    return value


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--selection', required=True)
    p.add_argument('--archive-plan', default=str(HERE / 'RESOURCE_ARCHIVE_PLAN.json'))
    p.add_argument('--out', required=True)
    args = p.parse_args()
    with Path(args.out).open('x') as output:
        json.dump(finalize(args.selection, args.archive_plan), output, indent=2, sort_keys=True)
        output.write('\n')
