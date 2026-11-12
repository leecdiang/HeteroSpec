"""Read-only code/staging audit plus compact status write; no compiler/models."""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent


def sha(p):
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        while b := f.read(4 * 1024 * 1024):
            h.update(b)
    return h.hexdigest()


def tree(root):
    root = Path(root)
    entries = [{"path": p.relative_to(root).as_posix(), "bytes": p.stat().st_size, "sha256": sha(p)}
               for p in sorted(root.rglob("*")) if p.is_file()]
    canonical = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()
    return entries, {"files": len(entries), "bytes": sum(p["bytes"] for p in entries),
                     "canonical_tree_sha256": hashlib.sha256(canonical).hexdigest()}


def main():
    old = Path("D:/HeteroSpec-PC/.venv-analysis/Lib/site-packages/ziglang")
    copied = HERE / "compiler_copy"
    a, ai = tree(old / "lib")
    b, bi = tree(copied / "lib")
    if a != b or sha(old / "zig.exe") != sha(copied / "zig.exe"):
        raise RuntimeError("compiler staging bytes differ")
    stage = {"status": "BYTE_IDENTICAL_LOCAL_COMPILER_COPY", "old_read_only": str(old),
             "copy": str(copied), "compiler_sha256": sha(copied / "zig.exe"),
             "library_identity": bi, "native_worker_or_GPU_execution": False}
    with (HERE / "COMPILER_STAGING.json").open("x", encoding="utf8") as f:
        json.dump(stage, f, indent=2)
    sources = [p for p in HERE.iterdir() if p.is_file()] + list((HERE.parent / "tests").glob("test_request*.py"))
    result = {"schema": "heterospec.request-preparation.v2", "status": "INCONCLUSIVE_NATIVE_REQUEST_AND_SERVICE_NOT_RUN",
              "CPU_tests": {"normal": 19, "optimized": 19, "both_passed": True,
                            "receipt": "cpu_result_v2/RESULT.json", "initial_version_retained": "cpu_result/RESULT.json"},
              "constructed_chain": "PASS_LOGICAL_FIXTURE_ONLY", "full_vector_pairs": 17,
              "real_dynamic_request_chain": "NOT_RUN_NOT_COVERED_BY_SEPARATE_FIXED_K_TRACES",
              "native_KV_or_geometry_qualification": False, "native_owner_guard_qualification": False,
              "complete_service_cost": "NOT_RUN_NO_INDEPENDENT_ENDPOINT_AUDIT",
              "cost_reader_endpoint_fix": "SELF_DECLARED_FLAG_CANNOT_ADMIT_SERVICE_CLAIM",
              "new_model_requests": 0, "new_model_rows": 0, "native_GPU_launches": 0,
              "frontend_source_preparation": "prepared_frontend_PREPARATION.json",
              "frontend_compile": "FAILED_NOT_VERIFIED", "frontend_link": "NOT_RUN",
              "failed_build_epochs": ["build/FAILED.json", "build_v2/FAILED.json"],
              "independent_header_compile_log": "build_v2/timeline-compile.log",
              "compiler_staging": stage,
              "code_and_document_sha256": {str(p.relative_to(HERE.parent)): sha(p) for p in sources},
              "receipts_sha256": {name: sha(HERE / name) for name in
                                   ("cpu_result/RESULT.json", "cpu_result_v2/RESULT.json", "prepared_frontend_PREPARATION.json",
                                    "build/FAILED.json", "build_v2/FAILED.json", "build_v2/timeline-compile.log")},
              "old_sources_and_data_modified": False}
    with (HERE / "STATUS.json").open("x", encoding="utf8") as f:
        json.dump(result, f, indent=2)
    print(json.dumps({k: result[k] for k in ("status", "CPU_tests", "frontend_compile", "new_model_requests", "native_GPU_launches")}, indent=2))


if __name__ == "__main__":
    main()
