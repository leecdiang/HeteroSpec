"""CPU-only resource-domain mocks. No model/native imports or real cgroups."""
import argparse
import copy
from dataclasses import FrozenInstanceError
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from resource_domain import (DomainBinding, DomainDenied, ResourceDomain,
                             OrdinaryCgroupAdapter, canonical, resource_manifest,
                             validate_parent, read_process_peer, KernelCgroupAdapter,
                             limit_operations, GiB, MiB, TOTAL_DISK)
from resource_manifest import load_execution_manifest, PRIOR
from cpu_resource_fixture import cpu_domain_factory

OUT = None


def fixture():
    uid = os.geteuid()
    supervisor = dict(pid=900, start_time=10, boot_id_sha256='b' * 64, uid=uid)
    parent = dict(path_sha256='c' * 64, device=11, inode=22, uid=uid,
                  mount_id=33, controllers=['memory', 'pids'])
    raw = dict(run_id='CPU_RESOURCE_DOMAIN', manifest_sha256='a' * 64,
               owner_uid=uid, device_uuid_sha256='d' * 64,
               stage='RESIDENT_R', worker_id='RESIDENT_R/NATURAL',
               executable_sha256='e' * 64, launcher_executable_sha256='2' * 64, lease_sha256='f' * 64,
               lease_issuer_sha256='1' * 64, supervisor=supervisor,
               parent=parent, window=dict(start_wall=1000., start_mono=100.,
                 deadline_wall=19000., deadline_mono=18100.,
                 last_launch_wall=7600., last_launch_mono=6700.))
    binding = DomainBinding.from_dict(raw)
    parent_evidence = {**parent, 'type': 'domain', 'delegated': True,
                       'writable_memory': True, 'writable_pids': True,
                       'no_foreign_processes': True}
    now = dict(wall=1001., mono=101.)
    child = {**supervisor, 'pid': 901, 'start_time': 11, 'parent_pid': 900,
             'parent_start_time': 10, 'exe_sha256': '2' * 64}
    lease = dict(verified=True, sha256='f' * 64, issuer_sha256='1' * 64,
                 run_id=raw['run_id'], device_uuid_sha256='d' * 64, owner_uid=uid,
                 heartbeat_wall=1001., heartbeat_mono=101.,
                 expires_wall=19000., expires_mono=18100.)
    snapshot = dict(parent=parent_evidence, lease=lease,
                    domain_sha256=binding.sha256, manifest_sha256='a' * 64,
                    observed_wall=1001., observed_mono=101.,
                    supervisor=supervisor, supervisor_alive=True,
                    locks=dict(verified=True, conflict=False, domain_sha256=binding.sha256),
                    disk_available_bytes=TOTAL_DISK, RAM_available_bytes=48 * GiB,
                    GPU_free_bytes=2 * GiB, domain_memory_current_bytes=0,
                    domain_pids_current=1, device_uuid_sha256='d' * 64,
                    foreign_target_processes=0, unknown_target_processes=0,
                    retained_build_bytes=7 * GiB, membership_verified=True,
                    only_owned_descendants=True, child=child)
    return binding, snapshot, now, child, supervisor


