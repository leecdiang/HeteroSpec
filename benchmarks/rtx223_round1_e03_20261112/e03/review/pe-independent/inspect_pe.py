"""Independent MSVC dumpbin inspection. Never loads or calls the target DLL."""
from pathlib import Path
import datetime
import hashlib
import json
import re
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TARGET = ROOT / "runtime/build-v3/bin/ggml-cuda.dll"
DUMPBIN = Path("D:/rtx184-tools/msvc/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64/dumpbin.exe")
EXPECTED_SHA = "bcdb7642d32609c9242dc8aaecfadfb9f4e082ac8cfeccf5de6b7466546eb24b"
EXPECTED_BYTES = 33850880


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    receipt_path = HERE / "PE_INDEPENDENT_RECEIPT.json"
    need(not receipt_path.exists(), "fresh independent PE receipt required")
    need(TARGET.stat().st_size == EXPECTED_BYTES and sha(TARGET) == EXPECTED_SHA, "target DLL identity mismatch")
    runs, texts = [], {}
    for switch in ("headers", "imports", "exports"):
        args = [str(DUMPBIN), "/nologo", "/" + switch, str(TARGET)]
        run = subprocess.run(args, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
        raw = HERE / (switch + ".txt")
        raw.write_bytes(run.stdout)
        need(run.returncode == 0, "offline dumpbin failed: " + switch)
        texts[switch] = run.stdout.decode("utf8", errors="replace")
        runs.append({"argv": args, "returncode": run.returncode, "raw_path": raw.name, "raw_sha256": sha(raw), "raw_bytes": len(run.stdout)})
    need(TARGET.stat().st_size == EXPECTED_BYTES and sha(TARGET) == EXPECTED_SHA, "target DLL changed during offline inspection")
    exports = re.findall(r"^\s*\d+\s+[0-9A-Fa-f]+\s+[0-9A-Fa-f]{8}\s+(\S+)", texts["exports"], flags=re.M)
    need(bool(exports), "no PE exports parsed")
    required = {
        "hs_e03_runtime_metadata", "hs_e03_select_arm", "hs_e03_selected_arm",
        "hs_e03_pair4_dispatches", "hs_e03_packed_dispatches", "hs_e03_loop4_dispatches",
        "hs_launch_budget_configure_v1", "hs_launch_budget_try_v1", "hs_launch_budget_before_launch_v1",
        "hs_launch_budget_deny_opaque_try_v1", "hs_launch_budget_deny_opaque_v1",
        "hs_launch_budget_snapshot_v1", "hs_launch_budget_metadata_v1"
    }
    missing = sorted(required - set(exports))
    need(not missing, "required runtime/budget export missing: " + repr(missing))
    need("hs_launch_budget_test_reentry_v1" not in exports, "CPU-only test export appears in numerical DLL")
    imports = sorted(set(re.findall(r"^\s*([A-Za-z0-9_.-]+\.dll)\s*$", texts["imports"], flags=re.M | re.I)), key=str.lower)
    low_imports = {name.lower() for name in imports}
    need({"ggml-base.dll", "cudart64_12.dll", "cublas64_12.dll"}.issubset(low_imports), "expected numerical/CUDA imports absent")
    need(re.search(r"8664 machine \(x64\)", texts["headers"], re.I), "not AMD64 PE")
    need(re.search(r"^\s*DLL\s*$", texts["headers"], re.M), "PE DLL flag missing")
    reg = sorted(set(re.findall(r"\b(?:__cuda\w+|cuda\w+|cublas\w+)\b", texts["imports"])))
    policy_names = [n for n in reg if n.startswith("__cudaRegister") or n in ("cudaLaunchKernel", "cudaLaunchKernelExC", "cudaLaunchCooperativeKernel", "cudaGraphLaunch", "cudaMemset", "cudaMemsetAsync") or n.startswith("cublasGemm") or n == "cublasSgemm"]
    receipt = {
        "schema": "heterospec.e03.independent-MSVC-PE-inspection.v1",
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "target": {"path": str(TARGET), "bytes": EXPECTED_BYTES, "sha256": EXPECTED_SHA, "unchanged_after_inspection": True},
        "trusted_parser": {"path": str(DUMPBIN), "sha256": sha(DUMPBIN), "kind": "MSVC dumpbin offline disk parser"},
        "runs": runs,
        "machine": "AMD64",
        "is_DLL": True,
        "export_count": len(exports),
        "required_runtime_budget_exports": sorted(required),
        "missing_required_exports": missing,
        "all_exports": exports,
        "CPU_only_reentry_export_absent": True,
        "imported_DLLs": imports,
        "selected_CUDA_library_import_symbols": policy_names,
        "scope": "PE/DISK IDENTITY ONLY: target DLL was not loaded, its entrypoint/CRT/fatbinary initialization was not run, exports were not called",
        "target_LoadLibrary_calls": 0,
        "CUDA_calls": 0,
        "model_requests": 0,
        "GPU_kernel_launches": 0,
        "findings": [
            "The linked disk DLL contains the required C-arm and budget API export names",
            "Presence of an export does not validate its implementation or prove runtime binding",
            "cuBLAS/cudart import presence remains visible even when source policy rejects selected routes; imports alone neither establish execution nor full physical-kernel coverage",
            "A normal DLL load can execute CRT/TLS/fatbinary registration; this offline inspection deliberately does not attempt it",
            "No native C dispatch, quantized activation/output/state qualification, graph policy execution or performance result is established"
        ],
        "numerical_or_GPU_qualification": "NOT_RUN",
        "verdict": "PASS_PE_IDENTITY_ONLY_NATIVE_GATES_REMAIN_CLOSED"
    }
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf8")
    print(json.dumps({"verdict": receipt["verdict"], "DLL_bytes": EXPECTED_BYTES, "DLL_sha256": EXPECTED_SHA, "exports": len(exports), "required_exports": len(required), "imports": imports, "selected_CUDA_library_import_symbols": policy_names}, indent=2))


if __name__ == "__main__":
    main()
