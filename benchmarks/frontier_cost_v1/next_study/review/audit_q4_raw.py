#!/usr/bin/env python3
"""Independent offline audit of the one completed, frozen CPU diagnostic.

This does not import the experiment's Python verifier or any native module.
It deliberately accepts only a complete panel, not partial failure receipts.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct


COMMIT = "ef2766327e7821fe188d1ad788b2c3b05531eb9a"
ARMS = [
    ("macro_reference", [4, 4], 8, 8, None),
    ("macro_reference_repeat", [4, 4], 8, 8, "macro_reference"),
    ("macro_wide", [8], 8, 8, "macro_reference"),
    ("frontier4_reference", [4], 4, 4, None),
    ("frontier4_wide_trim", [8], 4, 4, "frontier4_reference"),
    ("frontier5_reference_materialize", [4, 1], 4, 5, None),
    ("frontier5_wide_trim", [8], 4, 5, "frontier5_reference_materialize"),
]


def identity(path):
    value = path.read_bytes()
    return {"bytes": len(value), "sha256": hashlib.sha256(value).hexdigest()}


def float_difference(a, b):
    assert len(a) == len(b) == 128 * 4
    x, y = struct.unpack("<128f", a), struct.unpack("<128f", b)
    assert all(math.isfinite(v) for v in x + y)
    return {
        "vocabulary": 128,
        "different_float_bit_patterns": sum(a[i:i + 4] != b[i:i + 4] for i in range(0, len(a), 4)),
        "different_numerical_float_values": sum(u != v for u, v in zip(x, y)),
        "maximum_absolute_difference": max(abs(u - v) for u, v in zip(x, y)),
        "reference_argmax": max(range(128), key=x.__getitem__),
        "wide_argmax": max(range(128), key=y.__getitem__),
        "argmax_equal": max(range(128), key=x.__getitem__) == max(range(128), key=y.__getitem__),
        "is_primary_consumer": False,
    }


def audit(run_dir, preflight_path):
    run = json.loads((run_dir / "RUN.json").read_text())
    native = run_dir / "native"
    result = json.loads((native / "RESULT.json").read_text())
    job = json.loads((run_dir / "JOB.json").read_text())
    prepared = json.loads(preflight_path.read_text())
    assert run["publication"]["commit"] == job["published_source_commit"] == result["published_source_commit"] == COMMIT
    assert run["publication"]["sources"] == job["source_binding"] == result["source_binding"] == prepared["source_files"]
    assert run["build"] == prepared["build_receipt"]
    assert run["binary"] == prepared["binary"]
    assert run["job"] == identity(run_dir / "JOB.json")
    assert run["native_result"] == identity(native / "RESULT.json")
    assert result["job_sha256"] == identity(run_dir / "JOB.json")["sha256"]
    assert run["status"] == "COMPLETE_PENDING_INDEPENDENT_VERIFICATION" and run["returncode"] == 0
    assert run["native_child_launches"] == 1 and run["child_reaped"] and not run["timed_out"]
    assert not run["automatic_retry"] and not run["performance_admitted"]
    assert all(run[k] for k in ("dependencies_unchanged", "sources_unchanged", "model_unchanged"))
    assert set(run["logs"]) == {"stdout.log", "stderr.log"}
    for name, expected in run["logs"].items():
        assert identity(run_dir / name) == expected
    model = {"sha256": "e4b4f329077cc07036a307566f652a35b10e6f41c3b7a98478f2dfca4b09c044", "bytes": 7084832}
    assert run["model"] == model and result["model"] == dict(model, trained=False)
    assert result["model_loads"] == 1 and result["backend"] == "cpu" and result["threads"] == 1
    libraries = prepared["inherited_bindings"]["libraries"]
    assert job["expected_native_libraries"] == libraries
    for when in ("native_modules_before", "native_modules_after"):
        assert {name: desc["sha256"] for name, desc in result[when].items()} == libraries
    for name in ("performance_admitted", "timing_phase", "natural_acceptance_tested", "production_q8_full_mask_qualified"):
        assert result[name] is False
    assert result["historical_R_qualification"] == "NOT_ESTABLISHED"
    assert len(result["runs"]) == 14
    expected_cases = [{"name": f"controlled-p{p}", "history": [(3 + 7 * i) % 128 for i in range(p)],
                       "rows": [(p + 5 + 11 * i) % 128 for i in range(8)], "continuation": 37} for p in (248, 252)]
    assert job["cases"] == expected_cases
    blob_data = {}
    for record in result["runs"]:
        for desc in record["captures"].values():
            key = desc["sha256"]
            assert desc["path"] == f"blobs/{key}.bin"
            path = native / desc["path"]
            assert not path.is_symlink() and identity(path) == {"sha256": key, "bytes": desc["bytes"]}
            blob_data[key] = path.read_bytes()
    assert {p.name for p in (native / "blobs").iterdir()} == {key + ".bin" for key in blob_data}
    assert sum(map(len, blob_data.values())) == result["raw_bytes"] == 7385976
    checks = []
    fifth = []
    stages = {}
    calls_total = rows_total = trims_total = generated_vectors = 0
    index = 0
    for case in expected_cases:
        p = len(case["history"])
        refs = {}
        common_initial = None
        for name, schedule, shared, frontier, reference in ARMS:
            record = result["runs"][index]
            index += 1
            assert (record["case"], record["arm"], record["schedule"], record["shared_rows"], record["frontier"], record["base"]) == (case["name"], name, schedule, shared, frontier, p)
            assert record["reference"] == (reference or "")
            assert record["checkpoint"] == "CONTINUATION_CAPTURED"
            capture = {key: blob_data[desc["sha256"]] for key, desc in record["captures"].items()}
            if common_initial is None:
                common_initial = capture["initial_state"]
            assert capture["initial_state"] == common_initial
            full = capture["all_operation_vectors"]
            assert len(full) == sum(schedule) * 128 * 4
            assert capture["shared_operation_vectors"] == full[:shared * 128 * 4]
            assert all(math.isfinite(v[0]) for v in struct.iter_unpack("<f", capture["shared_operation_vectors"]))
            assert len(capture["continuation_vector"]) == 128 * 4
            assert all(math.isfinite(v[0]) for v in struct.iter_unpack("<f", capture["continuation_vector"]))
            assert record["all_operation_vectors_finite_diagnostic"] == all(math.isfinite(v[0]) for v in struct.iter_unpack("<f", full))
            generated_vectors += sum(schedule) + 1
            for field, end in (("initial_geometry", p), ("untrimmed_geometry", p + sum(schedule)),
                               ("final_geometry", p + frontier), ("continuation_geometry", p + frontier + 1)):
                expected = {"used": end, "occupied_end": end, "extent": ((end + 255) // 256) * 256,
                            "next_q1_extents": [((end + 1 + 255) // 256) * 256], "dense_seq0": True,
                            "head_equals_next_by_native_guard": True, "n_ubatch": 32, "n_ctx": 1024}
                assert record[field] == expected
            trim = int(sum(schedule) > frontier)
            assert record["trim_calls"] == trim
            trims_total += trim
            assert set(record["counts"]) == {"prefill", "operation", "continuation"}
            prefix_widths = [32] * (p // 32) + ([p % 32] if p % 32 else [])
            for stage, widths in (("prefill", prefix_widths), ("operation", schedule), ("continuation", [1])):
                count = record["counts"][stage]
                nc, nr = len(widths), sum(widths)
                assert count["total_native_calls"] == count["physical_calls"] == nc
                assert count["total_target_rows"] == nr
                assert count["outer_calls"] + count["prefill_calls"] == nc
                assert count["target_rows"] + count["prefill_rows"] == nr
                histogram = {str(width): widths.count(width) for width in set(widths)}
                assert count["physical_widths"] == histogram
                assert (count["prefill_calls"], count["prefill_rows"]) == ((nc, nr) if stage == "prefill" else (0, 0))
                stages[f"{case['name']}/{name}/{stage}"] = {"reserved_calls": nc, "attempted_calls": nc, "reserved_rows": nr, "attempted_rows": nr}
                calls_total += nc
                rows_total += nr
            if reference:
                old_record, old_capture = refs[reference]
                verdict = {key: capture[key] == old_capture[key] for key in ("initial_state", "shared_operation_vectors", "final_state", "continuation_vector", "continuation_state")}
                verdict.update({key: record[key] == old_record[key] for key in ("initial_geometry", "final_geometry", "continuation_geometry")})
                assert all(verdict.values())
                assert record["checks"] == verdict and record["status"] == "PASS"
                checks.append({"history_length": p, "arm": name, "reference": reference, "shared_operation_rows": shared, "raw_comparisons": verdict})
                if frontier == 5:
                    assert record["fifth_vector_is_primary_contract"] is False
                    assert capture["fifth_vector_diagnostic"] == full[4 * 128 * 4:5 * 128 * 4]
                    difference = float_difference(old_capture["fifth_vector_diagnostic"], capture["fifth_vector_diagnostic"])
                    assert record["fifth_vector_diagnostic_equal"] == (difference["different_float_bit_patterns"] == 0)
                    fifth.append({"history_length": p, **difference})
            else:
                assert record["status"] == "REFERENCE_CAPTURED" and record["checks"] == {}
                refs[name] = (record, capture)
    assert result["work"] == {"contexts": 14, "reserved_native_calls": calls_total, "attempted_native_calls": calls_total,
                               "reserved_target_rows": rows_total, "attempted_target_rows": rows_total, "by_stage": stages}
    assert (calls_total, rows_total, trims_total) == (146, 3612, 4)
    assert result["trim_calls"] == trims_total
    assert result["status"] == "DIAGNOSTIC_PASS"
    return {
        "schema": "heterospec.independent-q4-raw-review.v1", "status": "PASS_FOR_FROZEN_PRIMARY_CONSUMER_CONTRACTS",
        "publication_commit": COMMIT, "native_result": identity(native / "RESULT.json"),
        "run_receipt": identity(run_dir / "RUN.json"), "job": identity(run_dir / "JOB.json"),
        "independent_method": "Read every raw blob and recompute comparisons and expected per-stage physical/API work without importing the experiment verifier or running native code.",
        "unique_blobs_verified": len(blob_data), "raw_bytes_verified": sum(map(len, blob_data.values())),
        "contexts": 14, "decode_api_calls": calls_total, "physical_calls": calls_total, "target_rows": rows_total,
        "trim_calls": trims_total, "model_loads": result["model_loads"], "native_child_launches": run["native_child_launches"],
        "completed_reference_captures": 6, "completed_comparisons": len(checks), "primary_comparison_fields": 8 * len(checks),
        "captured_operation_and_continuation_vectors": generated_vectors,
        "comparisons": checks, "fifth_vector_diagnostics": fifth,
        "meaning": "q8 and q4+q4 agree on all eight operation vectors in the macro tests. At frontier5, the first four consumer vectors, materialized active-state bytes, geometry and common forced continuation agree, while the fifth output is unequal in both histories. Thus full-output interchangeability does not follow from the primary pass.",
        "claims_not_established": prepared["claims_not_established"], "performance_admitted": False,
        "reviewer_native_execution_count": 0,
    }


def main():
    parser = argparse.ArgumentParser()
    here = Path(__file__).resolve().parent
    parser.add_argument("--run", type=Path, default=here.parent / "q4_frontier/run_cpu_01")
    parser.add_argument("--preflight", type=Path, default=here / "q4_preexecution_review.json")
    parser.add_argument("--out", type=Path, default=here / "q4_evidence_review.json")
    args = parser.parse_args()
    result = audit(args.run, args.preflight)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in ("status", "unique_blobs_verified", "contexts", "decode_api_calls", "target_rows", "fifth_vector_diagnostics")}, indent=2))


if __name__ == "__main__":
    main()