class ResourceDomainTests(unittest.TestCase):
    def adapter(self, suffix='domain', **kwargs):
        return OrdinaryCgroupAdapter(Path(OUT) / (self._testMethodName + '-' + suffix), **kwargs)

    def test_bound_digest_is_canonical_and_immutable(self):
        binding, _, _, _, _ = fixture()
        self.assertEqual(hashlib.sha256(canonical(binding.as_dict())).hexdigest(), binding.sha256)
        value = binding.as_dict()
        value['supervisor']['pid'] = 99
        self.assertNotEqual(value, binding.as_dict())
        self.assertRaises(FrozenInstanceError, setattr, binding, 'encoded', b'bad')
        self.assertRaises(DomainDenied, DomainBinding, b'{}')

    def test_every_bound_identity_changes_domain_sha(self):
        b, _, _, _, _ = fixture()
        for key, replacement in [('run_id', 'OTHER'), ('stage', 'REPEAT_RESIDENT_R'),
                                 ('worker_id', 'OTHER'), ('manifest_sha256', '9' * 64),
                                 ('device_uuid_sha256', '9' * 64), ('lease_sha256', '9' * 64),
                                 ('executable_sha256', '9' * 64)]:
            with self.subTest(key=key):
                v = b.as_dict()
                v[key] = replacement
                self.assertNotEqual(DomainBinding.from_dict(v).sha256, b.sha256)

    def test_missing_unknown_or_unresolved_fields_rejected(self):
        b, _, _, _, _ = fixture()
        for change in (lambda x: x.pop('lease_sha256'), lambda x: x.update(approval=True),
                       lambda x: x.update(device_uuid_sha256=None),
                       lambda x: x['window'].update(deadline_mono=18101.),
                       lambda x: x['parent'].update(controllers=['memory']),
                       lambda x: x['supervisor'].update(start_time=0)):
            v = b.as_dict()
            change(v)
            self.assertRaises(DomainDenied, DomainBinding.from_dict, v)

    def test_before_launch_validates_without_writes_or_permission(self):
        b, s, now, _, _ = fixture()
        a = self.adapter()
        d = ResourceDomain(b, a)
        r = d.before_launch(s, now)
        self.assertEqual(r['status'], 'CPU_MOCK_POLICY_PASS_NOT_ADMISSION')
        self.assertFalse(r['native_execution_authorized'])
        self.assertEqual(a.writes, [])

    def test_zero_argument_hooks_use_injected_observer_and_clock(self):
        b, s, now, child, parent = fixture()
        d = ResourceDomain(b, self.adapter(), observer=lambda: copy.deepcopy(s), clock=lambda: dict(now))
        d.before_launch()
        d.bind_child(child, parent)
        self.assertEqual(d.assert_live()['status'], 'CPU_MOCK_POLICY_PASS_NOT_ADMISSION')

    def test_exact_mock_operations_and_membership(self):
        b, s, now, child, parent = fixture()
        a = self.adapter()
        d = ResourceDomain(b, a)
        d.bind_child(child, parent, s, now)
        self.assertEqual(a.writes, ['BINDING.json', 'memory.max', 'pids.max', 'cgroup.procs.901'])
        self.assertEqual((a.root / 'memory.max').read_text(), str(24 * GiB))
        self.assertEqual((a.root / 'pids.max').read_text(), '128')
        self.assertFalse(d.assert_live(s, now)['actual_cgroup_activated'])

    def test_actual_activation_is_permanently_denied_before_side_effects(self):
        b, _, _, _, _ = fixture()
        a = self.adapter()
        d = ResourceDomain(b, a)
        self.assertRaises(DomainDenied, d.activate_actual, approval=True, delegated=True)
        self.assertEqual(a.writes, [])
        self.assertEqual(list(a.root.iterdir()), [])

    def test_concrete_kernel_operation_plan_is_closed_before_path_or_callback(self):
        b, _, _, _, _ = fixture()
        k = KernelCgroupAdapter(b, '/never-open-this-unapproved-path')
        called = []
        self.assertRaises(DomainDenied, k.activate_actual, lambda *args: called.append(args))
        self.assertEqual(called, [])
        self.assertFalse(k.operation_plan()['numeric_PID_attach'])
        self.assertEqual(k.operation_plan()['limits'], {leaf: raw.decode() for leaf, raw in limit_operations()})
        self.assertRaises(DomainDenied, ResourceDomain, b, k)

    def test_absent_adapter_does_not_admit_an_actual_child(self):
        b, s, now, child, parent = fixture()
        d = ResourceDomain(b)
        d.before_launch(s, now)
        self.assertRaises(DomainDenied, d.bind_child, child, parent, s, now)
        self.assertTrue(d.poisoned)

    def test_missing_stale_or_conflicting_evidence_poison_no_retry(self):
        mutations = [lambda s: s.update(observed_mono=90.),
                     lambda s: s['parent'].update(inode=23),
                     lambda s: s['parent'].update(delegated=False),
                     lambda s: s.update(domain_sha256='9' * 64),
                     lambda s: s['lease'].update(verified=False),
                     lambda s: s['lease'].update(expires_wall=18999.),
                     lambda s: s['lease'].update(heartbeat_mono=90.),
                     lambda s: s['supervisor'].update(start_time=99),
                     lambda s: s.update(supervisor_alive=False),
                     lambda s: s['locks'].update(verified=False),
                     lambda s: s['locks'].update(conflict=True),
                     lambda s: s.update(unknown_target_processes=1),
                     lambda s: s.update(foreign_target_processes=1),
                     lambda s: s.update(device_uuid_sha256='9' * 64)]
        for i, mutate in enumerate(mutations):
            with self.subTest(index=i):
                b, s, now, _, _ = fixture()
                original = copy.deepcopy(s)
                mutate(s)
                d = ResourceDomain(b)
                self.assertRaises(DomainDenied, d.before_launch, s, now)
                self.assertTrue(d.poisoned)
                self.assertRaises(DomainDenied, d.before_launch, original, now)

    def test_all_resource_floors_and_hard_caps(self):
        values = [('disk_available_bytes', TOTAL_DISK - 1), ('RAM_available_bytes', 48 * GiB - 1),
                  ('GPU_free_bytes', 2 * GiB - 1), ('domain_memory_current_bytes', 24 * GiB + 1),
                  ('domain_pids_current', 129), ('retained_build_bytes', 7 * GiB + 1)]
        for key, value in values:
            with self.subTest(key=key):
                b, s, now, _, _ = fixture()
                s[key] = value
                self.assertRaises(DomainDenied, ResourceDomain(b).before_launch, s, now)

    def test_monotonic_deadline_and_last_start_cannot_be_renewed(self):
        b, s, _, _, _ = fixture()
        for now in (dict(wall=1001., mono=18100.), dict(wall=7601., mono=6701.)):
            s['observed_wall'], s['observed_mono'] = now['wall'], now['mono']
            s['lease']['heartbeat_wall'], s['lease']['heartbeat_mono'] = now['wall'], now['mono']
            self.assertRaises(DomainDenied, ResourceDomain(b).before_launch, s, now)

    def test_later_live_guard_allows_protected_RAM_floor_but_no_escape(self):
        b, s, now, child, parent = fixture()
        d = ResourceDomain(b, self.adapter())
        d.bind_child(child, parent, s, now)
        s['RAM_available_bytes'] = 24 * GiB
        self.assertEqual(d.assert_live(s, now)['status'], 'CPU_MOCK_POLICY_PASS_NOT_ADMISSION')
        s['membership_verified'] = False
        self.assertRaises(DomainDenied, d.assert_live, s, now)

    def test_pid_reuse_foreign_uid_wrong_parent_and_executable_rejected(self):
        for key, value in [('start_time', 0), ('uid', os.geteuid() + 1),
                           ('parent_pid', 99), ('parent_start_time', 99),
                           ('exe_sha256', '9' * 64)]:
            b, s, now, child, parent = fixture()
            child[key] = value
            self.assertRaises(DomainDenied, ResourceDomain(b, self.adapter(key)).bind_child,
                              child, parent, s, now)

    def test_contiguous_ancestry_required_not_just_last_supervisor(self):
        b, s, now, child, supervisor = fixture()
        parent = {**supervisor, 'pid': 902, 'start_time': 12,
                  'parent_pid': 900, 'parent_start_time': 10,
                  'ancestor_identities': [supervisor]}
        child.update(parent_pid=902, parent_start_time=12)
        d = ResourceDomain(b, self.adapter('valid'))
        d.bind_child(child, parent, s, now)
        parent['parent_pid'] = 999
        self.assertRaises(DomainDenied, ResourceDomain(b, self.adapter('broken')).bind_child,
                          child, parent, s, now)

    def test_bridge_four_field_identity_enriched_without_new_process(self):
        b, s, now, child, parent = fixture()
        boot = 'CPU-MOCK-BOOT'
        digest = hashlib.sha256(boot.encode()).hexdigest()
        value = b.as_dict()
        value['supervisor']['boot_id_sha256'] = digest
        b = DomainBinding.from_dict(value)
        parent['boot_id_sha256'] = child['boot_id_sha256'] = digest
        s.update(domain_sha256=b.sha256, supervisor=parent, child=child)
        s['locks']['domain_sha256'] = b.sha256
        minimal = lambda p: dict(pid=p['pid'], start_ticks=p['start_time'], uid=p['uid'], boot_id=boot)
        d = ResourceDomain(b, self.adapter(), process_reader=lambda pid: copy.deepcopy(child))
        d.bind_child(minimal(child), minimal(parent), s, now)
        self.assertEqual(d.peer['parent_pid'], parent['pid'])
        self.assertEqual(d.peer['exe_sha256'], value['launcher_executable_sha256'])

    def test_four_field_exit_never_reads_dead_child_proc(self):
        b, s, now, child, parent = fixture()
        boot = 'CPU-EXIT-BOOT'
        digest = hashlib.sha256(boot.encode()).hexdigest()
        value = b.as_dict()
        value['supervisor']['boot_id_sha256'] = digest
        b = DomainBinding.from_dict(value)
        parent['boot_id_sha256'] = child['boot_id_sha256'] = digest
        s.update(domain_sha256=b.sha256, supervisor=parent, child=child)
        s['locks']['domain_sha256'] = b.sha256
        d = ResourceDomain(b, self.adapter())
        d.bind_child(child, parent, s, now)
        def no_dead_proc(_pid):
            raise AssertionError('A completed bound child must not be reread through /proc')
        d.process_reader = no_dead_proc
        minimal = dict(pid=child['pid'], start_ticks=child['start_time'], uid=child['uid'], boot_id=boot)
        s.pop('child')
        self.assertEqual(d.assert_after_exit(minimal, s, now)['status'], 'CPU_MOCK_POLICY_PASS_NOT_ADMISSION')
        self.assertTrue(d.owned_exit_observed)

    def test_readonly_proc_identity_is_current_cpu_process(self):
        p = read_process_peer(os.getpid())
        self.assertEqual(p['pid'], os.getpid())
        self.assertEqual(p['uid'], os.geteuid())
        self.assertGreater(p['start_time'], 0)
        self.assertEqual(len(p['exe_sha256']), 64)

    def test_cpu_factory_distinguishes_real_reads_and_synthetic_authority(self):
        root = Path(OUT) / (self._testMethodName + '-fixture')
        root.mkdir(mode=0o700)
        current = read_process_peer(os.getpid())
        manifest = dict(run_id='CPU_FACTORY_TEST', manifest_sha256='a' * 64,
                        identity_bindings=dict(launcher=current['exe_sha256']),
                        window=dict(deadline_wall=time.time() + 60,
                                    deadline_mono=time.monotonic() + 60))
        worker = dict(stage='RESIDENT_R', id='RESIDENT_R/NATURAL',
                      executable_sha256=current['exe_sha256'])
        d = cpu_domain_factory(root, SimpleNamespace(manifest=manifest), worker, 'f' * 64, 'd' * 64)
        snapshot = d.observer()
        self.assertIn('disk_available', snapshot['real_reads'])
        self.assertIn('external_GPU_lease', snapshot['synthetic'])
        self.assertEqual(snapshot['complete_retained_build_selection'], 'NOT_MEASURED_NO_ADMISSION')
        self.assertFalse(snapshot['actual_cgroup_limits_activated'])
        self.assertEqual(d.adapter.writes, [])

    def test_partial_write_preserves_files_poison_and_reentry_denies(self):
        b, s, now, child, parent = fixture()
        a = self.adapter(fail_after=1)
        d = ResourceDomain(b, a)
        self.assertRaises(DomainDenied, d.bind_child, child, parent, s, now)
        self.assertEqual(a.writes, ['BINDING.json'])
        self.assertTrue((a.root / 'BINDING.json').exists())
        self.assertTrue(d.poisoned)
        self.assertRaises(DomainDenied, d.bind_child, child, parent, s, now)

    def test_limit_change_inode_replace_and_symlink_fail_closed(self):
        b, s, now, child, parent = fixture()
        for kind in ('limit', 'inode', 'symlink'):
            a = self.adapter(kind)
            d = ResourceDomain(b, a)
            d.bind_child(child, parent, s, now)
            if kind == 'limit':
                (a.root / 'memory.max').write_text(str(25 * GiB))
            elif kind == 'inode':
                a.root.rename(a.root.with_name(a.root.name + '-preserved'))
                a.root.mkdir(mode=0o700)
            else:
                (a.root / 'memory.max').rename(a.root / 'original.memory.max')
                (a.root / 'memory.max').symlink_to(a.root / 'original.memory.max')
            self.assertRaises((DomainDenied, OSError), d.assert_live, s, now)

    def test_close_preserves_remaining_processes_and_does_not_claim_gpu_kill(self):
        b, _, _, _, _ = fixture()
        d = ResourceDomain(b)
        r = d.close_result('CPU_ONLY', [901])
        self.assertEqual(r['status'], 'BLOCKED_OWNED_PROCESSES_REMAIN')
        self.assertFalse(r['resource_release_verified'])
        self.assertFalse(r['GPU_completion_or_preemption_guaranteed'])
        self.assertEqual(r['actual_signals_sent'], 0)
        self.assertRaises(DomainDenied, d.before_launch)

    def test_typed_preexec_postexec_and_known_exit_are_not_success(self):
        b, s, now, child, parent = fixture()
        d = ResourceDomain(b, self.adapter())
        d.bind_child(child, parent, s, now)
        self.assertEqual(d.image_phase, 'PREEXEC')
        worker = {**child, 'exe_sha256': 'e' * 64}
        s['child'] = worker
        d.observe_postexec(worker, s, now)
        self.assertEqual(d.image_phase, 'POSTEXEC')
        d.assert_live(s, now)
        d.observe_owned_exit(worker, kernel_exit_observed=True)
        s.pop('child')
        self.assertEqual(d.assert_live(s, now)['status'], 'CPU_MOCK_POLICY_PASS_NOT_ADMISSION')
        close = d.close_result('CPU_WORKER_EXIT')
        self.assertFalse(close['resource_release_verified'])
        self.assertFalse(close['GPU_completion_or_preemption_guaranteed'])

    def test_unobserved_or_wrong_identity_exit_and_postexec_replay_reject(self):
        b, s, now, child, parent = fixture()
        d = ResourceDomain(b, self.adapter())
        d.bind_child(child, parent, s, now)
        self.assertRaises(DomainDenied, d.observe_owned_exit, child, False)
        d = ResourceDomain(b, self.adapter('other'))
        d.bind_child(child, parent, s, now)
        wrong = {**child, 'start_time': 99}
        self.assertRaises(DomainDenied, d.observe_owned_exit, wrong, True)

    def test_bridge_caps_recompute_exact_old_total_not_extra_quota(self):
        m = resource_manifest()
        self.assertEqual(m['required_disk_bytes'], 553094505923)
        self.assertEqual(sum(m['artifact_subcaps'].values()), 8 * GiB)
        self.assertEqual(m['domain_records_max'] * m['domain_record_bytes_max'], 16 * MiB)
        self.assertLessEqual(2471 + m['bridge_and_domain_entries_max'], m['archive_entries_max'])
        self.assertLess(250100 * 2048, m['journal_bytes'])
        self.assertEqual((m['planned_requests'], m['requests'], m['planned_rows'], m['rows'], m['placements']),
                         (72, 76, 69354, 85738, 10))
        self.assertIsNone(m['approval'])
        self.assertFalse(m['native_execution_authorized'])

    def test_execution_manifest_preserves_exact_old_fixtures_and_caps(self):
        original = json.loads(PRIOR.read_text())
        m = load_execution_manifest()
        self.assertEqual(m['requests'], original['requests'])
        self.assertEqual(m['deployments'], original['deployments'])
        self.assertEqual(m['limits'], original['limits'])
        self.assertEqual(m['failure_reserve'], original['failure_reserve'])
        self.assertEqual(m['stage_check_ids'], original['stage_check_ids'])
        self.assertEqual(m['bridge_overhead']['immutable_record_bytes_product'], 4 * MiB)
        self.assertLess(m['bridge_overhead']['conservative_RPC_plus_bridge'], 250000)
        self.assertIsNone(m['build_selection']['measured_logical_bytes'])
        self.assertIsNone(m['approval'])
        digest = m.pop('manifest_sha256')
        self.assertEqual(hashlib.sha256(canonical(m)).hexdigest(), digest)

    def test_even_same_JSON_with_whitespace_changed_rejects_prior_pin(self):
        target = Path(OUT) / 'prior-pin-modified.json'
        target.write_bytes(PRIOR.read_bytes() + b'\n')
        self.assertRaises(DomainDenied, load_execution_manifest, target)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    out = Path(args.out)
    if not out.is_absolute() or out.exists():
        raise SystemExit('Fresh absolute ordinary CPU-test output required')
    out.mkdir(mode=0o700)
    OUT = str(out)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ResourceDomainTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    receipt = dict(status='PASS' if result.wasSuccessful() else 'FAIL', tests=result.testsRun,
                   errors=len(result.errors), failures=len(result.failures),
                   actual_cgroup_changes=0, native_model_context_placement_forwards=0,
                   scope='CPU_ONLY_ORDINARY_FILE_REHEARSAL_NOT_KERNEL_ENFORCEMENT',
                   resource_envelope=resource_manifest())
    (out / 'RESULT.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    print(json.dumps(receipt))
    raise SystemExit(0 if result.wasSuccessful() else 1)
