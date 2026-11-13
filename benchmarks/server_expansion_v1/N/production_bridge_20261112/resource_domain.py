"""CPU-only resource-domain preparation. No native or cgroup activation API.

An ordinary-file rehearsal is deliberately distinguishable from an enforced
kernel domain. A resource PASS is never permission to initialize a device.
"""
import copy
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import select
import stat
import time

MiB = 1024 ** 2
GiB = 1024 ** 3
TOTAL_DISK = 553094505923
HEX = re.compile(r'^[0-9a-f]{64}$')


class DomainDenied(RuntimeError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def sha(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def _int(value, minimum=0):
    return type(value) is int and value >= minimum


def _number(value):
    return type(value) in (int, float) and math.isfinite(value)


def _hex(value):
    return isinstance(value, str) and HEX.fullmatch(value) is not None


def resource_manifest():
    """Unapproved subcaps, carved from the original total without enlargement."""
    raw = 76 * (3 * 603979776 + 132 * 607744)
    meta, journal = 380 * MiB, 512 * MiB
    originals = raw + meta + journal
    archive = (102 * originals + 99) // 100 + 16 * MiB
    total = 2 * originals + archive + 8 * GiB + 100 * GiB
    if total != TOTAL_DISK:
        raise DomainDenied('Frozen disk arithmetic changed')
    return dict(schema='hs.resource-domain.envelope.v1', mode='CPU_MOCK_ONLY', approval=None,
                native_execution_authorized=False, requests=76, planned_requests=72,
                rows=85738, planned_rows=69354, failed_requests=4, failed_rows=16384,
                placements=10, backend_inits=10, models=10, contexts=10,
                raw_bytes=raw, metadata_bytes=meta, journal_bytes=journal,
                archive_bytes=archive, restore_bytes=originals,
                build_text_bytes=8 * GiB, protected_disk_bytes=100 * GiB,
                required_disk_bytes=total,
                artifact_subcaps=dict(prior_and_new_build_bytes=7 * GiB,
                                      worker_logs_bytes=256 * MiB,
                                      controller_logs_bytes=128 * MiB,
                                      bridge_logs_bytes=128 * MiB,
                                      resource_domain_records_bytes=16 * MiB,
                                      bridge_receipts_bytes=256 * MiB,
                                      controller_indices_bytes=240 * MiB),
                domain_records_max=4096, domain_record_bytes_max=4096,
                archive_entries_max=4096, bridge_and_domain_entries_max=512,
                journal_records_max=250100, journal_record_bytes_max=2048,
                memory_max_bytes=24 * GiB, protected_RAM_bytes=24 * GiB,
                prelaunch_RAM_bytes=48 * GiB, pids_max=128,
                minimum_free_VRAM_bytes=2 * GiB, max_window_seconds=18000,
                last_launch_offset_seconds=6600, worker_seconds_max=600,
                heartbeat_max_age_seconds=10, heartbeat_period_seconds=5,
                role_order=['RESIDENT_R', 'REPEAT_RESIDENT_R', 'COLD_CANONICAL_ORACLE',
                            'STRONG_WHOLE_RECHUNK_LOOP4'],
                failure_allowance_runnable=False, automatic_retries=False)


@dataclass(frozen=True, init=False)
class DomainBinding:
    """Immutable canonical bytes bind all policy identities and deadlines."""
    encoded: bytes

    def __init__(self, *_args, **_kwargs):
        raise DomainDenied('Use validated DomainBinding.from_dict')

    @classmethod
    def from_dict(cls, value):
        if not isinstance(value, dict):
            raise DomainDenied('Domain binding must be a mapping')
        v = copy.deepcopy(value)
        required = {'run_id', 'manifest_sha256', 'owner_uid', 'device_uuid_sha256',
                    'stage', 'worker_id', 'executable_sha256', 'launcher_executable_sha256', 'lease_sha256',
                    'lease_issuer_sha256', 'supervisor', 'parent', 'window'}
        if set(v) != required:
            raise DomainDenied('Binding keys incomplete or unknown')
        if not isinstance(v['run_id'], str) or not v['run_id'] or len(v['run_id']) > 128:
            raise DomainDenied('Bound run identity missing')
        if not _int(v['owner_uid']) or not isinstance(v['worker_id'], str) or not v['worker_id']:
            raise DomainDenied('Bound owner/worker missing')
        if v['stage'] not in resource_manifest()['role_order'] + ['PREFLIGHT']:
            raise DomainDenied('Unknown stage')
        for key in ('manifest_sha256', 'device_uuid_sha256', 'executable_sha256', 'launcher_executable_sha256',
                    'lease_sha256', 'lease_issuer_sha256'):
            if not _hex(v[key]):
                raise DomainDenied('Unresolved binding identity: ' + key)
        supervisor = v['supervisor']
        if not isinstance(supervisor, dict) or set(supervisor) != {'pid', 'start_time', 'boot_id_sha256', 'uid'}:
            raise DomainDenied('Supervisor identity schema')
        if not _int(supervisor['pid'], 1) or not _int(supervisor['start_time'], 1) or not _hex(supervisor['boot_id_sha256']) or supervisor['uid'] != v['owner_uid']:
            raise DomainDenied('Supervisor owner/start/boot identity')
        parent = v['parent']
        if not isinstance(parent, dict) or set(parent) != {'path_sha256', 'device', 'inode', 'uid', 'mount_id', 'controllers'}:
            raise DomainDenied('Delegated parent identity schema')
        if not _hex(parent['path_sha256']) or not all(_int(parent[k], 1) for k in ('device', 'inode', 'mount_id')) or parent['uid'] != v['owner_uid'] or parent['controllers'] != ['memory', 'pids']:
            raise DomainDenied('Delegated parent identity/controls')
        w = v['window']
        keys = {'start_wall', 'start_mono', 'deadline_wall', 'deadline_mono',
                'last_launch_wall', 'last_launch_mono'}
        if not isinstance(w, dict) or set(w) != keys or not all(_number(w[k]) for k in keys):
            raise DomainDenied('Finite dual-clock window required')
        for suffix in ('wall', 'mono'):
            start, end, last = (w['start_' + suffix], w['deadline_' + suffix], w['last_launch_' + suffix])
            if not 0 < end - start <= 18000 or not start <= last <= min(end, start + 6600):
                raise DomainDenied('Window exceeds fixed proposal')
        result = object.__new__(cls)
        object.__setattr__(result, 'encoded', canonical(v))
        return result

    @property
    def sha256(self):
        return hashlib.sha256(self.encoded).hexdigest()

    def as_dict(self):
        return json.loads(self.encoded)


def validate_parent(binding, evidence):
    """No filesystem mutation; exact independently observed parent identity."""
    b = binding.as_dict()
    if not isinstance(evidence, dict):
        raise DomainDenied('Unknown delegated-parent evidence')
    expected = b['parent']
    for key, value in expected.items():
        if evidence.get(key) != value:
            raise DomainDenied('Delegated parent identity changed: ' + key)
    if evidence.get('type') != 'domain' or evidence.get('delegated') is not True or evidence.get('writable_memory') is not True or evidence.get('writable_pids') is not True or evidence.get('no_foreign_processes') is not True:
        raise DomainDenied('Parent is not verified delegated/owned memory+pids domain')
    return True


def normalize_peer(peer):
    """Accept the bridge's four-field identity without weakening comparisons."""
    if not isinstance(peer, dict):
        raise DomainDenied('Peer must be an identity mapping')
    value = copy.deepcopy(peer)
    if 'start_ticks' in value:
        if 'start_time' in value and value['start_time'] != value['start_ticks']:
            raise DomainDenied('Contradictory process start identities')
        value['start_time'] = value['start_ticks']
    if 'boot_id' in value:
        if not isinstance(value['boot_id'], str) or not value['boot_id'] or len(value['boot_id']) > 128:
            raise DomainDenied('Invalid process boot identity')
        digest = hashlib.sha256(value['boot_id'].encode()).hexdigest()
        if 'boot_id_sha256' in value and value['boot_id_sha256'] != digest:
            raise DomainDenied('Contradictory process boot identities')
        value['boot_id_sha256'] = digest
    return value


def _identity(peer):
    peer = normalize_peer(peer)
    if not _int(peer.get('pid'), 1) or not _int(peer.get('start_time'), 1) or not _int(peer.get('uid')) or not _hex(peer.get('boot_id_sha256')):
        raise DomainDenied('Unknown/reused peer process identity')
    return (peer['pid'], peer['start_time'], peer['uid'], peer['boot_id_sha256'])


def read_process_peer(pid):
    """Read only an existing process and its executable; never launch it."""
    if not _int(pid, 1):
        raise DomainDenied('Invalid process PID')
    proc = Path('/proc') / str(pid)
    def stat_fields():
        fields = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
        return int(fields[1]), int(fields[19])
    ppid, start = stat_fields()
    uid_line = next(line for line in (proc / 'status').read_text().splitlines() if line.startswith('Uid:'))
    uids = [int(v) for v in uid_line.split()[1:]]
    if not uids or len(set(uids)) != 1:
        raise DomainDenied('Setuid/mixed-UID peer not supported')
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    digest = hashlib.sha256()
    size = 0
    with (proc / 'exe').open('rb') as executable:
        while True:
            chunk = executable.read(MiB)
            if not chunk:
                break
            size += len(chunk)
            if size > GiB:
                raise DomainDenied('Executable identity read exceeds bounded artifact limit')
            digest.update(chunk)
    if stat_fields() != (ppid, start):
        raise DomainDenied('Peer identity changed during read-only inspection')
    parent_fields = (Path('/proc') / str(ppid) / 'stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=pid, start_time=start, uid=uids[0], boot_id_sha256=hashlib.sha256(boot.encode()).hexdigest(),
                parent_pid=ppid, parent_start_time=int(parent_fields[19]), exe_sha256=digest.hexdigest())


def limit_operations():
    """Shared pure limit specification for mock and source-only kernel body."""
    return [('memory.max', str(24 * GiB).encode()), ('pids.max', b'128')]


class KernelCgroupAdapter:
    """Reviewable future kernel operation body; its first gate always denies.

    No JSON value or injected callback can bypass that first statement. This
    class is not accepted by ResourceDomain in the current CPU-only build.
    """
    def __init__(self, binding, delegated_parent_path):
        if type(binding) is not DomainBinding:
            raise DomainDenied('Validated immutable binding required')
        self.binding = binding
        self.parent_path = str(delegated_parent_path)

    def operation_plan(self):
        return dict(status='SOURCE_PREPARED_ACTIVATION_NOT_RUN',
                    domain_sha256=self.binding.sha256,
                    order=['HOLD_PARENT_FD_NO_SYMLINK', 'CHECK_CGROUP2_MOUNT_INODE_UID',
                           'REQUIRE_ALREADY_ENABLED_MEMORY_PIDS', 'MKDIR_FRESH_OWNED_CHILD',
                           'WRITE_READBACK_MEMORY_PIDS', 'ATOMIC_CLONE_INTO_HELD_CGROUP_FD',
                           'VERIFY_OWNED_PIDFDS_AND_EXACT_MEMBER_IDENTITIES'],
                    limits={key: value.decode() for key, value in limit_operations()},
                    numeric_PID_attach=False, actual_activation='PERMANENTLY_DENIED')

    def activate_actual(self, atomic_owned_launcher=None):
        raise DomainDenied('CPU-only successor: kernel-domain activation is permanently disabled')

        # SOURCE-ONLY BODY. Removing the gate is a new admission/code review,
        # not a runtime option. No tests execute any statement below the gate.
        # An audited clone3(CLONE_INTO_CGROUP) launcher is required; writing a
        # numeric PID to cgroup.procs is intentionally not a fallback.
        b = self.binding.as_dict()
        path = Path(self.parent_path)
        if not path.is_absolute() or hashlib.sha256(str(path).encode()).hexdigest() != b['parent']['path_sha256']:
            raise DomainDenied('Frozen delegated parent path differs')
        pfd = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        childfd = None
        try:
            for part in path.parts[1:]:
                nxt = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=pfd)
                os.close(pfd)
                pfd = nxt
            st = os.fstat(pfd)
            if (st.st_dev, st.st_ino, st.st_uid) != (b['parent']['device'], b['parent']['inode'], b['owner_uid']):
                raise DomainDenied('Held delegated parent identity differs')
            fdinfo = Path('/proc/self/fdinfo', str(pfd)).read_text().splitlines()
            mnt_id = int(next(line.split()[1] for line in fdinfo if line.startswith('mnt_id:')))
            if mnt_id != b['parent']['mount_id']:
                raise DomainDenied('Held delegated parent mount differs')
            entry = next(line for line in Path('/proc/self/mountinfo').read_text().splitlines()
                         if int(line.split()[0]) == mnt_id)
            lhs, rhs = entry.split(' - ', 1)
            fields = lhs.split()
            major, minor = (int(v) for v in fields[2].split(':'))
            if rhs.split()[0] != 'cgroup2' or os.makedev(major, minor) != st.st_dev:
                raise DomainDenied('Held parent is not the expected cgroup2 filesystem')

            def read_control(directory, name):
                fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory)
                try:
                    raw = os.read(fd, 4097)
                    if len(raw) > 4096:
                        raise DomainDenied('Control file exceeds bound')
                    return raw.decode('ascii').strip()
                finally:
                    os.close(fd)

            if read_control(pfd, 'cgroup.type') != 'domain' or read_control(pfd, 'cgroup.procs'):
                raise DomainDenied('Delegated parent type/direct membership is unsuitable')
            for name in ('cgroup.controllers', 'cgroup.subtree_control'):
                if not {'memory', 'pids'} <= set(read_control(pfd, name).split()):
                    raise DomainDenied('Controllers must already be delegated and enabled; no policy modification')
            child_name = 'hs-' + self.binding.sha256[:24]
            os.mkdir(child_name, mode=0o700, dir_fd=pfd)  # Existing name fails; never delete/reuse.
            childfd = os.open(child_name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=pfd)
            child_st = os.fstat(childfd)
            if child_st.st_uid != b['owner_uid'] or child_st.st_dev != st.st_dev:
                raise DomainDenied('Fresh domain owner/filesystem differs')
            for leaf, data in limit_operations():
                fd = os.open(leaf, os.O_WRONLY | os.O_NOFOLLOW, dir_fd=childfd)
                try:
                    if os.write(fd, data) != len(data):
                        raise DomainDenied('Short kernel limit write; preserve incomplete domain')
                finally:
                    os.close(fd)
                if read_control(childfd, leaf) != data.decode():
                    raise DomainDenied('Kernel limit readback differs')
            if not callable(atomic_owned_launcher):
                raise DomainDenied('No separately reviewed atomic owned launcher')
            # Future trusted launcher receives the held FD and immutable SHA;
            # it must use CLONE_INTO_CGROUP, never a numeric-PID attach race.
            spawned = atomic_owned_launcher(childfd, self.binding.sha256)
            if not isinstance(spawned, dict) or spawned.get('mechanism') != 'SOURCE_BOUND_CLONE3_INTO_CGROUP' or spawned.get('domain_sha256') != self.binding.sha256:
                raise DomainDenied('Atomic domain launch proof missing')
            peers = []
            for role in ('supervisor', 'worker'):
                peer, pidfd = spawned[role], spawned[role + '_pidfd']
                if not _int(pidfd) or select.select([pidfd], [], [], 0)[0]:
                    raise DomainDenied('Owned pidfd invalid or process already exited')
                info = Path('/proc/self/fdinfo', str(pidfd)).read_text().splitlines()
                if int(next(line.split()[1] for line in info if line.startswith('Pid:'))) != peer['pid']:
                    raise DomainDenied('pidfd does not identify the expected owned process')
                current = read_process_peer(peer['pid'])
                if _identity(current) != _identity(peer) or current['uid'] != b['owner_uid']:
                    raise DomainDenied('Owned process start/boot/UID differs')
                peers.append(current)
            if peers[1]['parent_pid'] != peers[0]['pid'] or peers[1]['parent_start_time'] != peers[0]['start_time']:
                raise DomainDenied('Worker not created by the held owned supervisor')
            # Exact process membership is read back from the held domain, and
            # must remain a subset of independently tracked owned descendants.
            members = {int(v) for v in read_control(childfd, 'cgroup.procs').split()}
            if members != {peer['pid'] for peer in peers}:
                raise DomainDenied('Unknown/missing initial domain process')
            return dict(domain_fd=childfd, parent_fd=pfd, domain_sha256=self.binding.sha256,
                        owned_peers=peers, admission='FUTURE_REVIEW_REQUIRED')
        except BaseException:
            # No deletion, PID signaling or reuse of an incomplete domain.
            if childfd is not None:
                os.close(childfd)
            os.close(pfd)
            raise


