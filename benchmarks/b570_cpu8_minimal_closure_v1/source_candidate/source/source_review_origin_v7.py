"""Narrow A-review provider capture binding, outside the candidate-owned root.

Authenticates consistency of the tool export and platform-owned capture index.
A human/platform must still verify the reviewer/provider's independent authority.
"""
import hashlib
import json
from pathlib import Path
from datetime import datetime


def need(ok, why):
    if not ok:
        raise ValueError(why)


def load(p):
    return json.loads(Path(p).read_bytes())


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def check(root, approval, source_review):
    root = Path(root).resolve()
    campaign = load(root / "CAMPAIGN.json")
    outside = Path(campaign["external_root"]).resolve()
    need(outside != root and root not in outside.parents and outside not in root.parents,
         "review capture must be outside candidate")
    provider = outside / "source-review" / "A01-provider.json"
    index = outside / "source-review" / "A01-index.json"
    for p in (provider, index):
        for ancestor in [p, *p.parents]:
            need(not ancestor.is_symlink() and not ancestor.is_junction(),
                 "review provider capture alias")
        need(p.is_file() and p.stat().st_nlink == 1, "review provider capture missing")
    raw = load(provider)
    anchor = load(index)
    need(anchor.get("sha256") == sha(provider)
         and anchor.get("bytes") == provider.stat().st_size
         and anchor.get("capture_meta") == raw.get("capture_meta")
         and approval.get("provider_capture_sha256") == sha(provider),
         "A review outside capture index mismatch")
    meta = raw.get("capture_meta", {})
    need(meta.get("callId") and meta.get("itemId"), "review actual tool capture metadata")
    request, response = raw.get("request"), raw.get("response")
    need(type(request) is dict and type(response) is dict, "review provider request/response")
    need(request.get("repository_full_name") == "leecdiang/HeteroSpec"
         and request.get("candidate_commit") == source_review["candidate_commit"]
         and request.get("scope") == "FULL_P0_P2_SOURCE_REVIEW",
         "A actual provider review request")
    need(response.get("report_sha256") == source_review["report_sha256"]
         and response.get("candidate_manifest_sha256") == source_review["candidate_manifest_sha256"]
         and response.get("reviewer_identity") == approval.get("independent_reviewer_identity")
         and response.get("review_url") == approval.get("external_provider_reference")
         and response.get("status") == "COMPLETED",
         "A actual provider response not bound")
    t1 = datetime.fromisoformat(raw["registered_utc"].replace("Z", "+00:00"))
    t2 = datetime.fromisoformat(raw["observed_utc"].replace("Z", "+00:00"))
    need(t1.tzinfo is not None and t2.tzinfo is not None and t1 <= t2,
         "A source review captured interval")
    need(isinstance(campaign.get("candidate_author"), str) and campaign["candidate_author"],
         "A source author identity required")
    need(response["reviewer_identity"] != campaign["candidate_author"],
         "A reviewer identity not independent")
    return {
        "status": "A_REVIEW_PROVIDER_CAPTURE_BOUND",
        "external_capture_sha256": sha(provider),
        "capture_call_id": meta["callId"],
        "review_url": response["review_url"],
        "provider_stable_call_id": response.get("provider_stable_call_id", "UNKNOWN_NOT_EXPOSED"),
        "scope": "Outside-candidate provider capture consistency; external authority still needs independent platform verification",
    }
