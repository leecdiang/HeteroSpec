"""Check one archived vector/state pair as a CPU parser-format smoke only."""
import datetime
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from admission import AdmissionError, NativeStateSpec, digest, read_artifact, read_native_state, validate_full_vector


def main():
    old_root = ROOT.parent / "q8rtx213-supplement-runtime-20261109"
    index_path = ROOT.parent / "q8rtx213-supplement-evidence-20261109/ARCHIVE_INDEX.json"
    index = json.loads(index_path.read_bytes())
    prefix = "runs/rtx213-s1-LOCAL-loop4-k3/native/boundary-natural-heavy/target/"
    paths = [prefix + "state/commit-0/sequence.bin", prefix + "verify-0-3.f32"]
    frozen = [{"path": paths[0], "bytes": 26840064,
               "sha256": "f10074d2f8c21c26622f5b51f1ce55fe463e1d69a3d3542cb04fe4684c9d2790"},
              {"path": paths[1], "bytes": 607744,
               "sha256": "25a75207dc30db1c6f0995fc6d5e21ad41d5432db4dc6f5b01e875f41c32fa25"}]
    for record in frozen:
        matches = [x for x in index["files"] if x["path"] == "runtime/" + record["path"]]
        if len(matches) != 1 or any(matches[0][key] != record[key] for key in ("bytes", "sha256")):
            raise AdmissionError("ARCHIVE_COMMITMENT", record["path"])
    state = read_native_state(read_artifact(old_root, frozen[0]), 182, NativeStateSpec(36, 1024, 1024, 1024))
    vector = validate_full_vector(read_artifact(old_root, frozen[1]), 151936)
    result = {"status": "PASS_ARCHIVED_BYTE_FORMAT_ONLY", "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "archive_index_sha256": digest(index_path.read_bytes()), "input_records": frozen,
              "state": state, "vector": vector, "model_requests": 0, "gpu_runs": 0,
              "native_qualification": "NOT_RUN_NEW_BINARIES", "scope": "One previously captured #215 pair read with new CPU parser; does not validate current native semantics, missing old states, or a new execution arm.",
              "source_sha256": {"src/admission.py": digest((ROOT / "src/admission.py").read_bytes()),
                                "qualification/check_legacy_byte_format.py": digest(Path(__file__).read_bytes())}}
    destination = ROOT / "qualification/LEGACY_FORMAT_SMOKE.json"
    with destination.open("x", encoding="utf8") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
