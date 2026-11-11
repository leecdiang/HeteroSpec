"""Reconstruct the source-pinned Linux M2 worker and generate a fresh tail patch.

The public PR203 portability functions and PR209 M2 transform execute only on a
fresh copy of the authenticated source-kit frontend. No original source or
reference is edited. This is a reconstructed source candidate, not a claim to
reproduce an earlier host-executed binary.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import shutil
import sys
import urllib.request
from patch_lazy_tail import generate

HERE = Path(__file__).resolve().parent
PR203 = "592abdfe9267fd97ecbde18cd0ee9a1bfc319e20"
PR209 = "2d076402b4ddc29c92549d360cd974af40d3f0a4"
PINS = {
    "sources.py": (PR203, "benchmarks/linux_transfer_v1/sources.py", "08d88ce0a7d84d24aa19689120b29c1cdb8b39bd4a5edc66f3c86e391be37bc5"),
    "adapt_host.py": (PR203, "benchmarks/linux_transfer_v1/adapt_host.py", "7d9bea86a87181b75dbe4e2cc0ccc13324439d2881a51d5e774b434f50984412"),
    "common.py": (PR203, "benchmarks/linux_transfer_v1/common.py", "f699d98affffaa8fd46fcf71059130f47b8663b8567b94339231e10c70753052"),
    "native/linux_platform.hpp": (PR203, "benchmarks/linux_transfer_v1/native/linux_platform.hpp", "4f3caf0b09dd6172573ebfe89e29f10fdbbfbf3ca3588f4d5f0f9a9e1ffaa3dc"),
    "native/linux_profile_disabled.hpp": (PR203, "benchmarks/linux_transfer_v1/native/linux_profile_disabled.hpp", "99e830b7dfb01134f6c43da6e6e5cd22508526cb21811fc2bcaff617c7fd46d3"),
    "m2_transform.py": (PR209, "benchmarks/server_expansion_v1/M2/transform.py", "d9d92ab4aa34afbf64194ea25d1caac2f02e625d7647872efaa702dc48d27cde"),
    "m2_tapes.hpp": (PR209, "benchmarks/server_expansion_v1/M2/native/tapes.hpp", "c89eefd812fe7f4b6020a24a20aa839efa2f4a26f8a4670778313983380763b1"),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kit", type=Path, default=HERE / "sourcekit")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists() or args.out.is_symlink():
        raise ValueError("fresh reconstruction directory required")
    kit = args.kit.resolve()
    original = kit / "native/frontend"
    expected = json.loads((kit / "SOURCE_ASSET_MANIFEST.json").read_bytes())["files"]
    actual = {}
    for path in original.rglob("*"):
        if path.is_symlink():
            raise ValueError("explicit regular frontend input required")
        if path.is_file():
            name = path.relative_to(kit).as_posix()
            row = {"sha256": digest(path), "bytes": path.stat().st_size}
            if expected.get(name) != row:
                raise ValueError("original frontend hash mismatch: " + name)
            actual[name] = row
    if actual != {name: row for name, row in expected.items() if name.startswith("native/frontend/")}:
        raise ValueError("original frontend membership differs")
    out = args.out.resolve()
    out.mkdir(parents=True)
    tools = out / "reviewed_tools"
    tools.mkdir()
    fetched = {}
    for name, (commit, repository_path, sha) in PINS.items():
        url = "https://raw.githubusercontent.com/leecdiang/HeteroSpec/" + commit + "/" + repository_path
        path = tools / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(url, timeout=60) as source:
            payload = source.read()
        if hashlib.sha256(payload).hexdigest() != sha:
            raise ValueError("reviewed transformation bytes changed: " + name)
        with path.open("xb") as destination:
            destination.write(payload)
        fetched[name] = {"url": url, "sha256": sha, "bytes": len(payload)}
    sys.path.insert(0, str(tools))
    source_tool = module(tools / "sources.py", "reviewed_pr203_sources")
    adapt_tool = module(tools / "adapt_host.py", "reviewed_pr203_adapt")
    common = module(tools / "common.py", "reviewed_pr203_common")
    stage01 = out / "stage-01"
    stage01.mkdir()
    shutil.copytree(original, stage01 / "frontend")
    port = source_tool.port(stage01 / "frontend")
    common.save(stage01 / "PORT.json", port)
    common.save(stage01 / "SOURCE_LOCK.json", {"status": port["status"], "frontend": common.inventory(stage01 / "frontend")})
    adapt_tool.adapt(stage01, out / "stage-04")
    stage04_worker = out / "stage-04/frontend/worker.cpp"
    if digest(stage04_worker) != "4a748ebd7d7aea489ff00e88b55f3584ae10cdabf244bd34f90040f34c18ec40":
        raise ValueError("reconstructed stage04 worker differs")
    m2 = out / "m2_frontend"
    shutil.copytree(out / "stage-04/frontend", m2)
    module(tools / "m2_transform.py", "reviewed_pr209_m2_transform").transform(m2)
    shutil.copy2(tools / "m2_tapes.hpp", m2 / "m2_tapes.hpp")
    if digest(m2 / "worker.cpp") != "429ca63224bffdc62fff65cc0c4b4199ea0ae9677fa3b087d1bbbe1d01b12938":
        raise ValueError("reconstructed M2 worker differs")
    candidate = generate(m2 / "worker.cpp", out / "candidate")
    full_candidate = out / "candidate_frontend"
    shutil.copytree(m2, full_candidate)
    for name in ("worker.cpp", "lazy_draft_tail.hpp"):
        shutil.copy2(out / "candidate" / name, full_candidate / name)
    result = dict(schema="heterospec.native-tail.reconstructed-m2.v1", status="RECONSTRUCTED_NOT_NATIVE_QUALIFIED",
                  reviewed_transformations=fetched, original_frontend=actual,
                  stage04_worker_sha256=digest(stage04_worker), m2_worker_sha256=digest(m2 / "worker.cpp"),
                  candidate=candidate, candidate_frontend=common.inventory(full_candidate),
                  numerical_source_edits=False, historical_host_binary_identity_claimed=False,
                  GPU_qualification="NOT_RUN", performance_claim=False)
    (out / "RECONSTRUCTION.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key not in ("reviewed_transformations", "original_frontend", "candidate_frontend")}, indent=2))


if __name__ == "__main__":
    main()
