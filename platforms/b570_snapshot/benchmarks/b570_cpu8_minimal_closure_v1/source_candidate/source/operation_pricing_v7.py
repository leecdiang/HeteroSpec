"""Conservative per-operation charge based on bounded total starts, not Job peak.

No JSON flag is proof that an external service is bounded. The provider's actual
hard boundary and lifetime evidence must be authenticated before native launch.
"""
from pathlib import Path
import re


def need(v, message):
    if not v:
        raise ValueError(message)


def number(x, name, minimum=0):
    need(type(x) is int and x >= minimum, name + " nonnegative integer")
    return x


def envelope(op):
    d = op.get("prospective_envelope")
    need(type(d) is dict and d.get("schema") == "B570_OWNED_ENVELOPE_V1",
         "prospective envelope missing")
    need(d.get("provider_bound_status") == "BOUNDARY_EVIDENCE_REQUIRED",
         "provider bound status must remain explicitly conditional in source plan")
    # Native admission requires an independent verified provider proof; source
    # code alone must never turn a plan into B ENTRY_ADMITTED.
    owned = number(d.get("owned_job_starts_limit"), "owned Job starts", 1)
    outside = number(d.get("owned_outer_starts_limit"), "owned outer starts", 1)
    remote = number(d.get("provider_lifetime_reserve_seconds"), "provider reserve", 1)
    seconds = number(op.get("seconds"), "operation timeout", 1)
    grace = number(op.get("cleanup_seconds"), "cleanup deadline", 1)
    need(owned >= number(op.get("max_job_processes"), "Job concurrent limit", 1),
         "Job cumulative starts smaller than active limit")
    need(number(op.get("starts_bound"), "starts upper") == owned + outside,
         "complete owned starts bound")
    expected = (owned + outside) * (seconds + grace) + remote
    need(number(op.get("lifetime_bound_seconds"), "operation upper") == expected,
         "full operation prospective cost")
    need(type(d.get("provider_proof_sha256")) is str
         and re.fullmatch(r"[0-9a-f]{64}", d["provider_proof_sha256"]) is not None,
         "unverified provider proof identity")
    return {"owned_job_starts_limit": owned, "owned_outer_starts_limit": outside,
            "provider_lifetime_reserve_seconds": remote, "max_process_seconds": expected,
            "provider_proof_sha256": d["provider_proof_sha256"],
            "status": "CONDITIONAL_QUOTE_NOT_BOUNDARY_PROOF"}
