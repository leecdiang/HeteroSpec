"""Pure injected CPU resource/manifest/cgroup-file tests; no native objects."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import generate_manifest as G
from resource_limits import (GiB, MiB, KV_BYTES, VECTOR_BYTES, FROZEN_SPACE_BYTES,
                             ResourcePolicy, ResourceBlocked, MockCgroupFS,
                             DelegatedCgroupPlan, resource_budget)

OUT = None


def cpu_fixture():
    manifest = G.instantiate_cpu_manifest('CPU_RESOURCE_TEST_ONLY', 1000., 100.)
    manifest['gpu_uuid_sha256'] = 'a' * 64
    manifest = G.finalize_manifest_cpu(manifest)
    now = dict(wall=1001., mono=101.)
    snapshot = dict(observed_wall=1001., observed_mono=101., evidence_class='CPU_MOCK_ONLY',
                    disk_available_bytes=FROZEN_SPACE_BYTES + GiB,
                    RAM_available_bytes=48 * GiB, worker_RSS_bytes=0,
                    retained_build_artifact_bytes=GiB,
                    gpu=dict(uuid_sha256='a' * 64, free_bytes=12 * GiB, total_bytes=24 * GiB,
                             preflight_peak_bytes=10 * GiB, preflight_status='PASS_NO_FORWARD'),
                    enforcement=dict(memory=dict(mechanism='DELEGATED_CGROUP_V2', status='VERIFIED',
                                                 membership_verified=True, only_owned_descendants=True,
                                                 memory_max_bytes=24 * GiB),
                                     GPU_exclusive=dict(mechanism='EXTERNAL_EXCLUSIVE_ALLOCATION', status='VERIFIED',
                                                        run_id=manifest['run_id'], uuid_sha256='a' * 64,
                                                        expires_wall=19000., expires_mono=18100.)),
                    process_ownership=dict(identity_verified=True, foreign_target_process_count=0,
                                           unknown_target_process_count=0),
                    locks=dict(verified=True, conflict=False),
                    identity=dict(verified=True, manifest_sha256=manifest['manifest_sha256']))
    return manifest, snapshot, now


class ResourceTests(unittest.TestCase):
    def test_frozen_operations_rows_and_deployments_independent_arithmetic(self):
        m = G.load_manifest()
        self.assertEqual(len(m['requests']), 4 * (4 * 2 + 5 * 2))
        natural = 4 * (92 + 63 + 27 + 108 + 4 * 127) + 16 * 4096
        controls = 20 * 13 + 3 * (16 + 16 + 1 + 25 + 25) + (29 + 25 + 13 + 25 + 25)
        self.assertEqual((natural, controls, natural + controls), (68728, 626, 69354))
        self.assertEqual(sum(r['row_limit'] for r in m['requests'].values()), natural + controls)
        self.assertEqual(len(m['workers']), 8)
        self.assertEqual(len(m['deployments']), 10)
        for axis in ('backend_inits', 'models', 'contexts', 'placements'):
            self.assertEqual(sum(d[axis] for d in m['deployments']), 10)
        self.assertFalse(m['failure_reserve']['runnable'])
        self.assertFalse(m['failure_reserve']['automatic_retry'])

    def test_capture_inventory_and_setup_ownership_charge(self):
        m = G.load_manifest()
        counts = [r['capture_counts'] for r in m['requests'].values()]
        self.assertEqual(sum(c['state_snapshots'] for c in counts), 252)
        self.assertEqual(sum(c['owned_events'] for c in counts), 72)
        self.assertEqual(sum(c['reconcile_receipts'] + c['mutation_receipts'] + c['binding_receipts'] for c in counts), 99)
        self.assertEqual(sum(c['producer_receipts'] for c in counts), 24)
        self.assertEqual(sum(r['prepaid_marker_bytes'] for r in m['requests'].values()), 324 * 1024)
        self.assertLessEqual(348 * 1024, MiB)
        self.assertEqual(m['requests']['natural/RESIDENT_R/0/0']['capture_counts']['owned_events'], 1)
        self.assertGreater(m['requests']['natural/RESIDENT_R/0/1']['metadata_byte_limit'], 5 * MiB)
        self.assertEqual(sum(len(x) for x in m['stage_check_ids'].values()), 261)
        self.assertEqual([len(m['stage_check_ids'][s]) for s in G.ORDER], [27, 81, 72, 81])

    def test_total_storage_exact_no_silent_increase(self):
        b = resource_budget()
        raw = 76 * (3 * 603979776 + 132 * 607744)
        metadata = 380 * MiB
        journal = 512 * MiB
        all_raw = raw + metadata + journal
        archive = (102 * all_raw + 99) // 100 + 16 * MiB
        total = 2 * all_raw + archive + 8 * GiB + 100 * GiB
        self.assertEqual((KV_BYTES, VECTOR_BYTES), (603979776, 607744))
        self.assertEqual(total, 553094505923)
        self.assertEqual(b['required_disk_bytes'], total)
        self.assertEqual(b['build_artifacts_bytes'] + b['worker_logs_bytes'] + b['controller_logs_bytes'] + b['controller_state_indices_bytes'], 8 * GiB)
        self.assertLessEqual(20 * 12 * MiB, b['worker_logs_bytes'])
        self.assertLess(250100 * 2048, b['journal_bytes'])

    def test_input_pin_checks_full_bytes_even_same_operation_count(self):
        actual = G.sha
        def changed(p):
            value = actual(p)
            if p.name == 'NATIVE_JOB_TEMPLATE.json':
                value['sha256'] = '0' * 64
            return value
        with patch.object(G, 'sha', side_effect=changed):
            self.assertRaisesRegex(ValueError, 'Frozen input identity', G.load_manifest)

    def test_null_cold_ids_are_unresolved_not_fabricated(self):
        t = json.loads((G.OLD / 'NATIVE_JOB_TEMPLATE.json').read_text())
        cold = next(j for j in t['jobs'] if j['worker_id'] == 'COLD_CANONICAL_ORACLE/NATURAL')
        self.assertIsNone(cold['episodes'][0]['operations'][0]['canonical_ids'])
        self.assertIsNone(cold['episodes'][0]['operations'][1]['canonical_ids'])
        r = G.static_rpc_bound(t)
        self.assertEqual(r['native_RPC_upper_bound'], 199196)
        self.assertEqual(r['planned_states']['state_phases'], 252)
        self.assertEqual(r['planned_states']['KV_chunks'], 29088)
        self.assertEqual(r['including_failure_states']['KV_chunks'], 36000)
        self.assertLess(r['native_RPC_upper_bound'], 250000)
        self.assertIsNone(cold['episodes'][0]['operations'][1]['canonical_ids'])

    def test_manifest_digest_canonical_without_own_field_and_no_grant(self):
        m = G.load_manifest()
        v = copy.deepcopy(m)
        expected = v.pop('manifest_sha256')
        self.assertEqual(hashlib.sha256(json.dumps(v, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest(), expected)
        v['run_id'] = 'CPU-LATE-BINDING'
        bound = G.finalize_manifest_cpu(v)
        self.assertNotEqual(expected, bound['manifest_sha256'])
        self.assertIsNone(bound['approval'])
        self.assertFalse(bound['native_execution_authorized'])
        v['native_execution_authorized'] = True
        self.assertRaises(ValueError, G.finalize_manifest_cpu, v)

    def test_injected_complete_mock_resource_pass_is_not_native_authority(self):
        m, s, now = cpu_fixture()
        r = ResourcePolicy(m).check(s, now)
        self.assertEqual(r['status'], 'PASS')
        self.assertFalse(r['native_execution_authorized'])

    def test_missing_stale_unknown_and_expired_conditions_fail_closed(self):
        mutations = [
            ('disk', lambda s: s.update(disk_available_bytes=FROZEN_SPACE_BYTES - 1), 'FAIL'),
            ('RAM', lambda s: s.update(RAM_available_bytes=48 * GiB - 1), 'FAIL'),
            ('RSS', lambda s: s.update(worker_RSS_bytes=24 * GiB + 1), 'FAIL'),
            ('freshness', lambda s: s.update(observed_mono=90.), 'FAIL'),
            ('UUID', lambda s: s['gpu'].update(uuid_sha256='b' * 64), 'FAIL'),
            ('VRAM', lambda s: s['gpu'].update(free_bytes=2 * GiB - 1), 'FAIL'),
            ('foreign', lambda s: s['process_ownership'].update(foreign_target_process_count=1), 'FAIL'),
            ('unknown', lambda s: s['process_ownership'].pop('identity_verified'), 'BLOCKED'),
            ('lock', lambda s: s['locks'].update(conflict=True), 'FAIL'),
            ('lease', lambda s: s['enforcement']['GPU_exclusive'].update(expires_mono=100.), 'FAIL'),
            ('group', lambda s: s['enforcement']['memory'].update(status='AVAILABLE_NOT_ACTIVATED'), 'BLOCKED'),
            ('RSS-limit', lambda s: s['enforcement']['memory'].update(mechanism='RLIMIT_RSS'), 'BLOCKED'),
            ('peak', lambda s: s['gpu'].update(preflight_status='NOT_RUN'), 'BLOCKED'),
            ('build', lambda s: s.update(retained_build_artifact_bytes=7 * GiB + 1), 'FAIL'),
        ]
        for name, mutate, expected in mutations:
            with self.subTest(name=name):
                m, s, now = cpu_fixture()
                mutate(s)
                self.assertEqual(ResourcePolicy(m).check(s, now)['status'], expected)

    def test_snapshot_and_real_template_unbound(self):
        self.assertEqual(ResourcePolicy(G.load_manifest()).check(None, {})['status'], 'NOT_RUN')
        _, s, now = cpu_fixture()
        self.assertEqual(ResourcePolicy(G.load_manifest()).check(s, now)['status'], 'BLOCKED')

    def test_last_launch_only_blocks_new_work_and_RAM_reserve_is_continuous(self):
        m, s, _ = cpu_fixture()
        now = dict(wall=8000., mono=7100.)
        s.update(observed_wall=8000., observed_mono=7100., RAM_available_bytes=30 * GiB, worker_RSS_bytes=20 * GiB)
        self.assertEqual(ResourcePolicy(m).check(s, now, 'BEFORE_LAUNCH')['status'], 'FAIL')
        self.assertEqual(ResourcePolicy(m).check(s, now, 'DURING_WORK')['status'], 'PASS')
        self.assertEqual(ResourcePolicy(m).check(s, now, 'UNRECOGNIZED')['status'], 'FAIL')

    def test_monotonic_deadline_cannot_be_extended_by_wall_rollback(self):
        m, s, _ = cpu_fixture()
        now = dict(wall=1001., mono=18101.)
        s.update(observed_wall=now['wall'], observed_mono=now['mono'])
        self.assertEqual(ResourcePolicy(m).check(s, now)['status'], 'FAIL')

    def test_malformed_resource_and_quota_increase_do_not_pass(self):
        m, s, now = cpu_fixture()
        s['gpu'] = []
        self.assertEqual(ResourcePolicy(m).check(s, now)['status'], 'FAIL')
        m, s, now = cpu_fixture()
        m['limits']['journal_bytes'] += 1
        self.assertEqual(ResourcePolicy(m).check(s, now)['status'], 'FAIL')

    def test_cgroup_mock_files_and_closed_actual_activation(self):
        root = Path(OUT) / self._testMethodName
        fs = MockCgroupFS(root)
        plan = DelegatedCgroupPlan('CPU_ONLY', 'hs-test', os.geteuid(), 900, 'CPU-MOCK-PARENT')
        child = dict(pid=901, parent_pid=900, owner_uid=os.geteuid(), start_time=1, boot_id_sha256='b' * 64)
        r = plan.rehearse(fs, child)
        self.assertEqual(r['status'], 'CPU_MOCK_REHEARSAL_PASS_NOT_ACTIVATED')
        self.assertEqual((fs.parent / 'hs-test/memory.max').read_text(), str(24 * GiB) + '\n')
        self.assertEqual(r['actual_cgroups_modified'], 0)
        before = list(fs.writes)
        self.assertRaises(ResourceBlocked, plan.activate_actual, approval=True, filesystem=fs)
        self.assertEqual(before, fs.writes)

    def test_cgroup_foreign_or_nonchild_and_reentry_rejected(self):
        fs = MockCgroupFS(Path(OUT) / self._testMethodName)
        plan = DelegatedCgroupPlan('CPU_ONLY', 'hs-test', os.geteuid(), 900, 'CPU-MOCK-PARENT')
        child = dict(pid=901, parent_pid=900, owner_uid=os.geteuid(), start_time=1, boot_id_sha256='b' * 64)
        for key, value in [('parent_pid', 1), ('owner_uid', os.geteuid() + 1), ('start_time', 0), ('boot_id_sha256', None)]:
            wrong = dict(child)
            wrong[key] = value
            self.assertRaises(ResourceBlocked, plan.rehearse, fs, wrong)
        plan.rehearse(fs, child)
        self.assertRaises(FileExistsError, plan.rehearse, fs, child)

    def test_cgroup_parent_inode_replacement_rejected(self):
        fs = MockCgroupFS(Path(OUT) / self._testMethodName)
        plan = DelegatedCgroupPlan('CPU_ONLY', 'hs-test', os.geteuid(), 900, 'CPU-MOCK-PARENT')
        fs.parent.rename(fs.root / 'original_parent_preserved')
        fs.parent.mkdir(mode=0o700)
        child = dict(pid=901, parent_pid=900, owner_uid=os.geteuid(), start_time=1, boot_id_sha256='b' * 64)
        self.assertRaises(ResourceBlocked, plan.rehearse, fs, child)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--out', required=True)
    args = p.parse_args()
    root = Path(args.out)
    if not root.is_absolute() or root.exists():
        raise SystemExit('Fresh absolute resource CPU-test output required')
    root.mkdir(mode=0o700)
    OUT = str(root)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ResourceTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    value = dict(status='PASS' if result.wasSuccessful() else 'FAIL', tests=result.testsRun,
                 failures=len(result.failures), errors=len(result.errors),
                 native_or_model_operations=0, actual_cgroup_activations=0,
                 scope='INJECTED_CPU_RESOURCE_AND_ORDINARY_FILE_TESTS_ONLY')
    (root / 'RESULT.json').write_text(json.dumps(value, indent=2) + '\n')
    print(json.dumps(value))
    raise SystemExit(0 if result.wasSuccessful() else 1)
