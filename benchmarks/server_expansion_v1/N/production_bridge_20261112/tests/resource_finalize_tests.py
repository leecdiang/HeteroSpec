"""CPU proposal arithmetic tests; do not read/execute any selected artifact."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from finalize_resource_manifest import finalize, HERE
from resource_domain import DomainDenied, canonical, GiB

OUT = None


class FinalizerTests(unittest.TestCase):
    def input(self, suffix='', **overrides):
        row = dict(root='CPU_MOCK', relative_path='synthetic.txt', bytes=1, sha256='a' * 64)
        value = dict(schema='hs.production-bridge.measured-retained-selection.v1',
                     selection_id='CPU_ONLY_SYNTHETIC_MEASUREMENT',
                     status='MEASURED_SELECTION_UNDER_CAP_NOT_ADMISSION',
                     selected_path_count=1, selected_path_logical_bytes=1,
                     unique_resolved_inode_allocated_bytes=4096, files=[row],
                     issues=[], pending_replacements=[])
        value.update(overrides)
        path = Path(OUT) / (self._testMethodName + suffix + '.json')
        path.write_text(json.dumps(value))
        return path

    def archive(self, mutate):
        value = json.loads((HERE / 'RESOURCE_ARCHIVE_PLAN.json').read_text())
        mutate(value)
        path = Path(OUT) / (self._testMethodName + '-archive.json')
        path.write_text(json.dumps(value))
        return path

    def test_exact_budget_and_shared_ancillary_restore(self):
        m = finalize(self.input())
        self.assertEqual(m['limits']['required_disk_bytes'], 553094505923)
        self.assertEqual((m['limits']['requests'], m['limits']['rows'], len(m['requests'])), (76, 85738, 72))
        self.assertEqual(m['build_selection']['selected_and_ancillary_readback_bytes'], 4096 + GiB)
        self.assertEqual(m['build_selection']['status'], 'MEASURED_SELECTED_SET_UNDER_CAP_NOT_ADMISSION')
        self.assertFalse(m['build_selection']['retained_selection_is_archive_allowlist'])
        self.assertIsNone(m['approval'])
        self.assertFalse(m['native_execution_authorized'])
        digest = m.pop('manifest_sha256')
        self.assertEqual(hashlib.sha256(canonical(m)).hexdigest(), digest)

    def test_7888_retained_files_do_not_claim_4096_raw_entry_admission(self):
        rows = [dict(root='CPU_MOCK', relative_path='retained-%04d.txt' % i,
                     bytes=1, sha256='a' * 64) for i in range(7888)]
        m = finalize(self.input(selected_path_count=7888, files=rows,
                                selected_path_logical_bytes=7888,
                                unique_resolved_inode_allocated_bytes=7888 * 4096))
        self.assertEqual(m['build_selection']['measured_selected_file_count'], 7888)
        self.assertEqual(m['resource_archive_plan']['raw_archive']['entry_ceiling'], 4096)
        self.assertEqual(m['archive_accounting']['raw_export_entries_status'], 'NOT_FROZEN_NO_NATIVE_DATA')

    def test_oversized_retained_plus_restore_fails_without_new_pool(self):
        rows = [dict(root='CPU_MOCK', relative_path='huge', bytes=7 * GiB, sha256='a' * 64)]
        p = self.input(files=rows, selected_path_logical_bytes=7 * GiB,
                       unique_resolved_inode_allocated_bytes=7 * GiB)
        self.assertRaises(DomainDenied, finalize, p)

    def test_missing_physical_measurement_blocks(self):
        p = self.input(unique_resolved_inode_allocated_bytes=None)
        self.assertRaises(DomainDenied, finalize, p)

    def test_receipt_denominator_and_byte_sum_must_match(self):
        self.assertRaises(DomainDenied, finalize, self.input('-count', selected_path_count=2))
        self.assertRaises(DomainDenied, finalize, self.input('-sum', selected_path_logical_bytes=2))

    def test_failed_measurement_never_becomes_cap_pass(self):
        self.assertRaises(DomainDenied, finalize, self.input(issues=[dict(reason='changed file')]))

    def test_pending_replacements_remain_blocked(self):
        m = finalize(self.input(pending_replacements=['source snapshot update']))
        self.assertEqual(m['build_selection']['status'], 'BLOCKED_FINAL_REPLACEMENTS_PENDING')
        self.assertIsNone(m['approval'])

    def test_changed_archive_entry_or_restore_quota_fails(self):
        for key, value in [('entry_ceiling', 4097), ('ancillary_strict_restore_bytes_ceiling', GiB + 1)]:
            plan = json.loads((HERE / 'RESOURCE_ARCHIVE_PLAN.json').read_text())
            plan['raw_archive'][key] = value
            target = Path(OUT) / (self._testMethodName + '-' + key + '.json')
            target.write_text(json.dumps(plan))
            self.assertRaises(DomainDenied, finalize, self.input('-' + key), target)

    def test_archive_cannot_grant_authority_or_include_all_retained_files(self):
        p = self.input()
        plan = self.archive(lambda a: a.update(approval=dict(approved=True)))
        self.assertRaises(DomainDenied, finalize, p, plan)
        plan = json.loads((HERE / 'RESOURCE_ARCHIVE_PLAN.json').read_text())
        plan['public_cpu_archive']['whole_retained_build_selection_included'] = True
        target = Path(OUT) / (self._testMethodName + '-retained.json')
        target.write_text(json.dumps(plan))
        self.assertRaises(DomainDenied, finalize, p, target)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--out', required=True)
    args = p.parse_args()
    out = Path(args.out)
    if not out.is_absolute() or out.exists():
        raise SystemExit('Fresh absolute CPU proposal test directory required')
    out.mkdir(mode=0o700)
    OUT = str(out)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(FinalizerTests))
    receipt = dict(status='PASS' if result.wasSuccessful() else 'FAIL', tests=result.testsRun,
                   failures=len(result.failures), errors=len(result.errors),
                   scope='SYNTHETIC_CPU_PROPOSAL_ARITHMETIC_NOT_ARTIFACT_OR_HARDWARE_ADMISSION',
                   artifact_executions=0, model_or_GPU_operations=0, actual_cgroup_changes=0)
    (out / 'RESULT.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))
    raise SystemExit(0 if result.wasSuccessful() else 1)
