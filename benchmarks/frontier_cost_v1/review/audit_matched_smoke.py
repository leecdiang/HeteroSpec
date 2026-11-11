"""Independent offline verification of the separate q1-only protocol smoke.

No model execution and no import from the implementation or its comparator.
"""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

if not __debug__:
    raise SystemExit("Run this audit without Python -O or PYTHONOPTIMIZE")


def read(path):
    return json.loads(path.read_text())


def identity(path):
    data = path.read_bytes()
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def main(root, out):
    assert not out.exists()
    run_dir = root / "matched_cost/cpu_protocol_final"
    run = read(run_dir / "RUN.json")
    result = read(run_dir / "native/RESULT.json")
    plan = read(run_dir / "PLAN.json")
    job = read(run_dir / "JOB.json")
    assert run["status"] == result["status"] == "PASS"
    assert run["returncode"] == 0 and result["timing_started"]
    assert job["backend"] == result["backend"] == "cpu"
    assert job["q_values"] == plan["q_values"] == [1]
    assert job["repeats"] == 2 and len(job["cases"]) == 2
    assert result["historical_GPU_reference_qualification"] == "NOT_ESTABLISHED"
    assert result["full_service_performance_claim"] is False
    historical_runner = root / "matched_cost/retained_protocol_snapshot/run_probe.py"
    for key in ["inputs", "runner", "probe_source", "model", "source_manifest", "binary", "job", "result"]:
        bound = run[key]
        # The wrapper later acquired host-only admission/deadline changes. Its
        # executed bytes were retained, and must not be attributed to the new file.
        path = historical_runner if key == "runner" and historical_runner.exists() else Path(bound["path"])
        actual = identity(path)
        assert all(actual[k] == bound[k] for k in actual), key
    assert run["libraries_before"] == run["libraries_after"]
    modules = {}
    for path, expected in run["libraries_before"].items():
        actual = identity(Path(path))
        assert all(actual[k] == expected[k] for k in actual)
        modules[Path(path).name] = actual
    assert result["native_modules_before"] == result["native_modules_after"] == modules
    assert len(modules) == 4
    for expected in run["frontend_headers"].values():
        actual = identity(Path(expected["path"]))
        assert all(actual[k] == expected[k] for k in actual)
    cache = {}
    records = []
    histories = {case["name"]: len(case["history"]) for case in job["cases"]}
    expected_work = Counter()
    expected_stages = {}
    references = {}
    captures_checked = pairs = 0
    modes = Counter()
    graph_counts = Counter()

    def stage(name, calls, rows):
        expected_work["native_calls"] += calls
        expected_work["target_rows"] += rows
        expected_stages.setdefault(name, Counter()).update({"attempted_calls": calls, "reserved_calls": calls,
                                                           "attempted_rows": rows, "reserved_rows": rows})

    def inspect(record, phase):
        nonlocal captures_checked
        p = histories[record["case"]]
        assert record["q"] == 1 and record["schedule"] == [1]
        work = record["work"]
        assert work["outer_calls"] == work["physical_calls"] == work["target_rows"] == 1
        assert work["physical_widths"] == {"1": 1}
        assert work["graphs_built"] + work["graphs_reused"] == 1
        graph_counts[(phase, work["graphs_built"], work["graphs_reused"])] += 1
        for field, position in [("initial_geometry", p), ("final_geometry", p + 1), ("continuation_geometry", p + 2)]:
            geometry = record[field]
            assert geometry["dense_seq0"] and geometry["head_equals_next_by_native_guard"]
            assert geometry["used"] == geometry["occupied_end"] == position
            assert geometry["n_ctx"] == 1024 and geometry["n_ubatch"] == 32
        assert len(record["executions"]) == 1
        execution = record["executions"][0]
        assert (execution["phase"], execution["position"], execution["width"], execution["requested_rows"]) == ("VERIFY", p, 1, [0])
        for name, descriptor in record["captures"].items():
            path = run_dir / "native" / descriptor["path"]
            data = path.read_bytes()
            assert len(data) == descriptor["bytes"]
            assert hashlib.sha256(data).hexdigest() == descriptor["sha256"]
            cache[descriptor["path"]] = data
            if name in {"operation_vectors", "continuation_vector"}:
                assert len(data) == 512
                assert all(math.isfinite(x[0]) for x in struct.iter_unpack("<f", data))
            captures_checked += 1
        expected_work["contexts"] += 1
        stage(phase + "/prefill", (p + 31) // 32, p)
        stage(phase + "/operation", 1, 1)
        stage(phase + "/continuation", 1, 1)
        if record.get("mode") == "one_shape_warmup_then_reset":
            stage(phase + "/warmup", 1, 1)
            stage(phase + "/reset_prefill", (p + 31) // 32, p)
        records.append(record)

    assert len(result["qualification"]) == 2
    for cell in result["qualification"]:
        assert cell["status"] == "PASS" and cell["candidates"] == [] and cell["q"] == 1
        reference = dict(cell["reference"], case=cell["case"], q=cell["q"])
        references[cell["case"]] = reference
        inspect(reference, "qualification")
    assert len(result["measurements"]) == 8
    seen = set()
    for measurement in result["measurements"]:
        name, mode, repeat = (measurement[k] for k in ["case", "mode", "repeat"])
        assert mode in {"first_after_fresh_context", "one_shape_warmup_then_reset"} and repeat in {0, 1}
        assert (name, mode, repeat) not in seen
        seen.add((name, mode, repeat))
        modes[mode] += 1
        assert measurement["qualified"] and all(measurement["comparison"].values())
        assert math.isfinite(measurement["operation_seconds"]) and measurement["operation_seconds"] > 0
        reference = references[name]
        inspect(measurement, "measurement/" + mode)
        for field in ["initial_geometry", "final_geometry", "continuation_geometry"]:
            assert measurement[field] == reference[field]
        assert measurement["captures"].keys() == reference["captures"].keys()
        for field in measurement["captures"]:
            assert cache[measurement["captures"][field]["path"]] == cache[reference["captures"][field]["path"]]
            pairs += 1
    assert expected_work == Counter({"contexts": 10, "native_calls": 136, "target_rows": 3524})
    assert dict(expected_work) == plan["budget"] == job["budget"]
    work = result["work"]
    assert work["contexts"] == expected_work["contexts"]
    assert work["attempted_native_calls"] == work["reserved_native_calls"] == expected_work["native_calls"]
    assert work["attempted_target_rows"] == work["reserved_target_rows"] == expected_work["target_rows"]
    assert work["by_stage"] == {k: dict(v) for k, v in expected_stages.items()}
    assert {"blobs/" + p.name for p in (run_dir / "native/blobs").iterdir()} == set(cache)
    assert sum(map(len, cache.values())) == result["raw_bytes"] == 3104840
    assert len(cache) == result["raw_unique_blobs"] == 10
    report = {"schema": "heterospec.independent-matched-q1-smoke-audit.v1",
              "status": "PASS_Q1_PROTOCOL_ONLY", "reviewer_native_executions": 0,
              "reviewer_GPU_executions": 0, "capture_references_rehashed": captures_checked,
              "comparison_blob_pairs": pairs, "unique_raw_blobs": len(cache),
              "unique_raw_bytes": sum(map(len, cache.values())),
              "independently_enumerated_work": dict(expected_work),
              "measurement_modes": dict(modes),
              "graph_counters": [{"stage": p, "built": b, "reused": u, "records": count}
                                 for (p, b, u), count in graph_counts.items()],
              "warm_reset_evidence": "Executed bound source enforces reset/replay initial active sequence bytes and native geometry equality before timing; reset export is not separately saved in raw captures.",
              "timing_scope": "Capture-conditioned LOCAL target operation; budget aggregation outside window, original PhaseContext synchronization and full requested vector materialization inside. Both modes rebuilt one graph in these q1 samples, so warm mode is not a steady-state guarantee.",
              "qualification_scope": "q1 reference only; no distinct width candidate. Does not amend or override the independently confirmed full-width q2 failure.",
              "executed_wrapper_snapshot": identity(historical_runner),
              "workspace_scope": "Requires the complete review workspace and its originally bound model/build paths. Use matched_cost/verify_run.py for portable raw-only replay.",
              "performance_claim": False,
              "bindings": {str(p.relative_to(root)): identity(p) for p in [run_dir / "RUN.json", run_dir / "PLAN.json", run_dir / "native/RESULT.json", Path(__file__).resolve()]}}
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "bindings"}, indent=2))


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
