"""Same-request host critical-path accounting; no model or GPU calls.

Nested spans are charged exclusively to the innermost stage. Crossing spans
are refused, not summed. CUDA events use a different clock and must remain a
separate operator diagnostic; they cannot be mixed into this wall timeline.
"""
from __future__ import annotations
from collections import defaultdict
import hashlib
import json


class CostError(ValueError):
    pass


ALLOWED = {"reset", "prefill_target", "prefill_draft", "draft", "verify", "sync",
           "planning", "guard", "reconciliation", "fallback", "sampling", "teardown"}


def decompose(record):
    def need(ok, text):
        if not ok:
            raise CostError(text)
    for key in ("request_id", "arm", "source_sha256", "input_sha256", "clock", "service", "spans"):
        need(key in record, "missing identity/timeline field: " + key)
    need(record["clock"] == "steady_clock_ns", "foreign or mixed timestamp clock")
    lo, hi = record["service"]
    need(isinstance(lo, int) and isinstance(hi, int) and hi > lo, "invalid service interval")
    spans = record["spans"]
    need(all(isinstance(s, dict) for s in spans), "invalid span")
    for s in spans:
        need(s.get("category") in ALLOWED, "unknown stage")
        need(s.get("clock", "steady_clock_ns") == record["clock"], "mixed clock")
        need(s.get("lane", "host_critical") == "host_critical", "asynchronous lane in service partition")
        need(all(isinstance(s.get(k), int) for k in ("begin", "end")), "noninteger timestamp")
        need(lo <= s["begin"] < s["end"] <= hi, "span outside service interval")
    for i, a in enumerate(spans):
        for b in spans[i + 1:]:
            overlap = max(a["begin"], b["begin"]) < min(a["end"], b["end"])
            contains = ((a["begin"] <= b["begin"] and b["end"] <= a["end"]) or
                        (b["begin"] <= a["begin"] and a["end"] <= b["end"]))
            need(not overlap or contains, "crossing overlapping spans cannot form exclusive cost stack")
            need(not (a["begin"] == b["begin"] and a["end"] == b["end"]), "ambiguous identical spans")
    edges = sorted({lo, hi} | {s[k] for s in spans for k in ("begin", "end")})
    exclusive = defaultdict(int)
    for a, b in zip(edges, edges[1:]):
        active = [s for s in spans if s["begin"] <= a and b <= s["end"]]
        category = (min(active, key=lambda s: s["end"] - s["begin"])["category"]
                    if active else "unattributed")
        exclusive[category] += b - a
    need(sum(exclusive.values()) == hi - lo, "partition accounting failure")
    return {"request_id": record["request_id"], "arm": record["arm"],
            "source_sha256": record["source_sha256"], "input_sha256": record["input_sha256"],
            "service_ns": hi - lo, "exclusive_ns": dict(sorted(exclusive.items())),
            "overlap_policy": "innermost nested host span; crossing spans rejected",
            "complete_endpoint_self_declared": record.get("complete_endpoint", False),
            "endpoint_qualification": "UNVERIFIED",
            "observed_categories": sorted({s["category"] for s in spans})}


def _endpoint_check(result, admission):
    """Admission is supplied by an independent frozen source/endpoint audit.

    This module cannot manufacture that audit from a caller Boolean or its
    own timeline. Merely supplying a JSON file is not independent verification;
    its bytes/identity and authority must be frozen by the external launcher.
    """
    if not isinstance(admission, dict) or admission.get("status") != "INDEPENDENT_ENDPOINT_AUDIT_PASSED":
        raise CostError("independent endpoint proof required")
    if admission.get("source_sha256") != result["source_sha256"]:
        raise CostError("endpoint proof source differs")
    if admission.get("request_id") != result["request_id"] or admission.get("input_sha256") != result["input_sha256"]:
        raise CostError("endpoint proof request/input differs")
    definition = admission.get("definition")
    if not isinstance(definition, dict):
        raise CostError("frozen endpoint definition missing")
    raw = json.dumps(definition, sort_keys=True, separators=(",", ":")).encode()
    if hashlib.sha256(raw).hexdigest() != admission.get("definition_sha256"):
        raise CostError("frozen endpoint definition hash mismatch")
    required = set(definition.get("required_categories", []))
    if not {"reset", "guard"}.issubset(required):
        raise CostError("endpoint definition must require reset and guard coverage")
    if definition.get("start") != "before_reset_and_per_request_admission" or definition.get("end") != "after_sync_reconciliation_and_response_ready":
        raise CostError("incomplete frozen endpoint boundaries")
    observed = set(result["observed_categories"])
    certificates = admission.get("zero_work_certificates", {})
    for category in required - observed:
        certificate = certificates.get(category)
        if not isinstance(certificate, dict) or certificate.get("status") != "INDEPENDENT_ZERO_WORK_AUDIT_PASSED":
            raise CostError("missing endpoint stage coverage: " + category)
        if certificate.get("request_id") != result["request_id"] or certificate.get("source_sha256") != result["source_sha256"]:
            raise CostError("zero-work stage certificate identity mismatch")
        h = certificate.get("receipt_sha256", "")
        if len(h) != 64 or any(c not in "0123456789abcdef" for c in h):
            raise CostError("zero-work stage receipt missing")


def paired_service(a, b, endpoint_admissions=None):
    if a["request_id"] != b["request_id"] or a["input_sha256"] != b["input_sha256"]:
        raise CostError("cannot pair different requests/inputs")
    if not isinstance(endpoint_admissions, dict):
        raise CostError("independent endpoint proof required; caller complete_endpoint flag is insufficient")
    for result in (a, b):
        key = (result["request_id"], result["arm"], result["source_sha256"])
        _endpoint_check(result, endpoint_admissions.get(key))
    return {"request_id": a["request_id"], "control": a["arm"], "candidate": b["arm"],
            "ratio_of_service": b["service_ns"] / a["service_ns"],
            "reduction": 1 - b["service_ns"] / a["service_ns"]}
