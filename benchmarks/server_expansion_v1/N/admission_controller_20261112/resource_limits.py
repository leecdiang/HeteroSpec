"""Pure CPU resource arithmetic and injected evidence checks. No native APIs."""
import copy
import math
import os
from pathlib import Path
import re
from dataclasses import dataclass

MiB = 1024 ** 2
GiB = 1024 ** 3
KV_BYTES = 36 * 8 * 4096 * 128 * 2 * 2
VECTOR_BYTES = 151936 * 4
FROZEN_SPACE_BYTES = 553094505923
RAW_PER_REQUEST = 3 * KV_BYTES + 132 * VECTOR_BYTES
STATE_METADATA = MiB + 2 * 64 * 1024
OWNED_METADATA = 3 * 64 * 1024
RECORD_METADATA = 64 * 1024
# Worst final natural request: 3 states+RESET, two ownership events,
# three transition records, one producer receipt, six prepaid1KiB markers.
REQUEST_METADATA = 4 * STATE_METADATA + 2 * OWNED_METADATA + 3 * RECORD_METADATA + MiB + 6 * 1024


def resource_budget():
    raw = 76 * RAW_PER_REQUEST
    metadata = 76 * 5 * MiB
    journal = 512 * MiB
    raw_all = raw + metadata + journal
    archive = (raw_all * 102 + 99) // 100 + 16 * MiB
    build = 8 * GiB
    total = raw_all + archive + raw_all + build + 100 * GiB
    if total != FROZEN_SPACE_BYTES:
        raise ValueError('Frozen resource envelope changed')
    planned_metadata = 252 * STATE_METADATA + 72 * OWNED_METADATA + 99 * RECORD_METADATA + 32 * MiB
    failure_metadata = 4 * (4 * STATE_METADATA + 2 * OWNED_METADATA + 3 * RECORD_METADATA + MiB)
    if planned_metadata + failure_metadata + MiB > metadata:
        raise ValueError('Metadata no longer fits the original global envelope')
    return {
        'raw_bytes': raw, 'metadata_bytes': metadata, 'capture_bytes': raw + metadata,
        'journal_bytes': journal, 'raw_and_journal_bytes': raw_all,
        'archive_bytes': archive, 'restore_bytes': raw_all,
        'build_text_bytes': build, 'build_artifacts_bytes': 7 * GiB,
        'worker_logs_bytes': 256 * MiB, 'controller_logs_bytes': 256 * MiB,
        'controller_state_indices_bytes': 512 * MiB,
        'protected_disk_bytes': 100 * GiB, 'required_disk_bytes': total,
        'archive_entries': 4096, 'archive_header_bytes': 16 * MiB,
        'planned_metadata_composition_bytes': planned_metadata,
        'failed_metadata_composition_bytes': failure_metadata,
        'partial_marker_bytes': MiB, 'prepaid_marker_bytes_per_capture': 1024,
        'max_capture_directories': 348, 'known_archive_entries': 2471,
        'worker_RSS_bytes': 24 * GiB, 'protected_RAM_bytes': 24 * GiB,
        'prelaunch_RAM_bytes': 48 * GiB, 'minimum_free_VRAM_bytes': 2 * GiB,
        'max_window_seconds': 18000, 'last_launch_offset_seconds': 6600,
        'native_end_offset_seconds': 7200, 'worker_timeout_seconds': 600,
        'probe_timeout_seconds': 120, 'snapshot_max_age_seconds': 10,
    }


def evaluate_resources(snapshot, policy, now, phase='BEFORE_LAUNCH'):
    """Evaluate provided evidence only; PASS never grants native permission.

    now={'wall': epochseconds, 'mono': monotonicseconds}; both are required.
    snapshot is injected, never collected through a driver or device API here.
    """
    return ResourcePolicy(policy).check(snapshot, now, phase)


