"""Static plan and historical PR86 audit. Never starts or approves inference."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOC = ROOT / "docs/experiments/b570_memory_followup_20261011"
MIB = 1024 ** 2


def require(condition, message):
    if not condition:
        raise ValueError(message)


def integer(value, field):
    require(type(value) is int, field + " must be an integer, not a boolean/string")
    return value


def memory_sample(row, expected_pid):
    """Recompute this historical B570 heap; do not trust logged scalar/gate."""
    require(row.get("event") == "MEMORY", "not a memory sample")
    require(row.get("point") != "UNLOADED", "unloaded memory cannot prove loaded headroom")
    require(row.get("scope") == "OWNED_MODEL_PROCESS", "wrong process scope")
    require(integer(row.get("pid"), "pid") == expected_pid, "PID changed")
    require(expected_pid > 0, "invalid PID")
    require(row.get("timestamp_utc"), "missing timestamp")
    require((row.get("vendor_id"), row.get("device_id"), row.get("device_type"))
            == (0x8086, 0xE20C, 2), "wrong historical B570 device")
    require("B570" in row.get("device_name", ""), "wrong device name")
    for key in ("model_forward_calls", "decode_calls"):
        require(integer(row.get(key), key) == 0, "history was not zero forward")
    heaps = row.get("heaps", [])
    require(heaps, "missing heap samples")
    indices = []
    local = []
    for heap in heaps:
        index = integer(heap.get("index"), "heap index")
        require(index not in indices, "duplicate heap index")
        indices.append(index)
        require(type(heap.get("device_local")) is bool, "invalid heap locality flag")
        physical = integer(heap.get("physical_size_bytes"), "physical size")
        budget = integer(heap.get("budget_bytes"), "budget")
        usage = integer(heap.get("usage_bytes"), "usage")
        require(physical > 0 and 0 <= budget <= physical and usage >= 0,
                "invalid budget/usage")
        if heap["device_local"]:
            require(index == 0 and physical == 10563354624,
                    "not the independently mapped historical dedicated heap")
            local.append(budget - usage)
    require(len(local) == 1, "expected one historical dedicated heap")
    headroom = min(local)
    require(integer(row.get("device_local_headroom_bytes"), "reported headroom")
            == headroom, "signed headroom mismatch; shared heap/unsigned value refused")
    return headroom


def historical_observation(rows):
    samples = [r for r in rows if r.get("event") == "MEMORY"
               and r.get("point") != "UNLOADED"]
    require(samples, "no owned-process memory evidence")
    pid = integer(samples[0].get("pid"), "pid")
    values = [(r, memory_sample(r, pid)) for r in samples]
    loaded = [(r, v) for r, v in values if r.get("point") == "LOADED"]
    require(len(loaded) <= 1, "ambiguous repeated loaded samples")
    sample, headroom = loaded[0] if loaded else values[-1]
    context = [r for r in rows if r.get("event") == "CONTEXT"
               and r.get("role") == "target"]
    require(len(context) == 1, "missing/ambiguous target context")
    final = [r for r in rows if r.get("event") in ("FINAL", "ERROR")]
    negative_observed = any(v < 0 for _, v in values)
    return {
        "pid": pid, "sample_point": sample["point"],
        "sample_timestamp_utc": sample["timestamp_utc"],
        "headroom_bytes": headroom, "headroom_mib": headroom / MIB,
        "negative_budget_observed": negative_observed,
        "complete_dual_context_loaded": bool(loaded),
        "loaded_sample_meets_512_mib": bool(loaded) and not negative_observed
        and headroom >= 512 * MIB,
        "loaded_sample_meets_128_mib_counterfactual": bool(loaded)
        and not negative_observed and headroom >= 128 * MIB,
        "target_outputs_capacity": context[0].get("n_outputs_max"),
        "batched_k3_capacity_certified": False,
        "engineering_peak_measured": False,
        "original_final_or_error": final[-1] if final else None,
        "original_gate_status_unchanged": True,
        "allow_forward": False, "qualified_speedup": None,
    }


def validate_policy(policy, assets):
    require(policy["state"] == "DESIGN_NO_B570_LOAD_OR_FORWARD", "wrong design state")
    require(policy["primary_profile"] == "STANDARD_Q6", "wrong primary profile")
    require(set(policy["profiles"]) == {"STANDARD_Q6", "TIGHT_Q8"}, "profile drift")
    expected = {
        "STANDARD_Q6": ("Llama_target_Q6_K", "Q6_K", 512 * MIB, 12, 510),
        "TIGHT_Q8": ("Llama_target_Q8_0", "Q8_0", 128 * MIB, 6, 360),
    }
    require(policy["candidate_modes"] == ["native_greedy", "vulkan_batched_repair"],
            "mode drift")
    require(policy["candidate_k_max"] == [1, 2, 3], "k drift")
    for name, (target, quant, threshold, candidates, planned) in expected.items():
        p = policy["profiles"][name]
        require(p["target_asset"] == target and assets["models"][target]["quantization"]
                == quant, "cross-precision reference/profile mismatch")
        require(integer(p["dedicated_headroom_min_bytes"], "threshold") == threshold,
                "headroom threshold drift")
        require(p["candidate_limit"] == candidates == len(p["draft_assets"]) * 2 * 3,
                "candidate count drift")
        require(p["planned_engineering_forward_units"] == planned, "forward budget drift")
        require(planned + policy["dedicated_zero_forward_probe_max_per_profile"]
                * policy["dedicated_zero_forward_probe_charge_units"]
                <= policy["engineering_unit_hard_cap_per_profile"], "probe budget overflow")
    require(policy["profiles"]["TIGHT_Q8"]["draft_assets"]
            == ["Llama_draft_Q4_K_M"], "tight draft drift")
    require(policy["profiles"]["STANDARD_Q6"]["draft_assets"]
            == ["Llama_draft_Q8_0", "Llama_draft_Q4_K_M"], "standard draft drift")
    require(policy["confirmation_admission_requires_positive_gain"] is False,
            "positive-only confirmation would censor results")
    require(policy["unrepaired_diagnostic_forward_units_per_profile"] == 25,
            "unrepaired trigger diagnostic omitted")
    require(policy["both_profile_selections_frozen_before_any_confirmation"] is True,
            "held-out task leakage")
    for key in ("cross_precision_reference_reuse", "cross_precision_ratio_pooling",
                "headroom_relaxation_after_forward_allowed",
                "hidden_quantization_or_cpu_offload_allowed", "gpu_execution_performed_by_this_design"):
        require(policy[key] is False, key + " must remain false")
    require(policy["qualified_ratio_on_residency_unknown"] is None,
            "unknown residency cannot qualify GPU result")
    require(policy["formal_retries"] == 0 and policy["date_ci"] is None,
            "retry/date inference drift")
    formal = (policy["confirmation_tasks"] * policy["confirmation_rounds"]
              * policy["confirmation_sessions"] * len(policy["confirmation_arms"]))
    require(formal == policy["formal_requests_per_profile"] == 768, "formal budget mismatch")
    require(formal // 4 == policy["formal_requests_per_arm"] == 192, "arm budget mismatch")
    total = policy["engineering_unit_hard_cap_per_profile"] + formal + policy["formal_warmups_per_profile"]
    require(total == policy["request_and_probe_unit_hard_cap_per_profile"] == 1440,
            "per-profile budget mismatch")
    require(2 * total == policy["total_request_and_probe_unit_hard_cap"] == 2880,
            "total budget mismatch")
    require(2 * policy["owned_gpu_lifetime_hours_per_profile"]
            == policy["total_owned_gpu_lifetime_hours"] == 16, "lifetime budget mismatch")


def run_audit():
    policy = json.loads((DOC / "POLICY.json").read_text())
    assets = json.loads((DOC / "ASSETS.json").read_text())
    bindings = json.loads((DOC / "SOURCE_BINDINGS.json").read_text())
    validate_policy(policy, assets)
    observations = {}
    for item in bindings["copied_historical_logs"]:
        data = (DOC / item["local_path"]).read_bytes()
        require(len(data) == item["bytes"] and hashlib.sha256(data).hexdigest()
                == item["sha256"], "historical log byte/hash mismatch")
        require(hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
                == item["git_blob_sha1"], "historical Git blob mismatch")
        observations[Path(item["local_path"]).name] = historical_observation(
            [json.loads(line) for line in data.splitlines()])
    q6 = json.loads((DOC / "Q6_STATIC_PREFLIGHT.json").read_text())
    target = assets["models"]["Llama_target_Q6_K"]
    require((q6["file"]["size"], q6["file"]["lfs"]["sha256"], q6["revision"])
            == (target["bytes"], target["sha256"], target["revision"]), "Q6 pin mismatch")
    require(q6["model_loads"] == q6["model_forwards"] == 0
            and q6["full_file_sha256_verified"] is False, "static receipt scope changed")
    require(q6["all_tokenizer_components_equal_to_Q8_target"] is True
            and q6["chat_template_equal_to_Q8_target"] is True, "static tokenizer mismatch")
    saving = assets["models"]["Llama_target_Q8_0"]["bytes"] - target["bytes"]
    require(saving == q6["byte_savings_vs_Q8_file"] == 1944764416, "file saving mismatch")
    return {"status": "STATIC_AUDIT_PASS_NO_RUNTIME_APPROVAL", "historical_pr86": observations,
            "q6_file_bytes_saved": saving, "q6_file_gib_saved": saving / 1024 ** 3,
            "allow_forward": False, "gpu_loads_performed": 0, "gpu_forwards_performed": 0,
            "native_followup_worker_implemented": False, "native_followup_worker_compiled": False,
            "full_q6_file_hash_verified": False, "qualified_speedup": None}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(run_audit(), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(result)
    else:
        print(result, end="")
