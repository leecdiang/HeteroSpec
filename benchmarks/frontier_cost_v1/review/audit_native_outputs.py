"""Independent offline audit of native CPU integration receipts and captured bytes.

Does not import the implementation comparator or run/load a native model.
Usage: python audit_native_outputs.py CONTINUATION_ROOT NEW_REPORT_PATH
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


def bound(path, expected):
    actual = identity(path)
    assert all(actual[k] == expected[k] for k in actual), str(path)
    return actual


def main(root, out):
    assert not out.exists(), "fresh independent report required"
    native = root / "native_integration"
    run = native / "run_final_01"
    build_dir = native / "build_final_01"
    front = root / "work_cpu_01/frontend/candidate_frontend"
    lib = root / "work_cpu_01/numerical_build/bin"
    build = read(build_dir / "BUILD.json")
    plan = read(run / "PLAN.json")
    summary = read(run / "RUN_SUMMARY.json")
    fixture = read(native / "fixture_01/FIXTURE.json")
    bound(build_dir / "BUILD.json", plan["build_receipt"])
    bound(native / "fixture_01/FIXTURE.json", plan["fixture_receipt"])
    bound(native / "run_integration.py", plan["run_script"])
    assert build["harness"] == build["harness_after"]
    bound(native / "cpu_request_driver.cpp", build["harness"])
    assert build["libraries_before"] == build["libraries_after"]
    assert summary["libraries_before"] == summary["libraries_after"]
    for name, expected in build["frontend"].items():
        bound(front / name, expected)
    for name, expected in build["outputs"].items():
        bound(build_dir / name, expected)
    wanted_modules = {}
    for name, expected in build["libraries_before"].items():
        bound(lib / name, expected)
        bound(lib / name, summary["libraries_before"][name])
        wanted_modules[(lib / name).resolve().name] = expected["sha256"]
    for model in fixture["models"]:
        bound(native / "fixture_01" / model["name"], model)
    assert fixture["generator_sha256"] == identity(native / "make_integration_fixture.py")["sha256"]
    assert summary["status"] == "EXECUTED_PENDING_OFFLINE_COMPARISON"
    assert len(summary["records"]) == 9
    assert summary["model_requests"] == 64 and summary["GPU_requests"] == 0
    for i, record in enumerate(summary["records"]):
        assert not record["timed_out"] and record["returncode"] == (2 if i == 0 else 0)
        bound(run / (record["name"] + ".stdout"), record["stdout"])
        bound(run / (record["name"] + ".stderr"), record["stderr"])
    assert read(run / "guarded_gpu_required/failure.json") == {"error": "GPU required"}
    entry = (front / "entry.cpp").read_text()
    assert entry.index('need(gpu,"GPU required")') < entry.index("llama_model_load_from_file")

    # The only receipt fields allowed to differ have explicit independent checks
    # below, or are instrumented wall-clock measurements that are not interpreted.
    time_fields = {"request_seconds", "service_seconds", "setup_seconds", "teardown_seconds",
                   "target_phases", "draft_phases"}
    policy_fields = {"draft_tail_policy", "draft_tail_recovered", "draft_tail_skipped", "draft_calls",
                     "draft_physical_width_hist", "graphs_built", "graphs_reused"}
    totals = Counter()
    coverage = Counter()
    requests = []
    byte_manifest = hashlib.sha256()
    for cell in plan["matrix"]:
        k = cell["k"]
        job = read(run / cell["job"])
        assert cell["request_count"] == len(job["inputs"]) == 8
        assert job["k"] == k and job["synthetic_fixture"] is True
        for role in ["target", "draft"]:
            assert identity(Path(job[role + "_model"]))["sha256"] == job[role + "_model_sha256"]
        results = []
        for mode in [0, 1]:
            result = read(run / (cell["name"] + f"_mode{mode}") / "RESULT.json")
            results.append(result)
            assert result["status"] == "COMPLETE" and result["normal_cleanup_returned"]
            assert result["GPU_qualification"] == "NOT_RUN" and result["performance_claim"] is False
            assert result["eog_ids"] == [127]
            assert result["actual_context"] == {"target_ubatch": 32, "draft_ubatch": 4,
                                                 "target_n_ctx": 1024, "draft_n_ctx": 1024,
                                                 "target_output_reserve": 8}
            assert result["numerical_modules_before"] == result["numerical_modules_after"]
            modules = result["numerical_modules_before"]
            assert {m["name"]: m["sha256"] for m in modules} == wanted_modules
            assert len(modules) == 4
            for module in modules:
                assert Path(module["path"]).parent.resolve() == lib.resolve()
                assert identity(Path(module["path"]))["sha256"] == module["sha256"]
            assert [r["name"] for r in result["requests"]] == [r["name"] for r in job["inputs"]]
        for index, request in enumerate(job["inputs"]):
            name = request["name"]
            dirs = [run / (cell["name"] + f"_mode{mode}") / name for mode in [0, 1]]
            eager, lazy = [read(d / "RECEIPT.json") for d in dirs]
            audits = [read(d / "AUDIT.json") for d in dirs]
            assert audits[0] == audits[1], (cell["name"], name, "event stream")
            audit = audits[0]
            assert eager.keys() == lazy.keys()
            for key in eager.keys() - time_fields - policy_fields:
                assert eager[key] == lazy[key], (name, key)
            assert eager["draft_tail_policy"] == "eager-control"
            assert lazy["draft_tail_policy"] == "deferred-last-q1"
            assert eager["draft_tail_recovered"] == eager["draft_tail_skipped"] == 0
            cycles = lazy["cycles"]
            skips = sum(c["accepted"] < k for c in cycles)
            recoveries = len(cycles) - skips
            assert lazy["draft_tail_skipped"] == skips and lazy["draft_tail_recovered"] == recoveries
            assert eager["draft_calls"] - lazy["draft_calls"] == skips
            assert (Counter(eager["draft_physical_width_hist"]) - Counter(lazy["draft_physical_width_hist"])) == (+Counter({"1": skips}))
            assert not (Counter(lazy["draft_physical_width_hist"]) - Counter(eager["draft_physical_width_hist"]))
            for receipt in [eager, lazy]:
                assert receipt["graphs_built"] + receipt["graphs_reused"] == sum(receipt["target_physical_width_hist"].values()) + sum(receipt["draft_physical_width_hist"].values())
            assert all({p.name for p in (d / "audit").iterdir()} == {e["file"] for e in audit} for d in dirs)
            assert len({e["file"] for e in audit}) == len(audit)
            vectors = {"target": [], "draft": []}
            local_bytes = 0
            for event in audit:
                left, right = [(d / "audit" / event["file"]).read_bytes() for d in dirs]
                assert left == right, (name, event["file"])
                local_bytes += len(left)
                byte_manifest.update((cell["name"] + "/" + name + "/" + event["file"] + ":" + hashlib.sha256(left).hexdigest() + "\n").encode())
                if event["kind"] == "requested-logits":
                    assert len(left) == event["vocab"] * 4 == 512
                    values = [v[0] for v in struct.iter_unpack("<f", left)]
                    assert all(math.isfinite(v) for v in values)
                    vectors[event["role"]].append(max(range(len(values)), key=values.__getitem__))
                    totals["full_vector_pairs"] += 1
                else:
                    assert len(left) == event["bytes"]
                    geometry = event["geometry"]
                    assert geometry["dense"] and geometry["native_append_head_guard_passed"]
                    assert geometry["used"] == geometry["used_max_p1"]
                    assert geometry["position_max"] == geometry["used"] - 1
                    assert geometry["position_min"] == (0 if geometry["used"] else -1)
                    totals["active_sequence_pairs"] += 1
            assert len(vectors["target"]) == 1 + (k + 1) * len(cycles)
            assert len(vectors["draft"]) == k * len(cycles)
            prompt = request["input"]["prompt_ids"]
            cap = request["input"]["cap"]
            assert lazy["prompt_ids"] == prompt and lazy["prompt_tokens"] == len(prompt)
            output = [vectors["target"][0]]
            pending = output[-1]
            base = len(prompt)
            done = pending == 127 or len(output) == cap
            expected_events = [("target", "reset", 0), ("draft", "reset", 0),
                               ("target", "requested-logits", (len(prompt) - 1) % 32)]
            for i, cycle in enumerate(cycles):
                assert not done
                assert cycle["cycle"] == i and cycle["base"] == base and cycle["seed"] == pending
                proposals = vectors["draft"][i * k:(i + 1) * k]
                decisions = vectors["target"][1 + i * (k + 1):1 + (i + 1) * (k + 1)]
                assert cycle["proposals"] == proposals and cycle["decisions"] == decisions
                accepted = 0
                rejected = False
                for proposal, decision in zip(proposals, decisions):
                    if done:
                        break
                    if proposal == decision:
                        output.append(proposal)
                        accepted += 1
                        kind = "accepted"
                    else:
                        output.append(decision)
                        pending = decision
                        rejected = True
                        kind = "correction"
                    done = output[-1] == 127 or len(output) == cap
                    if rejected:
                        break
                if accepted == k and not done:
                    pending = decisions[k]
                    output.append(pending)
                    kind = "bonus"
                    done = pending == 127 or len(output) == cap
                keep = base + 1 + accepted
                for role in ["target", "draft"]:
                    assert cycle[role + "_before"] == {"min": 0, "max": base - 1}
                    assert cycle[role + "_after"] == {"min": 0, "max": keep - 1}
                assert (cycle["accepted"], cycle["rejected"], cycle["commit_kind"], cycle["done"], cycle["keep"], cycle["output_length"], cycle["pending_after"]) == (accepted, rejected, kind, done, keep, len(output), None if done else pending)
                expected_events += [("draft", "trim", base)]
                expected_events += [("draft", "requested-logits", -1)] * k
                expected_events += [("target", "requested-logits", row) for row in range(k + 1)]
                expected_events += [("target", "trim", keep), ("draft", "trim", keep)]
                coverage["correction"] += int(rejected)
                if done and kind == "accepted":
                    coverage["terminal_all_accepted" if accepted == k else "terminal_partial_accepted"] += 1
                if done and kind == "bonus":
                    coverage["terminal_bonus"] += 1
                base = keep
            assert done and lazy["ids"] == output and lazy["length"] == len(output)
            assert lazy["terminal_id"] == output[-1]
            assert lazy["eog"] == [token == 127 for token in output]
            stop = "EOG" if output[-1] == 127 else "CAP"
            assert lazy["stop_reason"] == stop
            expected_events += [("target", "terminal", base), ("draft", "terminal", base)]
            assert len(audit) == len(expected_events)
            for event, (role, kind, position) in zip(audit, expected_events):
                assert (event["role"], event["kind"]) == (role, kind)
                if kind == "requested-logits":
                    assert event["row"] == position
                else:
                    assert event["geometry"]["used"] == position
                    if kind == "trim":
                        assert event["details"] == {"p0": position, "p1": -1, "sequence": 0}
            for role in ["target", "draft"]:
                assert lazy[role + "_final_kv"] == {"min": 0, "max": base - 1}
            coverage[stop] += 1
            coverage["dirty_resident_resets"] += int(index > 0)
            if not cycles:
                coverage["initial_" + stop] += 1
            coverage["crossing_extent_256"] += int(any(256 in e["expected_extents"] and len(set(e["expected_extents"])) > 1 for e in lazy["phase_executions"]))
            totals.update({"request_pairs": 1, "compared_bytes_per_side": local_bytes,
                           "tail_skips": skips, "tail_recoveries": recoveries})
            requests.append({"cell": cell["name"], "request": name, "cycles": len(cycles),
                             "bytes_per_side": local_bytes,
                             "audit": identity(dirs[0] / "AUDIT.json"),
                             "eager_receipt": identity(dirs[0] / "RECEIPT.json"),
                             "deferred_receipt": identity(dirs[1] / "RECEIPT.json")})
    report = {"schema": "heterospec.independent-native-offline-audit.v1",
              "status": "PASS_SAVED_BYTES_AND_RECOMPUTED_LOGIC",
              "reviewer_native_executions": 0, "reviewer_GPU_executions": 0,
              "totals": dict(totals), "coverage": dict(coverage),
              "capture_manifest_sha256": byte_manifest.hexdigest(),
              "checks": ["All referenced raw pairs and exact directory membership",
                         "No event filtering; literal reset/read/trim/terminal sequence",
                         "All 128-float vectors finite, exact, and argmax recomputed",
                         "CAP/EOG, correction, bonus, accepted count and keep reconstructed",
                         "All active native sequence bytes plus dense/head/extent geometry",
                         "Complete logical receipt equality; graph counts and omitted q1 accounted",
                         "Build source, binaries, fixtures, run logs and actual modules bound",
                         "Original CLI GPU rejection precedes model loading"],
              "scope": "Synthetic F32 CPU fixtures; active native sequence and checked allocator geometry, not byte equality of inactive storage or all hidden backend state; instrumented timings have no performance interpretation.",
              "bindings": {str(p.relative_to(root)): identity(p) for p in [build_dir / "BUILD.json", run / "PLAN.json", run / "RUN_SUMMARY.json", native / "COMPARISON_FINAL_01.json", native / "cpu_request_driver.cpp", Path(__file__).resolve()]},
              "requests": requests}
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in {"requests", "bindings", "checks"}}, indent=2))


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