class ResourcePolicy:
    def __init__(self, manifest):
        self.manifest = copy.deepcopy(manifest)
        self.limits = resource_budget()

    def check(self, snapshot, now, phase='BEFORE_LAUNCH'):
        gates = []

        def gate(name, status, reason, **evidence):
            gates.append(dict(name=name, status=status, reason=reason, **evidence))

        def number(value):
            return type(value) in (int, float) and math.isfinite(value)

        def minimum(name, value, required):
            if not number(value) or value < 0:
                gate(name, 'BLOCKED', 'Missing/invalid measured resource')
            else:
                gate(name, 'PASS' if value >= required else 'FAIL', 'Provided measurement versus hard proposal floor', measured=value, required=required)

        if snapshot is None:
            return dict(status='NOT_RUN', gates=[dict(name='resource_snapshot', status='NOT_RUN', reason='No snapshot supplied')], native_execution_authorized=False)
        if not isinstance(snapshot, dict) or not isinstance(now, dict):
            return dict(status='FAIL', gates=[dict(name='schema', status='FAIL', reason='Snapshot and dual clock must be dictionaries')], native_execution_authorized=False)
        if phase not in ('BEFORE_LAUNCH', 'BEFORE_PREFLIGHT', 'DURING_WORK', 'CLOSEOUT'):
            return dict(status='FAIL', gates=[dict(name='phase', status='FAIL', reason='Unknown resource-check phase')], native_execution_authorized=False)

        def mapping(value, name):
            if not isinstance(value, dict):
                gate(name, 'FAIL', 'Malformed nested resource evidence')
                return {}
            return value

        proposed = mapping(self.manifest.get('limits', {}), 'budget_limits_schema')
        ceilings = {**self.limits, 'requests': 76, 'rows': 85738,
                    'backend_inits': 10, 'models': 10, 'contexts': 10, 'placements': 10}
        for key in ('requests', 'rows', 'backend_inits', 'models', 'contexts', 'placements',
                    'raw_bytes', 'metadata_bytes', 'capture_bytes', 'journal_bytes', 'build_text_bytes'):
            value = proposed.get(key)
            if type(value) is not int or value < 0:
                gate('budget_' + key, 'BLOCKED', 'Bound integer resource quota absent')
            else:
                gate('budget_' + key, 'PASS' if value <= ceilings[key] else 'FAIL', 'No resource/quota expansion beyond the frozen proposal')
        wall, mono = now.get('wall'), now.get('mono')
        observed_wall, observed_mono = snapshot.get('observed_wall'), snapshot.get('observed_mono')
        if not all(number(x) for x in (wall, mono, observed_wall, observed_mono)):
            gate('freshness', 'BLOCKED', 'Both measurement clocks are required')
        else:
            ages = (wall - observed_wall, mono - observed_mono)
            gate('freshness', 'PASS' if all(0 <= a <= self.limits['snapshot_max_age_seconds'] for a in ages) else 'FAIL', 'Stale/future snapshot cannot establish current resources', ages=list(ages))

        window = mapping(self.manifest.get('window', {}), 'window_schema')
        keys = ('start_wall', 'start_mono', 'deadline_wall', 'deadline_mono', 'last_launch_wall', 'last_launch_mono')
        if not all(number(window.get(k)) for k in keys) or not number(wall) or not number(mono):
            gate('window', 'BLOCKED', 'Absolute dual-clock start/deadline/last-launch window is unbound')
        else:
            duration = (window['deadline_wall'] - window['start_wall'], window['deadline_mono'] - window['start_mono'])
            valid = (all(0 < d <= 18000 for d in duration)
                     and window['start_wall'] <= window['last_launch_wall'] <= window['deadline_wall']
                     and window['start_mono'] <= window['last_launch_mono'] <= window['deadline_mono']
                     and wall >= window['start_wall'] and mono >= window['start_mono']
                     and wall < window['deadline_wall'] and mono < window['deadline_mono'])
            if phase in ('BEFORE_LAUNCH', 'BEFORE_PREFLIGHT'):
                valid = valid and wall <= window['last_launch_wall'] and mono <= window['last_launch_mono']
            gate('window', 'PASS' if valid else 'FAIL', 'Fixed wall and monotonic deadlines; no deadline renewal', durations=list(duration))

        minimum('disk', snapshot.get('disk_available_bytes'), self.limits['required_disk_bytes'])
        ram_floor = self.limits['prelaunch_RAM_bytes'] if phase in ('BEFORE_LAUNCH', 'BEFORE_PREFLIGHT') else self.limits['protected_RAM_bytes']
        minimum('RAM_available', snapshot.get('RAM_available_bytes'), ram_floor)
        rss = snapshot.get('worker_RSS_bytes')
        if not number(rss) or rss < 0:
            gate('worker_RSS', 'BLOCKED', 'Measured worker/process-group RSS absent')
        else:
            gate('worker_RSS', 'PASS' if rss <= self.limits['worker_RSS_bytes'] else 'FAIL', 'Sampled RSS is checked but is not itself hard enforcement', measured=rss, ceiling=self.limits['worker_RSS_bytes'])

        enforcement = mapping(snapshot.get('enforcement', {}), 'enforcement_schema')
        memory = mapping(enforcement.get('memory', {}), 'memory_schema')
        if memory.get('mechanism') != 'DELEGATED_CGROUP_V2' or memory.get('status') != 'VERIFIED' or memory.get('membership_verified') is not True or memory.get('only_owned_descendants') is not True:
            gate('memory_hard_enforcement', 'BLOCKED', 'Delegation capability alone is not an activated/verified owned cgroup; RSS polling/RLIMIT_RSS is insufficient')
        elif type(memory.get('memory_max_bytes')) is not int or not (0 < memory['memory_max_bytes'] <= self.limits['worker_RSS_bytes']):
            gate('memory_hard_enforcement', 'FAIL', 'Actual cgroup hard limit exceeds the resource contract')
        else:
            gate('memory_hard_enforcement', 'PASS', 'Injected verified owned-cgroup evidence; this checker performs no cgroup write')

        uuid = self.manifest.get('gpu_uuid_sha256')
        gpu = mapping(snapshot.get('gpu', {}), 'GPU_schema')
        if not isinstance(uuid, str) or len(uuid) != 64:
            gate('GPU_identity', 'BLOCKED', 'Allocated UUID identity is not bound')
        else:
            gate('GPU_identity', 'PASS' if gpu.get('uuid_sha256') == uuid else 'FAIL', 'Only the allocated exact UUID can qualify')
        minimum('GPU_free', gpu.get('free_bytes'), self.limits['minimum_free_VRAM_bytes'])
        if phase != 'BEFORE_PREFLIGHT':
            peak = gpu.get('preflight_peak_bytes')
            if not number(peak) or peak <= 0 or gpu.get('preflight_status') != 'PASS_NO_FORWARD':
                gate('GPU_preflight_peak', 'BLOCKED', 'Actual no-forward placement peak has not been measured/qualified')
            else:
                minimum('GPU_placement_margin', gpu.get('total_bytes'), peak + self.limits['minimum_free_VRAM_bytes'])
        external = mapping(enforcement.get('GPU_exclusive', {}), 'GPU_exclusive_schema')
        if external.get('status') != 'VERIFIED' or external.get('mechanism') != 'EXTERNAL_EXCLUSIVE_ALLOCATION' or external.get('run_id') != self.manifest.get('run_id') or external.get('uuid_sha256') != uuid:
            gate('GPU_quiet_window', 'BLOCKED', 'No verified external exclusive allocation; an idle snapshot is not a continuous quiet-window guarantee')
        elif not number(external.get('expires_wall')) or not number(external.get('expires_mono')) or not number(wall) or not number(mono) or wall >= external['expires_wall'] or mono >= external['expires_mono']:
            gate('GPU_quiet_window', 'FAIL', 'Exclusive allocation expired or clocks invalid')
        else:
            gate('GPU_quiet_window', 'PASS', 'Injected external lease remains valid; no allocation is created by this checker')

        owners = mapping(snapshot.get('process_ownership', {}), 'process_ownership_schema')
        if owners.get('identity_verified') is not True or type(owners.get('foreign_target_process_count')) is not int or type(owners.get('unknown_target_process_count')) is not int:
            gate('process_ownership', 'BLOCKED', 'Unknown target process identity/ownership')
        else:
            clean = owners['foreign_target_process_count'] == 0 and owners['unknown_target_process_count'] == 0
            gate('process_ownership', 'PASS' if clean else 'FAIL', 'Target conflicts stop; unrelated devices do not grant or revoke this lease')
        locks = mapping(snapshot.get('locks', {}), 'locks_schema')
        gate('locks', 'BLOCKED' if locks.get('verified') is not True else ('FAIL' if locks.get('conflict') is not False else 'PASS'), 'Canonical coordinator/worker lock identity must be known and conflict-free')
        identity = mapping(snapshot.get('identity', {}), 'identity_schema')
        gate('identity', 'PASS' if identity.get('verified') is True and identity.get('manifest_sha256') == self.manifest.get('manifest_sha256') else 'BLOCKED', 'Frozen input/manifest/lease identities require the independent verifier')
        build_bytes = snapshot.get('retained_build_artifact_bytes')
        if type(build_bytes) is not int or build_bytes < 0:
            gate('build_pool', 'BLOCKED', 'Actual retained build/source selection size is unknown')
        else:
            gate('build_pool', 'PASS' if build_bytes <= self.limits['build_artifacts_bytes'] else 'FAIL', 'Seven GiB build cap carves control/log space from the old eight-GiB pool')
        statuses = {g['status'] for g in gates}
        status = 'FAIL' if 'FAIL' in statuses else 'BLOCKED' if 'BLOCKED' in statuses else 'PASS'
        return dict(status=status, gates=gates, native_execution_authorized=False,
                    scope='INJECTED_RESOURCE_EVIDENCE_ONLY_NOT_ADMISSION', phase=phase)


