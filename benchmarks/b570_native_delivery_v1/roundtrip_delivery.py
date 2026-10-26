"""Re-download both assets into a fresh directory and run CPU-only delivery audits."""
from pathlib import Path
import argparse
import datetime
import json
import stat
import zipfile

from download import download
from verify_package import digest, portable_path, verify_package, write_json


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def extract(archive, dest):
    if dest.exists():
        raise ValueError("Fresh extraction directory required")
    with zipfile.ZipFile(archive) as zipped:
        seen = set()
        for item in zipped.infolist():
            name = portable_path(item.filename)
            if name.casefold() in seen or item.is_dir():
                raise ValueError("Duplicate or unexpected directory ZIP member: " + name)
            if stat.S_ISLNK(item.external_attr >> 16):
                raise ValueError("ZIP symlink is not allowed: " + name)
            seen.add(name.casefold())
        dest.mkdir()
        for item in zipped.infolist():
            target = dest / item.filename
            if not target.resolve().is_relative_to(dest.resolve()):
                raise ValueError("ZIP member escapes extraction directory")
            target.parent.mkdir(parents=True, exist_ok=True)
            with zipped.open(item) as source, target.open("xb") as output:
                while block := source.read(1024 * 1024):
                    output.write(block)
    return len(seen)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--access", type=Path, required=True)
    parser.add_argument("--dest", type=Path, required=True)
    parser.add_argument("--asset", choices=("minimal", "four_input_references"),
                        help="Verify one asset; omit to verify both")
    args = parser.parse_args()
    if args.dest.exists():
        raise ValueError("Fresh round-trip destination required")
    args.dest.mkdir(parents=True)
    access = json.loads(args.access.read_text(encoding="utf-8"))
    started = utc()
    results = []
    for kind in ([args.asset] if args.asset else ("minimal", "four_input_references")):
        row = access["assets"][kind]
        archive = args.dest / row["name"]
        print(json.dumps({"stage": "remote_download", "asset": row["name"]}), flush=True)
        download_started = utc()
        receipt = download(row, archive)
        receipt.update(started_utc=download_started, completed_utc=utc(), asset_id=row["id"])
        write_json(args.dest / (kind + "-download.json"), receipt)
        root = args.dest / kind
        members = extract(archive, root)
        if digest(root / "delivery/verify_package.py") != digest(Path(__file__).with_name("verify_package.py")):
            raise ValueError("Packaged verifier differs from the invoked verifier")
        result = verify_package(root, args.dest / (kind + "-audit"))
        if members != result["integrity"]["verified_files"] + 1:
            raise ValueError("ZIP/extracted inventory mismatch")
        results.append({"asset": kind, "download": receipt, "zip_file_members": members,
                        "verification": result})
        print(json.dumps({"stage": "CPU_VERIFIED", "asset": kind,
                          "zip_file_members": members}), flush=True)
    receipt = {"status": "REMOTE_DOWNLOAD_EXTRACT_CPU_VERIFY_PASS", "started_utc": started,
               "completed_utc": utc(), "repository": access["repository"],
               "release_id": access["release_id"], "assets": results,
               "credential_scope": "Current authorized repository account; separate reader account not tested",
               "new_gpu_requests": 0, "new_native_runs": 0, "new_performance_experiments": 0}
    write_json(args.dest / "ROUNDTRIP.json", receipt)
    print(json.dumps({"status": receipt["status"], "receipt": str(args.dest / "ROUNDTRIP.json")}), flush=True)


if __name__ == "__main__":
    main()
