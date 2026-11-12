"""Create the 22-case prospective admission matrix without native execution."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "upstream221/benchmarks/frontier_cost_v1/next_study/guard_audit/PACKED_QUALIFICATION_DESIGN.json"


def main():
    raw = UPSTREAM.read_bytes()
    old = json.loads(raw)
    cases = []
    widths = {"P01": 4, "P02": 5, "P03": 7, "P04": 8, "P05": 9, "P06": 11,
              "P07": 12, "P08": 31, "P09": 32, "P10": 8, "P11": 8}
    for item in old["positive_cases"]:
        q = widths[item["id"]]
        case = {"id": item["id"], "original_purpose": item["purpose"], "frozen_q": q, "arms": {}}
        for arm in ("A", "B", "C"):
            supported = arm != "C" or q == 8
            decision = "EXACT_FULL_OUTPUT_STATE_PASS" if supported else "REJECT_PREEXEC_C_DOMAIN"
            route = "old-four-column-and-tail MMVQ" if arm == "A" or q < 8 else (
                "generic MMVQ with ncols=4,channels=q//4 plus old tail" if arm == "B" else "pair4 MMVQ with ncols=4,g=2 inside CTA")
            case["arms"][arm] = {"expected_decision": decision, "expected_route": route if supported else "NO_NATIVE_WORK",
                                 "native_result": "NOT_RUN", "numerical_result": "NOT_RUN", "clean_guard_result": "NOT_RUN"}
        if item["id"] == "P10":
            case["extra_obligation"] = "Same actual q=8 input on each side of the native padding boundary; full target/draft untrimmed and committed states and geometry; same request contract."
        elif item["id"] == "P11":
            case["extra_obligation"] = "Verified q=8 macro with earlier accepted frontier, all owned requested vectors including L4, pretrim state, trim/pending/correction and real continuation."
        cases.append(case)
    expected = {"N01": ("REJECT_PREEXEC_WIDTH", "q=0 and q=33; no implicit wide fallback"),
                "N02": ("REJECT_PREEXEC_STRIDE", "noncontiguous activation"),
                "N03": ("REJECT_PREEXEC_WEIGHT_RECIPE", "noncontiguous weight and batched weight tested separately"),
                "N04": ("REJECT_PREEXEC_PADDING_RECIPE", "safe metadata-only padding-clear conflict; do not execute unsafe views"),
                "N05": ("REJECT_PREEXEC_PLACEMENT", "actual CPU/foreign CUDA buffer; no fabricated pointers"),
                "N06": ("REJECT_PREEXEC_BACKEND", "bound device must be NVIDIA SM120 warp32; metadata test only"),
                "N07": ("REJECT_PREEXEC_ARITHMETIC_RECIPE", "precision, IDs, fusion and activation dtype each separate subcase"),
                "N08": ("REJECT_PREEXEC_INTEGER_SPAN", "checked int32 strides/offsets; no large allocation"),
                "N09": ("REBUILD_THEN_EXACT_PASS", "prefix vector, active/layout policy, head placement, output count, topology or recipe change must rebuild; refresh current mask"),
                "N10": ("OWNER_INVALID_AFTER_NATIVE_FAILURE", "failure after at least one native operator: no success, same-owner retry/reset/continuation"),
                "N11": ("OWNER_INVALID_AFTER_TRANSACTION_FAILURE", "trim/draft/sample/reset-postcheck failure invalidates new wrapper owner; old CLI remains terminate-only")}
    for item in old["negative_and_failure_cases"]:
        decision, detail = expected[item["id"]]
        cases.append({"id": item["id"], "original_change": item["change"], "frozen_detail": detail,
                      "arms": {arm: {"expected_decision": decision, "native_result": "NOT_RUN",
                                     "numerical_result": "NOT_RUN", "clean_guard_result": "NOT_RUN"}
                               for arm in ("A", "B", "C")}})
    matrix = {"schema": "heterospec.rtx-round1.qualification-cases.v1", "status": "PROSPECTIVE_FROZEN_EXPECTATIONS",
              "upstream_head": "af436df989570ad882db65bd8a4b265b9e8cfdae", "upstream_design_sha256": hashlib.sha256(raw).hexdigest(),
              "arms": {"A": "backend-loop4", "B": "current packed", "C": "same-CTA two independent four-column groups"},
              "interpretation": "The new host admission policy is stricter than historical packed source. Expectations are not native observations or retroactive baseline qualifications.",
              "fallback_policy": "No automatic fallback. Only separately frozen native-qualified fallback receipts admitted by allowlist; allowlist currently empty.",
              "required_layers": ["source identity", "operator own-path bytes", "A/B/C full-output and activation bytes", "untrimmed and committed target/draft state",
                                  "geometry", "real request output ownership/consumer chain", "always-on clean guard and dispatch", "matched complete service cost"],
              "cases": cases, "model_requests": 0, "native_runs": 0, "gpu_runs": 0}
    out = ROOT / "qualification/CASES.json"
    with out.open("x", encoding="utf8") as f:
        json.dump(matrix, f, indent=2)
        f.write("\n")
    with (ROOT / "qualification/FALLBACK_ALLOWLIST.json").open("x", encoding="utf8") as f:
        json.dump({}, f)
        f.write("\n")


if __name__ == "__main__":
    main()
