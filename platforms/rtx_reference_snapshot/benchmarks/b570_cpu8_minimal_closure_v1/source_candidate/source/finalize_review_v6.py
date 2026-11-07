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
    # A self-authored short manifest is not a complete review scope. Bind its
    # EXACT inventory to the independently pinned 122+ source and input list.
    composition_path = confined(root, "review/PINNED_SOURCE_COMPOSITION.json")
    composition = load(composition_path)
    need(manifest.get("source_composition_sha256") == digest(composition_path),
         "source composition identity")
    source_rows = composition.get("source_import_composition")
    reference_rows = composition.get("a2_references")
    need(type(source_rows) is list and len(source_rows) >= 123
         and type(reference_rows) is list and len(reference_rows) >= 10,
         "A2 full source and auxiliary inputs absent")
    required = {
        "source/operation_guard.py", "source/finalize_review_v6.py",
        "source/verify_cpu8.py", "source/integration_gates.py",
        "source/native_gate_audit.py", "source/engineering_gates_v6.py",
        "source/operation_roles_v7.py", "source/operation_pricing_v7.py",
        "source/b_negative_binding_v7.py", "source/source_review_origin_v7.py", "src/rev2/win.py",
    }
    need(required.issubset({x["path"] for x in source_rows}), "A2 required modules absent")
    expected = {x["path"]: (x["sha256"], x["bytes"]) for x in source_rows + reference_rows}
    need(len(expected) == len(source_rows) + len(reference_rows), "duplicate full review input")
    files = manifest.get("files")
    need(type(files) is list and len(files) == len(expected),
         "complete source candidate inventory")
    names = []
    for row in files:
        need(type(row) is dict and set(row) == {"path", "sha256", "bytes"}, "source row schema")
        path = confined(root, row["path"])
        need(re.fullmatch(r"[0-9a-f]{64}", row["sha256"]) is not None, "source digest type")
        need(path.is_file() and path.stat().st_size == row["bytes"] and digest(path) == row["sha256"],
             "review source byte drift: " + row["path"])
        names.append(row["path"])
    need(len(names) == len(set(names)), "duplicate reviewed file")
    need(set(names) == set(expected) and
         all((row["sha256"], row["bytes"]) == expected[row["path"]] for row in files),
         "manifest omits or substitutes pinned review inputs")

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