class ResourceBlocked(RuntimeError):
    pass


class MockCgroupFS:
    """Ordinary fresh files only. This class never targets the cgroup mount."""
    def __init__(self, fresh_root):
        root = Path(fresh_root)
        if not root.is_absolute() or root.exists() or str(root).startswith('/sys/'):
            raise ResourceBlocked('Fresh absolute ordinary mock directory required')
        parent = root.parent.resolve(strict=True)
        if parent != root.parent or str(parent).startswith('/sys/'):
            raise ResourceBlocked('No symlink/system cgroup mock roots')
        # A path alias under /tmp must not turn a mock into a cgroup write.
        # Read-only mountinfo identifies the containing filesystem without
        # ctypes, device libraries or a privileged operation.
        mounts = []
        for line in Path('/proc/self/mountinfo').read_text().splitlines():
            left, right = line.split(' - ', 1)
            point = left.split()[4].replace('\\040', ' ').replace('\\134', '\\')
            mount = Path(point)
            if parent.is_relative_to(mount):
                mounts.append((len(point), right.split()[0]))
        if not mounts or max(mounts)[1] not in ('ext4', 'xfs', 'btrfs', 'tmpfs', 'overlay'):
            raise ResourceBlocked('Ordinary CPU mock filesystem required; cgroup/proc/sys mounts rejected')
        root.mkdir(mode=0o700)
        self.root = root
        self.owner_uid = os.geteuid()
        self.parent = root / 'app.slice'
        self.parent.mkdir(mode=0o700)
        self.parent_stat = self.parent.stat()
        self.writes = []
        self._write(root / 'CPU_MOCK_CGROUP_FS', 'SYNTHETIC_ORDINARY_FILES_ONLY\n')

    def _write(self, path, value):
        if not path.parent.resolve().is_relative_to(self.root.resolve()):
            raise ResourceBlocked('Mock write outside owned root')
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            data = value.encode('ascii')
            if os.write(fd, data) != len(data):
                raise ResourceBlocked('Short mock cgroup write')
            os.fsync(fd)
        finally:
            os.close(fd)
        self.writes.append(path.relative_to(self.root).as_posix())

    def check_parent(self):
        if self.parent.is_symlink():
            raise ResourceBlocked('Mock parent replaced by symlink')
        current = self.parent.stat()
        expected = self.parent_stat
        if (current.st_dev, current.st_ino, current.st_uid) != (expected.st_dev, expected.st_ino, self.owner_uid):
            raise ResourceBlocked('Known parent owner/inode identity changed')


