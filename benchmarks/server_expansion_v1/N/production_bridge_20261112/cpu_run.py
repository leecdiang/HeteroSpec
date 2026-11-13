"""Bounded CPU-only integration runner, never a native admission command.

Only the source-frozen std-only pair may execute. There is no generic --cpu flag
that permits a native or user-selected GPU ELF. Existing STATE is inspect-only.
"""
import argparse
import copy
import fcntl
import json
import os
from pathlib import Path
import re
import select
import signal
import stat
import subprocess
import threading
import time
from bridge import BridgeController, BridgeBroker, C, file_hash, parent_pid, cgroup_membership
from generate_manifest import instantiate_cpu_manifest, finalize_manifest_cpu

# Pinned after the reviewed source recipe compiled the fixed pair (build02).
# Caller-supplied ELF/SHA or a submitted receipt can never populate these pins.
CPU_LAUNCHER_SHA256 = "770609a9fc019701a8252bbffc63f968b481789f34f4cbee7182b9344ca3290e"
CPU_WORKER_SHA256 = "8ea68312efbdcf00fbf0c5d58354055a741ea91c4ddb3d9406af18538f2f1295"


class ExplicitCpuPolicy:
    def check(self, snapshot, now, phase="DURING_WORK"):
        return {"status": "PASS", "native_execution_authorized": False,
                "scope": "CPU_FIXED_WORKER_NO_HARDWARE_ADMISSION"}


class NeverVerifier:
    def verify(self, stage):
        raise C.Closed("CPU bridge IPC is not a numerical stage qualification")


def check_std_elf(path, expected):
    C.need(file_hash(path, 4 * 1024 * 1024) == expected, "CPU artifact frozen SHA changed")
    result = subprocess.run(["/usr/bin/readelf", "-d", str(path)], capture_output=True, text=True, check=True,
        env={"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C", "CUDA_VISIBLE_DEVICES": ""})
    needed = re.findall(r"Shared library: \[([^]]+)\]", result.stdout)
    allowed = {"libstdc++.so.6", "libgcc_s.so.1", "libc.so.6", "libm.so.6"}
    C.need(needed and "libstdc++.so.6" in needed and not set(needed) - allowed,
           "model/backend/CUDA or non-standard dependency refused without execution")
    return needed


def sealed_cpu_image(path, expected):
    """Execute the hashed immutable bytes, never a subsequently replaced path."""
    original = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        st = os.fstat(original)
        C.need(stat.S_ISREG(st.st_mode) and 0 < st.st_size <= 4 * 1024 * 1024,
               "small regular fixed CPU image required")
        raw = os.read(original, 4 * 1024 * 1024 + 1)
        C.need(len(raw) == st.st_size and C.sha(raw) == expected, "CPU image changed before sealing")
    finally:
        os.close(original)
    fd = os.memfd_create("hs-reviewed-cpu-launcher", os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING)
    try:
        C.need(os.write(fd, raw) == len(raw), "short CPU image copy")
        fcntl.fcntl(fd, fcntl.F_ADD_SEALS,
            fcntl.F_SEAL_WRITE | fcntl.F_SEAL_GROW | fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_SEAL)
        return fd
    except BaseException:
        os.close(fd)
        raise


def cpu_job(root, manifest, worker, launcher, image, log_fds, domain_sha, device_sha, behavior):
    return {"schema": "hs.production-bridge.cpu-job.v1", "mode": "CPU_FIXED_WORKER",
        "run_id": manifest["run_id"], "manifest_sha256": manifest["manifest_sha256"],
        "worker_id": worker["id"], "stage": worker["stage"], "lease_sha256": C.sha(b"cpu-lease:" + str(root).encode()),
        "domain_sha256": domain_sha, "device_sha256": device_sha,
        "controller_owner": C.process_identity(), "accounting_socket": str(root / "control.sock"),
        "capture_root": str(root / "capture"), "deployment_id": worker["deployment_id"],
        "request_ids": worker["request_ids"], "worker_executable": str(image),
        "worker_executable_sha256": file_hash(image),
        "deadline_wall": min(manifest["window"]["deadline_wall"], time.time() + 15),
        "deadline_mono": min(manifest["window"]["deadline_mono"], time.monotonic() + 15),
        "stdout_path": str(root / "WORKER.stdout.log"), "stderr_path": str(root / "WORKER.stderr.log"),
        "stdout_fd": log_fds["stdout"], "stderr_fd": log_fds["stderr"],
        "per_log_bytes": 4096, "worker_behavior": behavior}


