"""Ordinary-file domain for the fixed std-only CPU bridge demonstration.

Real /proc, memory and disk reads are identified separately from synthetic GPU
lease/limits. This is not an external GPU allocation or kernel memory domain.
"""
import hashlib
import os
from pathlib import Path
import time
from resource_domain import (DomainBinding, DomainDenied, ResourceDomain,
                             OrdinaryCgroupAdapter, read_process_peer, GiB)


def _hash_bytes(value):
    return hashlib.sha256(value).hexdigest()


def _cgroup(pid):
    return (Path('/proc') / str(pid) / 'cgroup').read_bytes()


def _rss(pid):
    for line in (Path('/proc') / str(pid) / 'status').read_text().splitlines():
        if line.startswith('VmRSS:'):
            return int(line.split()[1]) * 1024
    return 0


def _mount_id(path):
    matches = []
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        fields = line.split(' - ', 1)[0].split()
        point = fields[4].replace('\\040', ' ').replace('\\134', '\\')
        if path.is_relative_to(Path(point)):
            matches.append((len(point), int(fields[0])))
    if not matches:
        raise DomainDenied('Ordinary mock filesystem mount identity unavailable')
    return max(matches)[1]


def cpu_domain_factory(root, controller, worker, lease, device):
    """Signature expected by cpu_run.run_case; source-frozen CPU pair only."""
    root = Path(root)
    adapter = OrdinaryCgroupAdapter(root / 'ORDINARY_RESOURCE_DOMAIN')
    own = read_process_peer(os.getpid())
    supervisor = {k: own[k] for k in ('pid', 'start_time', 'uid', 'boot_id_sha256')}
    own_cgroup = _cgroup(os.getpid())
    st = adapter.root.stat()
    # This identity belongs to ordinary mock files, not /sys/fs/cgroup.
    parent = dict(path_sha256=_hash_bytes(str(adapter.root).encode()),
                  device=st.st_dev, inode=st.st_ino, uid=st.st_uid,
                  mount_id=_mount_id(adapter.root), controllers=['memory', 'pids'])
    m = controller.manifest
    start_wall, start_mono = time.time(), time.monotonic()
    remaining = min(60., m['window']['deadline_wall'] - start_wall,
                    m['window']['deadline_mono'] - start_mono)
    if remaining <= 0:
        raise DomainDenied('CPU fixture window already closed')
    binding = DomainBinding.from_dict(dict(
        run_id=m['run_id'], manifest_sha256=m['manifest_sha256'], owner_uid=os.geteuid(),
        device_uuid_sha256=device, stage=worker['stage'], worker_id=worker['id'],
        executable_sha256=worker['executable_sha256'],
        launcher_executable_sha256=m['identity_bindings']['launcher'],
        lease_sha256=lease, lease_issuer_sha256=_hash_bytes(b'CPU_SYNTHETIC_ISSUER_NO_GPU_AUTHORITY'),
        supervisor=supervisor, parent=parent,
        window=dict(start_wall=start_wall, start_mono=start_mono,
                    deadline_wall=start_wall + remaining, deadline_mono=start_mono + remaining,
                    last_launch_wall=start_wall + min(15., remaining),
                    last_launch_mono=start_mono + min(15., remaining))))
    box = {}

    def observe():
        now = dict(wall=time.time(), mono=time.monotonic())
        current = read_process_peer(os.getpid())
        d = box['domain']
        child = None
        pids = [os.getpid()]
        memberships = [_cgroup(os.getpid()) == own_cgroup]
        if d.peer is not None and not d.owned_exit_observed:
            child = read_process_peer(d.peer['pid'])
            pids.append(child['pid'])
            memberships.append(_cgroup(child['pid']) == own_cgroup)
        if d.parent_peer is not None:
            try:
                parent_now = read_process_peer(d.parent_peer['pid'])
                pids.append(parent_now['pid'])
                memberships.append(_cgroup(parent_now['pid']) == own_cgroup)
            except FileNotFoundError:
                # The root bridge separately verifies/reaps this exact launcher.
                pass
        available = next(int(line.split()[1]) * 1024 for line in Path('/proc/meminfo').read_text().splitlines()
                         if line.startswith('MemAvailable:'))
        vfs = os.statvfs(root)
        memory = sum(_rss(pid) for pid in set(pids) if (Path('/proc') / str(pid)).exists())
        b = binding.as_dict()
        return dict(
            evidence_class='CPU_MOCK_GPU_LEASE_AND_ORDINARY_MEMORY_DOMAIN',
            real_reads=['proc_identity', 'proc_ancestry', 'proc_cgroup_membership', 'proc_RSS', 'RAM_available', 'disk_available'],
            synthetic=['external_GPU_lease', 'GPU_free_bytes', 'delegation_flags', 'cgroup_limit_activation',
                       'retained_build_bytes_fixture_subset_not_deployment_selection'],
            parent={**parent, 'type': 'domain', 'delegated': True, 'writable_memory': True,
                    'writable_pids': True, 'no_foreign_processes': True},
            lease=dict(verified=True, sha256=lease, issuer_sha256=b['lease_issuer_sha256'],
                       run_id=m['run_id'], device_uuid_sha256=device, owner_uid=os.geteuid(),
                       heartbeat_wall=now['wall'], heartbeat_mono=now['mono'],
                       expires_wall=b['window']['deadline_wall'], expires_mono=b['window']['deadline_mono'],
                       authority_kind='SYNTHETIC_CPU_ONLY_NO_GPU_AUTHORITY'),
            domain_sha256=binding.sha256, manifest_sha256=m['manifest_sha256'],
            observed_wall=now['wall'], observed_mono=now['mono'],
            supervisor=current, supervisor_alive=True,
            locks=dict(verified=True, conflict=False, domain_sha256=binding.sha256,
                       evidence_kind='SYNTHETIC_CPU_ONLY_CANONICAL_CONTROLLER_OWNS_FRESH_ROOT'),
            disk_available_bytes=vfs.f_bavail * vfs.f_frsize,
            RAM_available_bytes=available, GPU_free_bytes=2 * GiB,
            domain_memory_current_bytes=memory, domain_pids_current=len(set(pids)),
            device_uuid_sha256=device, foreign_target_processes=0, unknown_target_processes=0,
            retained_build_bytes=sum(p.stat().st_size for p in root.iterdir() if p.is_file()),
            retained_build_bytes_scope='SYNTHETIC_CPU_ROOT_FILE_SUBSET_NOT_RETAINED_DEPLOYMENT',
            complete_retained_build_selection='NOT_MEASURED_NO_ADMISSION',
            membership_verified=all(memberships), only_owned_descendants=all(memberships),
            actual_cgroup_inherited_sha256=_hash_bytes(own_cgroup), actual_cgroup_limits_activated=False,
            child=child)

    domain = ResourceDomain(binding, adapter=adapter, observer=observe)
    box['domain'] = domain
    return domain