@dataclass(frozen=True)
class DelegatedCgroupPlan:
    """Source-supported future parent binding; actual activation is closed."""
    run_id: str
    child_name: str
    owner_uid: int
    supervisor_pid: int
    known_parent_identity: str
    memory_max_bytes: int = 24 * GiB
    pids_max: int = 128

    def activate_actual(self, *_args, **_kwargs):
        # This test precedes any actual system path lookup, unit creation,
        # cgroup mutation or PID movement. No Boolean argument can enable it.
        raise ResourceBlocked('NOT_RUN: actual user-manager/cgroup activation requires separate admission and audited native deployment')

    def rehearse(self, filesystem, child_identity):
        if type(filesystem) is not MockCgroupFS:
            raise ResourceBlocked('Only concrete ordinary-file CPU mock filesystem allowed')
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', self.child_name) or not self.run_id or not self.known_parent_identity:
            raise ResourceBlocked('Bound run/known parent/safe fresh child name required')
        if type(self.owner_uid) is not int or self.owner_uid != filesystem.owner_uid or type(self.supervisor_pid) is not int or self.supervisor_pid <= 0:
            raise ResourceBlocked('Owned supervisor identity required')
        if type(self.memory_max_bytes) is not int or not (0 < self.memory_max_bytes <= 24 * GiB) or type(self.pids_max) is not int or not (0 < self.pids_max <= 128):
            raise ResourceBlocked('Finite hard memory/PID proposal required')
        pid = child_identity.get('pid')
        if type(pid) is not int or pid <= 0 or type(child_identity.get('owner_uid')) is not int or child_identity.get('owner_uid') != self.owner_uid or type(child_identity.get('parent_pid')) is not int or child_identity.get('parent_pid') != self.supervisor_pid or type(child_identity.get('start_time')) is not int or child_identity['start_time'] <= 0:
            raise ResourceBlocked('Only independently identified owned child PID may be assigned')
        if not isinstance(child_identity.get('boot_id_sha256'), str) or not re.fullmatch(r'[0-9a-f]{64}', child_identity['boot_id_sha256']):
            raise ResourceBlocked('Boot/start identity missing')
        filesystem.check_parent()
        child = filesystem.parent / self.child_name
        child.mkdir(mode=0o700)
        st = child.stat()
        if st.st_uid != self.owner_uid:
            raise ResourceBlocked('Fresh child owner mismatch')
        for name, value in [('memory.max', self.memory_max_bytes), ('pids.max', self.pids_max), ('cgroup.procs', pid)]:
            filesystem.check_parent()
            current = child.stat()
            if child.is_symlink() or (current.st_dev, current.st_ino, current.st_uid) != (st.st_dev, st.st_ino, self.owner_uid):
                raise ResourceBlocked('Fresh child identity changed')
            filesystem._write(child / name, str(value) + '\n')
        return dict(status='CPU_MOCK_REHEARSAL_PASS_NOT_ACTIVATED', writes=list(filesystem.writes),
                    memory_max_bytes=self.memory_max_bytes, pids_max=self.pids_max,
                    actual_units_created=0, actual_cgroups_modified=0,
                    actual_PID_moves=0, native_execution_authorized=False)