def run_case(root, launcher, worker_image, launcher_sha, worker_sha, *, behavior="normal",
             fault=None, domain_factory=None):
    root = Path(root)
    C.need(root.is_absolute() and not root.exists(), "fresh absolute unique CPU run only")
    C.need(launcher_sha == CPU_LAUNCHER_SHA256 and worker_sha == CPU_WORKER_SHA256,
           "only the source-reviewed, pinned std-only fixture build may execute")
    needed = {"launcher": check_std_elf(launcher, launcher_sha),
              "worker": check_std_elf(worker_image, worker_sha)}
    root.mkdir(mode=0o700)
    (root / "capture").mkdir(mode=0o700)
    m = instantiate_cpu_manifest(root.name, time.time(), time.monotonic(), 60)
    source_paths = [Path(__file__).resolve(), Path(__file__).with_name("bridge.py"),
                    Path(__file__).with_name("resource_domain.py"),
                    Path(__file__).with_name("cpu_resource_fixture.py"),
                    Path(__file__).with_name("resource_manifest.py")]
    source_paths += [Path(__file__).resolve().parent.parent / "admission_controller_20261112" / name
                    for name in ("controller.py", "generate_manifest.py", "resource_limits.py", "late_bind.py")]
    source_hashes = {p.parent.name + "/" + p.name: file_hash(p) for p in source_paths}
    m["identity_bindings"] = {"scope": "CPU_FIXED_ELF_ONLY", "sources": source_hashes,
                               "launcher": launcher_sha, "worker": worker_sha}
    for w in m["workers"]:
        w["executable_sha256"] = worker_sha
    m = finalize_manifest_cpu(m)
    def current_identities():
        return {"scope": "CPU_FIXED_ELF_ONLY", "sources": {p.parent.name + "/" + p.name: file_hash(p) for p in source_paths},
                "launcher": file_hash(launcher), "worker": file_hash(worker_image)}
    controller = BridgeController(root / "run", m, NeverVerifier(), ExplicitCpuPolicy(), lambda: {}, current_identities)
    for dep in m["deployments"]:
        if dep["kind"] == "PREFLIGHT":
            controller.synthetic_preflight(dep["id"])
    broker = BridgeBroker(controller, root / "control.sock", timeout=3)
    logs = {name: os.open(root / ("WORKER." + name + ".log"),
                        os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            for name in ("stdout", "stderr")}
    launch_logs = {name: os.open(root / ("WORKER." + name + ".log"), os.O_WRONLY | os.O_NOFOLLOW)
                   for name in ("stdout", "stderr")}
    worker = m["workers"][0]
    lease = C.sha(b"cpu-lease:" + str(root).encode())
    device = C.sha(b"NO_DEVICE_CPU_ONLY")
    domain = None if domain_factory is None else domain_factory(root, controller, worker, lease, device)
    C.need(domain is not None, "fixed-process CPU runner requires the actual ordinary-file domain factory")
    job = cpu_job(root, m, worker, launcher, worker_image, launch_logs,
                  C.sha(b"CPU_NO_ACTUAL_RESOURCE_ENFORCEMENT") if domain is None else domain.sha256,
                  device, behavior)
    job_path = root / "JOB.json"
    job_bytes = C.encoded(job)
    jf = os.open(job_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        C.need(os.write(jf, job_bytes) == len(job_bytes), "short frozen CPU job write")
        os.fsync(jf)
    finally:
        os.close(jf)
    rd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(rd)
    finally:
        os.close(rd)
    job_sha = file_hash(job_path)
    controller.reserve_launch(worker["id"], lease, job_path, launcher_sha, job["domain_sha256"], device,
                              domain, log_limit=job["per_log_bytes"])
    # These callbacks are explicit CPU fault injection, not production options.
    if fault == "job_after_bind_changed":
        bind = controller.bind_child
        def changed_after_bind(*args):
            result = bind(*args)
            with job_path.open("ab") as f:
                f.write(b" "); f.flush(); os.fsync(f.fileno())
            return result
        controller.bind_child = changed_after_bind
    if fault in ("result_unknown", "log_fsync", "log_partial"):
        if fault == "result_unknown":
            def unknown(*args):
                raise C.Closed("injected source-bound result transport uncertainty")
            controller.supervisor_result = unknown
        else:
            verify_log = controller._verify_log
            def uncertain_log(name, count):
                if name == "stdout":
                    if fault == "log_fsync":
                        raise OSError(5, "injected controller log fsync failure")
                    fd = logs[name]
                    os.ftruncate(fd, max(0, os.fstat(fd).st_size - 1))
                return verify_log(name, count)
            controller._verify_log = uncertain_log
    child = None
    launcher_image_fd = None
    launch_pidfd = None
    child_peer = None
    threads, errors, roles = [], [], []
    stop_seen = None
    try:
        # No inherited injection variables, GPU visibility or unreviewed env.
        env = {"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C", "CUDA_VISIBLE_DEVICES": ""}
        launcher_image_fd = sealed_cpu_image(launcher, launcher_sha)
        child = subprocess.Popen(["/proc/self/fd/" + str(launcher_image_fd), "--cpu-fixed-worker", str(job_path), job_sha],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            pass_fds=tuple(launch_logs.values()) + (launcher_image_fd,), env=env)
        launch_pidfd = os.pidfd_open(child.pid, 0)
        ready = select.select([child.stdout], [], [], 3)[0]
        C.need(ready and child.stdout.readline() == b"CPU_BRIDGE_READY\n", "CPU launch READY barrier missing")
        controller.register_launcher(child, logs)
        if fault == "before_bind_crash":
            signal.pidfd_send_signal(launch_pidfd, signal.SIGKILL)
        else:
            def serve_all():
                try:
                    for _ in range(3):
                        roles.append(broker.serve_one())
                except BaseException as error:
                    errors.append(str(error))
            t = threading.Thread(target=serve_all)
            threads.append(t)
            t.start()
            if fault == "job_changed":
                with job_path.open("ab") as f:
                    f.write(b" ")
                    f.flush(); os.fsync(f.fileno())
            child.stdin.write(b"1")
            child.stdin.flush()
            if fault == "after_bind_crash":
                until = time.monotonic() + 3
                while controller.bridge["phase"] not in ("CHILD_BOUND", "LAUNCHER_CLOSED", "WORKER_ACTIVE", "WORKER_CLOSED"):
                    C.need(time.monotonic() < until, "test BINDCHILD timeout")
                    time.sleep(.001)
                signal.pidfd_send_signal(launch_pidfd, signal.SIGKILL)
            if fault == "parent_disconnect":
                broker.sock.close()
                controller.disconnect("injected controller socket loss")
            for t in threads:
                t.join(20)
                C.need(not t.is_alive(), "CPU bridge supervisor finite timeout")
            C.need(not errors, "bridge session error: " + str(errors))
            controller.reap_launcher()
            controller.confirm_worker_exit(worker["id"])
            C.need(roles == ["launcher", "worker", "supervisor"], "launch/worker/supervisor order changed")
            C.need(controller.state["worker_index"] == 1 and controller.state["stage_index"] == 0,
                   "CPU bridge must not invent a native stage seal")
        C.need(controller.bridge["phase"] == "COMPLETE" and controller.state["worker_index"] == 1,
               "exited or crashed launcher without a bound complete result is uncertain")
    except BaseException as error:
        stop_seen = str(error)
        controller.disconnect(stop_seen)
    finally:
        for t in threads:
            t.join(4)
        if child is not None and child.returncode is None:
            # Only this exact owned std-only launcher can be signalled.
            try:
                if not select.select([launch_pidfd], [], [], 0)[0]:
                    signal.pidfd_send_signal(launch_pidfd, signal.SIGKILL)
                child.wait(timeout=3)
            except (ProcessLookupError, ChildProcessError):
                pass
        if child is not None:
            out = child.stdout.read(4097)
            err = child.stderr.read(4097)
            (root / "LAUNCHER.stdout.log").write_bytes(out)
            (root / "LAUNCHER.stderr.log").write_bytes(err)
        # Child cleanup is performed only by its source-bound C++ parent;
        # controller never sends signals to unknown process IDs or groups.
        report = {"status": "PASS_CPU_BRIDGE" if stop_seen is None else "STOPPED_CPU_BRIDGE",
            "stop_reason": stop_seen, "source_epoch": source_hashes, "ELF_NEEDED": needed,
            "launcher_sha256": launcher_sha, "worker_sha256": worker_sha,
            "roles_observed": roles, "phase": None if controller.bridge is None else controller.bridge["phase"],
            "counts_scope": "SYNTHETIC_RESERVATIONS_NOT_HARDWARE_OPERATIONS",
            "counts": controller.state["counts"], "worker_index": controller.state["worker_index"],
            "stage_index": controller.state["stage_index"], "native_checks": "ALL_261_NOT_RUN",
            "model_creations": 0, "backend_initializations": 0, "GPU_contexts": 0,
            "actual_placement_actions": 0, "model_forwards": 0, "native_ELF_invocations": 0,
            "actual_cgroup_activation": False, "automatic_retry": False, "refund": False}
        (root / "RESULT.json").write_bytes(C.encoded(report))
        broker.close()
        controller.store.close()
        for fd in logs.values():
            os.close(fd)
        for fd in launch_logs.values():
            os.close(fd)
        for fd in (launch_pidfd, controller.child_pidfd, launcher_image_fd):
            if fd is not None:
                os.close(fd)
    return report


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True); p.add_argument("--launcher", required=True)
    p.add_argument("--worker", required=True); p.add_argument("--launcher-sha256", required=True)
    p.add_argument("--worker-sha256", required=True)
    a = p.parse_args()
    from cpu_resource_fixture import cpu_domain_factory
    result = run_case(Path(a.out), Path(a.launcher), Path(a.worker), a.launcher_sha256, a.worker_sha256,
                      domain_factory=cpu_domain_factory)
    print(json.dumps(result, sort_keys=True))
    if result["status"] != "PASS_CPU_BRIDGE":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
