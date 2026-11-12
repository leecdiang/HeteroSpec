"""Final additive independent receipt after source fixes; no native execution."""
from pathlib import Path
import hashlib
import json
import re
import recompute_preparation as independent

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "final"


def main():
    independent.need(not OUT.exists(), "fresh final review directory required")
    independent.OUT = OUT
    independent.main()
    result = independent.read(OUT / "INDEPENDENT_RAW_CHECK.json")
    for run in result["test_runs"]:
        label = run["mode"]
        raw = (OUT / ("all_tests_" + label + ".log")).read_bytes()
        match = re.search(rb"Ran (\d+) tests", raw)
        independent.need(match is not None, "test count missing")
        run["test_count"] = int(match.group(1))
    cases = independent.read(ROOT / "qualification/CASES.json")["cases"]
    independent.need(len(cases) == 22 and len({c["id"] for c in cases}) == 22, "qualification case identity")
    native_results = [v["native_result"] for c in cases for v in c["arms"].values()]
    independent.need(len(native_results) == 66 and set(native_results) == {"NOT_RUN"}, "native results misclassified")
    result["qualification_expectations"] = {"cases": 22, "arm_case_cells": 66, "native_result_all": "NOT_RUN", "source_sha256": independent.sha((ROOT / "qualification/CASES.json").read_bytes())}
    plan = independent.read(ROOT / "RESOURCE_PLAN.json")
    independent.need(plan["gpu_admission"].startswith("BLOCKED"), "GPU plan unexpectedly released")
    result["resource_plan"] = {"admission": plan["gpu_admission"], "plan_sha256": independent.sha((ROOT / "RESOURCE_PLAN.json").read_bytes()), "old_budget_borrowing": False, "live_exclusive_lock_or_worker_monitor": "NOT_IMPLEMENTED_NOT_CLAIMED"}
    buildpath = ROOT / "build_tools/build-v5/BUILD.json"
    build = independent.read(buildpath)
    independent.need(build["returncode"] == 0 and build["execution_enabled"] is False and build["native_execution"] == "NOT_RUN", "final build status")
    exe = ROOT / "build_tools/build-v5/operator_probe.exe"
    independent.need(independent.sha(exe.read_bytes()) == build["executable_sha256"], "final compiled executable hash")
    for name, h in build["source_sha256"].items():
        independent.need(independent.sha((ROOT / name).read_bytes()) == h, "final native source hash: " + name)
    log = (ROOT / "build_tools/build-v5/build.log").read_bytes()
    text = log.decode("utf8", errors="replace")
    entries = re.findall(r"Compiling entry function '([^']+)'.*?([0-9]+) bytes stack frame, ([0-9]+) bytes spill stores, ([0-9]+) bytes spill loads.*?Used ([0-9]+) registers, used ([0-9]+) barriers(?:, ([0-9]+) bytes smem)?", text, flags=re.S)
    independent.need(len(entries) == 3, "three resource kernel records")
    resources = []
    for symbol, stack, store, load, regs, barriers, smem in entries:
        resources.append({"symbol": symbol, "stack_bytes": int(stack), "spill_store_bytes": int(store), "spill_load_bytes": int(load), "registers": int(regs), "barriers": int(barriers), "shared_bytes": int(smem or 0)})
    independent.need([(r["registers"], r["shared_bytes"]) for r in resources] == [(63, 3072), (91, 6144), (24, 0)], "compiled resource values")
    source = (ROOT / "native/operator_probe.cu").read_text(encoding="utf8")
    mainpart = source[source.index("int main("):]
    independent.need(mainpart.index("need(execution_enabled") < mainpart.index("cudaSetDevice"), "compile gate is not before explicit CUDA admission")
    independent.need("-DHS_NATIVE_EXECUTION_ENABLED=0" in build["command"], "final build execution enabled")
    result["final_operator_build"] = {"status": "COMPILE_ONLY_EXECUTION_DISABLED", "receipt_sha256": independent.sha(buildpath.read_bytes()), "build_log_sha256": independent.sha(log), "exe_sha256": build["executable_sha256"], "resources": resources, "occupancy": "unknown", "DRAM_L2": "unknown", "ABC_numerical_replay": "NOT_RUN"}
    constructed_v2 = ROOT / "request/cpu_result_v2/CONSTRUCTED_RAW.json"
    independent.need(constructed_v2.is_file(), "corrected request CPU record missing")
    result["corrected_request_fixture"] = independent.check_constructed(independent.read(constructed_v2))
    result["request_frontend_compilation"] = {"status": "FAILED_PRESERVED", "native_executable": "NOT_CREATED", "source_transform": "PREPARED_NOT_NATIVE_QUALIFIED", "timing_header": "NOT_INTEGRATED"}
    result["initial_review_findings"] = [
        {"finding": "Self-reported requested rows/vocab could omit complete output obligations", "resolution": "External frozen requested rows and vocabulary now required; tested"},
        {"finding": "Arbitrary SM120 UUID could pass descriptor metadata admission", "resolution": "External authorized UUID now required; tested"},
        {"finding": "Blocked resource plan could pass helper; fractional actual counts; overruns not preserved", "resolution": "Blocked plan enforced in admission/reserve; integer counts and persisted charged overrun halt; tested"},
        {"finding": "Caller complete_endpoint flag could be mistaken for complete service admission", "resolution": "Self declaration marked UNVERIFIED; external endpoint audit/coverage required; tested"},
        {"finding": "Operator job Boolean alone was not a resource gate", "resolution": "Final artifact is compiled execution-disabled; future launcher/ledger/native qualification explicitly still missing"}
    ]
    result["limitations"] = ["Original execution thread remains unverified; native GPU gate remains blocked", "Final operator binary is execution-disabled and was not invoked; A/B/C numerical or timing data do not exist", "Native recipe qualification is66 NOT_RUN arm-case cells", "Recovered historical A/B equality is a derived-real-q32-prefix replay, not a new current q8 model capture", "Constructed request has logical token-list states, not native KV/geometry; no real dynamic request is certified", "Dynamic frontend build failed; full draft snapshots, guard/poison/timing integration and independent reference bridge remain open", "Resource helper is not yet a live process-bound lock/window/launch monitor; changing the blocked plan alone must not be used as launch authorization", "Independent endpoint receipt authority and always-on instrumentation remain external integration obligations", "Compiler registers/shared/spills do not establish achieved occupancy, memory traffic, latency, novelty or complete-service value"]
    result["verdict"] = "PREPARATION_REVIEW_PASSED_WITH_EXPLICIT_INCOMPLETE_NATIVE_GATES"
    (OUT / "FINAL_INDEPENDENT_REVIEW.json").write_text(json.dumps(result, indent=2), encoding="utf8")
    print(json.dumps({"verdict": result["verdict"], "decision": result["decision"], "tests": [r["test_count"] for r in result["test_runs"]], "native_cases": len(native_results), "resources": [(r["registers"], r["shared_bytes"]) for r in resources]}, indent=2))


if __name__ == "__main__":
    main()
