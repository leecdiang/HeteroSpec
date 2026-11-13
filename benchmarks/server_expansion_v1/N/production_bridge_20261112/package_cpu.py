"""Allowlisted UTF-8 CPU review package; never opens models or native ELFs."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PACKAGING = HERE.parent / "admission_controller_20261112/packaging"
sys.path.insert(0, str(PACKAGING))
spec = importlib.util.spec_from_file_location("cpu_text_archive", PACKAGING / "archive.py")
archive = importlib.util.module_from_spec(spec); spec.loader.exec_module(archive)


def build(repo, output, deny=()):
    repo, output = Path(repo).resolve(), Path(output)
    roots = [HERE, HERE.parent / "admission_controller_20261112",
             HERE.parent / "native_chain_successor_20261112", HERE.parent / "n1a_lifecycle_20261112"]
    files = []
    for root in roots:
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.is_symlink() or "__pycache__" in path.parts:
                continue
            if path.suffix in (".gz", ".pyc", ".o", ".so", ".a", ".bin") or path.name in (
                    "PACKET.json", "PUBLIC_READBACK.json", "CPU_PACKET_SELECTION.json"):
                continue
            raw = path.read_bytes()
            try:
                raw.decode("utf-8", errors="strict")
            except UnicodeDecodeError:
                raise RuntimeError("unexpected non-text candidate: " + str(path.relative_to(repo)))
            files.append({"path": path.relative_to(repo).as_posix(), "sha256": hashlib.sha256(raw).hexdigest(),
                "bytes": len(raw), "payload_kind": "utf8-text", "public_review": "TEXT_REVIEWED_NO_PRIVATE_IDENTIFIERS"})
    if len(files) > 4096 or sum(x["bytes"] for x in files) > 128 * 1024 * 1024:
        raise RuntimeError("CPU review packet exceeds bounded existing text pool; no output written")
    selection = {"schema": "hs.strong.public-selection.v1", "terminal_status": "NOT_ADMITTED",
                 "private_literals": list(deny), "files": files, "withheld_numeric_payloads": []}
    receipt = archive.create(repo, selection, output)
    receipt.update(scope="PUBLIC_CPU_TEXT_ONLY_NOT_NATIVE_VALIDATION", native_GPU_calls=0,
                   all_261_native_checks="NOT_RUN", payload_total_bytes=sum(x["bytes"] for x in files),
                   private_original_CPU_process_job_bytes="WITHHELD_HASH_INDEXED_NOT_NUMERICAL_GPU_CAPTURES")
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--repo", required=True); p.add_argument("--out", required=True)
    p.add_argument("--deny-file"); p.add_argument("--receipt", required=True)
    a = p.parse_args()
    deny = [] if a.deny_file is None else [v for v in Path(a.deny_file).read_text().splitlines() if v]
    result = build(a.repo, a.out, deny)
    with Path(a.receipt).open("x") as output:
        json.dump(result, output, sort_keys=True, indent=2); output.write("\n")
    print(json.dumps(result, sort_keys=True))