class OrdinaryCgroupAdapter:
    """Rehearse the exact operation list on fresh ordinary files only.

    No adapter for a real cgroup is supplied. '/sys', procfs, cgroupfs and any
    symlink component are rejected before creating files.
    """
    def __init__(self, fresh_root, fail_after=None):
        root = Path(fresh_root)
        if not root.is_absolute() or root.exists() or str(root).startswith(('/sys/', '/proc/')):
            raise DomainDenied('Fresh ordinary mock directory required')
        parent = root.parent.resolve(strict=True)
        if parent != root.parent:
            raise DomainDenied('Symlink mock parent forbidden')
        mounts = []
        for line in Path('/proc/self/mountinfo').read_text().splitlines():
            lhs, rhs = line.split(' - ', 1)
            point = lhs.split()[4].replace('\\040', ' ').replace('\\134', '\\')
            if parent.is_relative_to(Path(point)):
                mounts.append((len(point), rhs.split()[0]))
        if not mounts or max(mounts)[1] not in ('ext4', 'xfs', 'btrfs', 'tmpfs', 'overlay'):
            raise DomainDenied('Mock cgroup requires an ordinary filesystem')
        root.mkdir(mode=0o700)
        self.root = root
        self.root_identity = (root.stat().st_dev, root.stat().st_ino, root.stat().st_uid)
        self.fail_after = fail_after
        self.writes = []
        self.members = {}
        self.domain_sha256 = None
        self.poisoned = False

    def _check(self):
        if self.poisoned or self.root.is_symlink():
            raise DomainDenied('Mock adapter poisoned or replaced')
        st = self.root.stat()
        if (st.st_dev, st.st_ino, st.st_uid) != self.root_identity:
            raise DomainDenied('Mock root identity changed')

    def _write(self, leaf, data):
        self._check()
        if '/' in leaf or leaf not in ('BINDING.json', 'memory.max', 'pids.max') and not leaf.startswith('cgroup.procs.'):
            raise DomainDenied('Unknown mock operation')
        if len(data) > 4096:
            raise DomainDenied('Mock operation payload too large')
        if self.fail_after is not None and len(self.writes) >= self.fail_after:
            self.poisoned = True
            raise DomainDenied('Injected mock write failure; partial files retained')
        fd = None
        try:
            fd = os.open(self.root / leaf, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            if os.write(fd, data) != len(data):
                self.poisoned = True
                raise DomainDenied('Short mock write; partial file retained')
            os.fsync(fd)
        except BaseException:
            self.poisoned = True
            raise
        finally:
            if fd is not None:
                os.close(fd)
        self.writes.append(leaf)

    def _read(self, leaf):
        self._check()
        fd = os.open(self.root / leaf, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            st = os.fstat(fd)
            if not stat.S_ISREG(st.st_mode) or st.st_uid != self.root_identity[2] or st.st_nlink != 1 or st.st_size > 4096:
                raise DomainDenied('Mock control file owner/type/size changed')
            return os.read(fd, 4097)
        finally:
            os.close(fd)

    def activate(self, binding):
        self._check()
        if self.domain_sha256 is not None or self.writes:
            raise DomainDenied('Existing domain cannot be reactivated')
        try:
            self._write('BINDING.json', binding.encoded)
            for leaf, data in limit_operations():
                self._write(leaf, data)
            self.domain_sha256 = binding.sha256
        except BaseException:
            self.poisoned = True
            raise

    def attach(self, binding, peer):
        self._check()
        if self.domain_sha256 != binding.sha256 or len(self.members) >= 128 or peer['pid'] in self.members:
            raise DomainDenied('Mock domain identity/pids/reentry failure')
        self._write('cgroup.procs.' + str(peer['pid']), str(peer['pid']).encode())
        self.members[peer['pid']] = _identity(peer)

    def verify(self, binding, peer=None):
        self._check()
        if self.domain_sha256 != binding.sha256 or self._read('BINDING.json') != binding.encoded or self._read('memory.max') != str(24 * GiB).encode() or self._read('pids.max') != b'128':
            raise DomainDenied('Mock domain binding or limit changed')
        if peer is not None and self.members.get(peer['pid']) != _identity(peer):
            raise DomainDenied('Mock child membership/reused PID differs')
        return True


class ResourceDomain:
    """Fail-closed policy attached to one immutable worker/stage binding.

    observer() may provide read-only snapshots; clock() supplies dual clocks.
    Tests can instead pass snapshots and now explicitly. Adapter=None cannot
    activate a domain and therefore can never admit a child.
    """
    def __init__(self, binding, adapter=None, observer=None, clock=None, process_reader=None):
        if type(binding) is not DomainBinding:
            raise DomainDenied('Canonical DomainBinding required')
        if adapter is not None and type(adapter) is not OrdinaryCgroupAdapter:
            raise DomainDenied('Only explicit ordinary-file rehearsal adapter exists')
        self.binding = binding
        self.adapter, self.observer = adapter, observer
        self.clock = clock or (lambda: dict(wall=time.time(), mono=time.monotonic()))
        self.process_reader = process_reader or read_process_peer
        self.closed = False
        self.poisoned = False
        self.peer = None
        self.parent_peer = None
        self.last_snapshot = None
        self.owned_exit_observed = False
        self.image_phase = 'UNBOUND'

    @property
    def sha256(self):
        return self.binding.sha256

    def activate_actual(self, *_args, **_kwargs):
        raise DomainDenied('CPU-only successor: actual cgroup activation is permanently disabled')

    def _evidence(self, snapshot, now):
        if self.closed or self.poisoned:
            raise DomainDenied('Closed/poisoned resource domain')
        if snapshot is None:
            if not callable(self.observer):
                raise DomainDenied('No independent resource/lease/process observer')
            snapshot = self.observer()
        if not isinstance(snapshot, dict):
            raise DomainDenied('Unknown resource evidence')
        now = self.clock() if now is None else now
        if not isinstance(now, dict) or not all(_number(now.get(k)) for k in ('wall', 'mono')):
            raise DomainDenied('Finite dual clock required')
        return snapshot, now

    def _check(self, snapshot, now, launch):
        b, r = self.binding.as_dict(), resource_manifest()
        validate_parent(self.binding, snapshot.get('parent'))
        if snapshot.get('domain_sha256') != self.sha256 or snapshot.get('manifest_sha256') != b['manifest_sha256']:
            raise DomainDenied('Resource/manifest domain SHA conflict')
        for axis in ('wall', 'mono'):
            observed = snapshot.get('observed_' + axis)
            if not _number(observed) or not 0 <= now[axis] - observed <= 10:
                raise DomainDenied('Stale/future resource observation')
            w = b['window']
            if not w['start_' + axis] <= now[axis] < w['deadline_' + axis] or launch and now[axis] > w['last_launch_' + axis]:
                raise DomainDenied('Hard deadline or last-launch limit')
        lease = snapshot.get('lease')
        if not isinstance(lease, dict) or lease.get('verified') is not True or lease.get('sha256') != b['lease_sha256'] or lease.get('issuer_sha256') != b['lease_issuer_sha256'] or lease.get('run_id') != b['run_id'] or lease.get('device_uuid_sha256') != b['device_uuid_sha256'] or lease.get('owner_uid') != b['owner_uid']:
            raise DomainDenied('Unknown/mismatched external authority or GPU lease')
        for axis in ('wall', 'mono'):
            heartbeat, expiry = lease.get('heartbeat_' + axis), lease.get('expires_' + axis)
            if not _number(heartbeat) or not 0 <= now[axis] - heartbeat <= 10 or not _number(expiry) or expiry < b['window']['deadline_' + axis] or now[axis] >= expiry:
                raise DomainDenied('Lost parent heartbeat or insufficient lease window')
        if _identity(snapshot.get('supervisor')) != _identity(b['supervisor']) or snapshot.get('supervisor_alive') is not True:
            raise DomainDenied('Parent lease owner exited or PID identity changed')
        locks = snapshot.get('locks')
        if not isinstance(locks, dict) or locks.get('verified') is not True or locks.get('conflict') is not False or locks.get('domain_sha256') != self.sha256:
            raise DomainDenied('Unknown/conflicting resource locks')
        for key, floor in (('disk_available_bytes', TOTAL_DISK),
                           ('RAM_available_bytes', 48 * GiB if launch else 24 * GiB),
                           ('GPU_free_bytes', 2 * GiB)):
            if not _int(snapshot.get(key)) or snapshot[key] < floor:
                raise DomainDenied('Resource floor failed: ' + key)
        for key, ceiling in (('domain_memory_current_bytes', 24 * GiB), ('domain_pids_current', 128)):
            if not _int(snapshot.get(key)) or snapshot[key] > ceiling:
                raise DomainDenied('Resource hard limit failed: ' + key)
        if snapshot.get('device_uuid_sha256') != b['device_uuid_sha256'] or snapshot.get('foreign_target_processes') != 0 or snapshot.get('unknown_target_processes') != 0:
            raise DomainDenied('GPU identity/conflicting or unknown target task')
        if launch and (not _int(snapshot.get('retained_build_bytes')) or snapshot['retained_build_bytes'] > 7 * GiB):
            raise DomainDenied('Selected artifact set is unmeasured or exceeds old pool')
        return dict(status='CPU_MOCK_POLICY_PASS_NOT_ADMISSION', domain_sha256=self.sha256,
                    native_execution_authorized=False, actual_cgroup_activated=False,
                    enforcement='ORDINARY_FILES_ONLY' if self.adapter else 'NOT_ACTIVATED')

    def plan(self, parent_evidence=None, lease_evidence=None, now=None, snapshot=None):
        """Pure validation. Explicit parent/lease overwrite only the injected copy."""
        if snapshot is None and callable(self.observer):
            snapshot = self.observer()
        snapshot = copy.deepcopy(snapshot) if isinstance(snapshot, dict) else {}
        if parent_evidence is not None:
            snapshot['parent'] = parent_evidence
        if lease_evidence is not None:
            snapshot['lease'] = lease_evidence
        return self.before_launch(snapshot, now)

    def before_launch(self, snapshot=None, now=None):
        try:
            snapshot, now = self._evidence(snapshot, now)
            result = self._check(snapshot, now, True)
            self.last_snapshot = copy.deepcopy(snapshot)
            return result
        except BaseException:
            self.poisoned = True
            raise

    def bind_child(self, childpeer, parentpeer, snapshot=None, now=None):
        try:
            snapshot, now = self._evidence(snapshot, now)
            self._check(snapshot, now, True)
            b = self.binding.as_dict()
            childpeer, parentpeer = normalize_peer(childpeer), normalize_peer(parentpeer)
            if not all(key in childpeer for key in ('exe_sha256', 'parent_pid', 'parent_start_time')):
                observed = self.process_reader(childpeer['pid'])
                if _identity(observed) != _identity(childpeer):
                    raise DomainDenied('Read-only child identity differs from bridge peer')
                childpeer = observed
            if _identity(parentpeer) != _identity(b['supervisor']) and 'ancestor_identities' not in parentpeer:
                observed = self.process_reader(parentpeer['pid'])
                if _identity(observed) != _identity(parentpeer):
                    raise DomainDenied('Read-only parent identity differs from bridge peer')
                parentpeer = observed
                chain = []
                previous = observed
                for _ in range(64):
                    ancestor = self.process_reader(previous['parent_pid'])
                    chain.append(ancestor)
                    if _identity(ancestor) == _identity(b['supervisor']):
                        break
                    previous = ancestor
                parentpeer['ancestor_identities'] = chain
            child, parent = _identity(childpeer), _identity(parentpeer)
            if self.peer is not None or child[2:] != parent[2:] or child[2] != b['owner_uid'] or childpeer.get('parent_pid') != parentpeer['pid'] or childpeer.get('parent_start_time') != parentpeer['start_time'] or childpeer.get('exe_sha256') != b['launcher_executable_sha256']:
                raise DomainDenied('Child ownership/ancestry/executable/reentry conflict')
            supervisor = _identity(b['supervisor'])
            chain = parentpeer.get('ancestor_identities', [])
            if parent != supervisor:
                if not isinstance(chain, list) or not chain or len(chain) > 64 or _identity(chain[-1]) != supervisor:
                    raise DomainDenied('Child ancestry does not reach bound supervisor')
                previous = parentpeer
                seen = {child[0], parent[0]}
                for ancestor in chain:
                    ident = _identity(ancestor)
                    if ident[0] in seen or ident[2:] != supervisor[2:] or previous.get('parent_pid') != ident[0] or previous.get('parent_start_time') != ident[1]:
                        raise DomainDenied('Broken/cyclic/foreign process ancestry')
                    seen.add(ident[0])
                    previous = ancestor
            if snapshot.get('membership_verified') is not True or snapshot.get('only_owned_descendants') is not True:
                raise DomainDenied('Unknown actual/rehearsed membership/descendants')
            if self.adapter is None:
                raise DomainDenied('Actual domain activation not authorized/implemented')
            self.adapter.activate(self.binding)
            self.adapter.attach(self.binding, childpeer)
            self.adapter.verify(self.binding, childpeer)
            self.peer, self.parent_peer = copy.deepcopy(childpeer), copy.deepcopy(parentpeer)
            self.image_phase = 'PREEXEC'
            self.last_snapshot = copy.deepcopy(snapshot)
            return dict(status='CPU_MOCK_CHILD_BOUND_NOT_ACTIVATED', domain_sha256=self.sha256,
                        actual_cgroup_activated=False, native_execution_authorized=False)
        except BaseException:
            self.poisoned = True
            raise

    def assert_live(self, snapshot=None, now=None):
        try:
            snapshot, now = self._evidence(snapshot, now)
            result = self._check(snapshot, now, False)
            if self.peer is None or self.adapter is None:
                raise DomainDenied('No bound/enforced child domain')
            if snapshot.get('membership_verified') is not True or snapshot.get('only_owned_descendants') is not True:
                raise DomainDenied('Child exited/escaped/reused or membership unknown')
            expected_image = self.binding.as_dict()['launcher_executable_sha256' if self.image_phase == 'PREEXEC' else 'executable_sha256']
            if not self.owned_exit_observed and (_identity(snapshot.get('child')) != _identity(self.peer) or snapshot['child'].get('exe_sha256') != expected_image):
                raise DomainDenied('Child exited/escaped/reused or executable changed')
            self.adapter.verify(self.binding, self.peer)
            self.last_snapshot = copy.deepcopy(snapshot)
            return result
        except BaseException:
            self.poisoned = True
            raise

    def observe_postexec(self, childpeer, snapshot=None, now=None):
        """Worker HELLO transition: same held identity, now the worker image."""
        try:
            snapshot, now = self._evidence(snapshot, now)
            self._check(snapshot, now, False)
            peer = normalize_peer(childpeer)
            if self.peer is None or self.image_phase != 'PREEXEC' or self.owned_exit_observed or _identity(peer) != _identity(self.peer):
                raise DomainDenied('Invalid/replayed postexec identity transition')
            if 'exe_sha256' not in peer:
                observed = self.process_reader(peer['pid'])
                if _identity(observed) != _identity(peer):
                    raise DomainDenied('Postexec observed identity changed')
                peer = observed
            if peer.get('exe_sha256') != self.binding.as_dict()['executable_sha256'] or snapshot.get('membership_verified') is not True or snapshot.get('only_owned_descendants') is not True:
                raise DomainDenied('Postexec worker image/membership mismatch')
            self.adapter.verify(self.binding, self.peer)
            self.image_phase = 'POSTEXEC'
            return dict(status='CPU_MOCK_POSTEXEC_IDENTITY_NOT_NATIVE_ADMISSION', domain_sha256=self.sha256,
                        native_execution_authorized=False, image_phase=self.image_phase)
        except BaseException:
            self.poisoned = True
            raise

    def observe_owned_exit(self, childpeer, kernel_exit_observed=False):
        """Caller must independently poll its held pidfd for this exact child.

        This changes only the post-exit resource-check phase. It is not a worker
        result, successful stage, release proof or GPU preemption guarantee.
        """
        try:
            normalized = normalize_peer(childpeer)
            valid = (not self.closed and not self.poisoned and self.peer is not None
                     and _identity(normalized) == _identity(self.peer)
                     and kernel_exit_observed is True)
        except BaseException:
            self.poisoned = True
            raise
        if not valid:
            self.poisoned = True
            raise DomainDenied('No independently observed exit of the bound owned identity')
        self.owned_exit_observed = True
        return dict(status='CALLER_PIDFD_EXIT_OBSERVATION_RECORDED_NOT_SUCCESS',
                    domain_sha256=self.sha256, native_execution_authorized=False,
                    GPU_completion_or_preemption_guaranteed=False)

    def assert_after_exit(self, childpeer, snapshot=None, now=None):
        """Bridge-only call after its held pidfd became readable.

        The bridge must establish pidfd readability itself, not accept a JSON
        exit receipt. This method never seals numerical or deployment success.
        """
        self.observe_owned_exit(childpeer, kernel_exit_observed=True)
        return self.assert_live(snapshot, now)

    def close_result(self, reason, remaining_owned_pids=None):
        if not isinstance(reason, str) or not reason or len(reason) > 1024:
            raise DomainDenied('Bounded explicit close reason required')
        remaining = [] if remaining_owned_pids is None else list(remaining_owned_pids)
        self.closed = True
        return dict(status='BLOCKED_OWNED_PROCESSES_REMAIN' if remaining else 'CPU_MOCK_CLOSED_NOT_NATIVE',
                    reason=reason, poisoned=self.poisoned, domain_sha256=self.sha256,
                    image_phase=self.image_phase,
                    remaining_owned_pids=remaining, actual_signals_sent=0,
                    native_execution_authorized=False, observed_no_remaining_processes=not remaining,
                    resource_release_verified=False,
                    GPU_completion_or_preemption_guaranteed=False)
