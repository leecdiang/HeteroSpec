"""Anonymous immutable Git/text-packet readback, CPU only; never a native runner."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

PREFIX = "benchmarks/server_expansion_v1/N/production_bridge_20261112/"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    p = argparse.ArgumentParser(); p.add_argument("--commit", required=True)
    p.add_argument("--index", required=True); p.add_argument("--out", required=True)
    p.add_argument("--source-repo", required=True)
    p.add_argument("--prior-public-bytes", help="read-only cache from the prior completed anonymous-transfer epoch")
    a = p.parse_args()
    if not re.fullmatch("[0-9a-f]{40}", a.commit):
        raise RuntimeError("immutable Git commit required")
    root = Path(a.out)
    if not root.is_absolute() or root.exists():
        raise RuntimeError("fresh absolute readback directory required")
    root.mkdir(mode=0o700)
    index = json.loads(Path(a.index).read_bytes())
    if not index or len(index) > 4096:
        raise RuntimeError("bounded exact public index required")
    base = "https://raw.githubusercontent.com/leecdiang/HeteroSpec/" + a.commit + "/"
    def fetch(item):
        name = item["path"]
        if not name.startswith(PREFIX) or ".." in Path(name).parts or "\\" in name or not 0 <= item["bytes"] <= 16 * 1024 * 1024:
            raise RuntimeError("outside/big public file")
        # The first urllib epoch's TLS EOF is preserved. curl uses the actual
        # host's working certificate/proxy path; no credential/header is sent.
        if a.prior_public_bytes:
            prior = Path(a.prior_public_bytes) / name
            if not prior.is_file() or prior.is_symlink() or prior.stat().st_size != item["bytes"]:
                raise RuntimeError("prior anonymous bytes absent/changed")
            value = prior.read_bytes()
        else:
            transfer = subprocess.run(["/usr/bin/curl", "--fail", "--silent", "--show-error", "--location",
                "--proto", "=https", "--proto-redir", "=https", "--connect-timeout", "10", "--max-time", "30",
                "--max-filesize", str(item["bytes"] + 1), "--retry", "1", "--retry-all-errors", "--retry-delay", "1",
                "--write-out", "\n%{http_code}", base + name], capture_output=True, timeout=65)
            if transfer.returncode or not transfer.stdout.endswith(b"\n200"):
                raise RuntimeError("bounded anonymous curl transfer failed: " + name + " " + transfer.stderr.decode(errors="replace"))
            value = transfer.stdout[:-4]
        if len(value) != item["bytes"] or hashlib.sha1(b"blob " + str(len(value)).encode() + b"\0" + value).hexdigest() != item["sha"]:
            raise RuntimeError("public Git blob identity mismatch: " + name)
        dest = root / "downloads" / name; dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("xb") as f:
            f.write(value)
        return dict(path=name, bytes=len(value), git_blob_sha1=item["sha"], sha256=sha(value),
                    anonymous_HTTP="200_PRIOR_TRANSFER_EPOCH_BYTES_REVERIFIED" if a.prior_public_bytes else 200)
    try:
        with ThreadPoolExecutor(max_workers=4) as pool:
            verified = list(pool.map(fetch, index))
        downloaded = root / "downloads" / PREFIX
        packet = json.loads((downloaded / "PACKET.json").read_bytes())
        archive = downloaded / "PRODUCTION_BRIDGE_CPU_PACKET.tar.gz"
        if sha(archive.read_bytes()) != packet["archive_sha256"]:
            raise RuntimeError("anonymous packet SHA mismatch")
        packaging = Path(a.source_repo) / "benchmarks/server_expansion_v1/N/admission_controller_20261112/packaging"
        sys.path.insert(0, str(packaging))
        spec = importlib.util.spec_from_file_location("frozen_CPU_archive", packaging / "archive.py")
        reader = importlib.util.module_from_spec(spec); spec.loader.exec_module(reader)
        restored = root / "restored"
        replay = reader.replay(archive, restored, packet["archive_sha256"])
        source = restored / PREFIX
        env = {"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C", "CUDA_VISIBLE_DEVICES": ""}
        cmds = [([sys.executable, str(source / "tests/bridge_tests.py"), "--out", str(root / "controller-mock"), "-v"], "controller32.log"),
                ([sys.executable, str(source / "tests/resource_tests.py"), "--out", str(root / "resource-mock")], "resource27.log"),
                ([sys.executable, str(source / "finalize_resource_manifest.py"), "--selection", str(source / "review/MEASURED_SELECTION_FINAL02.json"),
                  "--out", str(root / "FINAL_MANIFEST.json")], "manifest.log")]
        for cmd, name in cmds:
            with (root / name).open("x") as out:
                result = subprocess.run(cmd, stdout=out, stderr=subprocess.STDOUT, env=env, timeout=120)
            if result.returncode:
                raise RuntimeError("public CPU replay failure, log retained: " + name)
        if (root / "FINAL_MANIFEST.json").read_bytes() != (source / "FINAL_EXECUTION_MANIFEST_NOT_ADMITTED.json").read_bytes():
            raise RuntimeError("public manifest regeneration bytes differ")
        native = json.loads((source / "NATIVE_261_NOT_RUN.json").read_bytes())
        if native["total"] != 261 or native["native_checks_run"] != 0 or any(c["native_status"] != "NOT_RUN" for c in native["checks"]):
            raise RuntimeError("native NOT_RUN graph changed")
        receipt = dict(status="PASS_ANONYMOUS_PUBLIC_CPU_CLOSURE", commit=a.commit,
            checked_Git_files=len(verified), files=verified, packet=packet, strict_restore=replay,
            CPU_replay=dict(controller_tests=32, resource_tests=27, final_manifest="BYTE_IDENTICAL"),
            all261_native_checks="NOT_RUN", model_backend_GPU_context_placement_forward_native_ELF=0,
            not_repeated=["actual std-only fourteen-case process suite", "native ELF/model execution", "private raw process/job identity verification", "GPU numerical qualification"],
            transport="prior anonymous curl transfer bytes reverified from immutable Git identities" if a.prior_public_bytes else "fresh anonymous curl HTTP200",
            readback_script_sha256=sha(Path(__file__).read_bytes()),
            scope="Anonymous text/source identity and lightweight CPU replay only")
        (root / "PUBLIC_READBACK.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
        print(json.dumps({k: receipt[k] for k in ("status", "commit", "checked_Git_files", "strict_restore", "CPU_replay", "all261_native_checks")}))
    except BaseException as e:
        (root / "STOP.json").write_text(json.dumps({"status": "READBACK_FAILED_NOT_NATIVE", "reason": str(e), "native_calls": 0}) + "\n")
        raise


if __name__ == "__main__":
    main()
