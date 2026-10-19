"""Prospective A-only source review finalizer. Never executes a Windows/native gate.

The computed result is evidence consistency, NOT an independent reviewer attestation.
An external reviewer must verify the review's origin and explicitly approve A.
"""
import hashlib
import json
import re
from pathlib import Path


def need(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_bytes())


def confined(root, relative):
    need(type(relative) is str and relative and "\\" not in relative, "review relative path")
    p = Path(relative)
    need(not p.is_absolute() and ".." not in p.parts and ":" not in relative, "review path escape")
    current = root
    for part in p.parts:
        current = current / part
        need(not current.is_symlink() and not current.is_junction(), "review alias")
    return current


def verify(root):
    root = Path(root).resolve()
    manifest_path = confined(root, "review/CANDIDATE_MANIFEST.json")
    report_path = confined(root, "review/FINAL_REVIEW.json")
    manifest, report = load(manifest_path), load(report_path)

    need(manifest.get("schema") == "B570_SOURCE_CANDIDATE_V2", "source manifest schema")
    need(re.fullmatch(r"[0-9a-f]{40}", manifest.get("candidate_commit", "")) is not None,
         "immutable source commit")
    files = manifest.get("files")
    need(type(files) is list and files, "complete source candidate inventory")
    names = []
    for row in files:
        need(type(row) is dict and set(row) == {"path", "sha256", "bytes"}, "source row schema")
        path = confined(root, row["path"])
        need(re.fullmatch(r"[0-9a-f]{64}", row["sha256"]) is not None, "source digest type")
        need(path.is_file() and path.stat().st_size == row["bytes"] and digest(path) == row["sha256"],
             "review source byte drift: " + row["path"])
        names.append(row["path"])
    need(len(names) == len(set(names)), "duplicate reviewed file")
    need(report.get("status") == "scoped-clean" and report.get("complete") is True,
         "no completed exact scoped-clean")
    need(report.get("scope") == "A_SOURCE_ONLY", "source review scope")
    need(report.get("candidate_manifest_sha256") == digest(manifest_path), "review candidate identity")
    need(report.get("candidate_commit") == manifest["candidate_commit"], "review commit identity")
    need(report.get("severity_coverage") == ["P0", "P1", "P2"], "complete P0-P2 coverage")
    covered = report.get("reviewed_files")
    need(type(covered) is list and len(covered) == len(names) and set(covered) == set(names),
         "full file coverage")
    findings = report.get("findings")
    need(type(findings) is list and all(
        type(row) is dict and row.get("severity") in ("P0", "P1", "P2")
        and row.get("disposition") == "resolved" for row in findings
    ), "unresolved P0-P2 finding")
    need(type(report.get("reviewer")) is dict and report["reviewer"].get("identity")
         and report["reviewer"].get("session_or_review_url"), "reviewer attribution missing")
    need(type(report.get("transcript_sha256")) is str
         and re.fullmatch(r"[0-9a-f]{64}", report["transcript_sha256"]), "review transcript binding")
    # This verifier checks hashes and coverage; it cannot authenticate the provider/reviewer.
    return {
        "status": "SOURCE_REVIEW_EVIDENCE_CONSISTENT",
        "candidate_commit": manifest["candidate_commit"],
        "candidate_manifest_sha256": digest(manifest_path),
        "report_sha256": digest(report_path),
        "reviewed_file_count": len(names),
        "reviewed_files": names,
        "source_only": True,
        "independent_review_authentication": "REQUIRES_EXTERNAL_VERIFICATION",
        "native_qualification": "NOT_PERFORMED",
    }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    target = confined(root, args.output)
    need(target.parent == root / "review" and not target.exists(), "new review-only output")
    evidence = verify(root)
    target.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
