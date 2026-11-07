#!/usr/bin/env python3
"""Run current checks and authenticate the historical Phase-4 checkpoint receipt."""

import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "paper/mlsys2027/scripts"
EVIDENCE = ROOT / "paper/mlsys2027/evidence"
PHASE4_INPUT = "3b6d7eee8888f96c71835b0b15eb1c7cb074a038"
PHASE4_OUTPUT = "d3ae7067fc5ff285d87238f8c48a7104ebfb349d"
PHASE5_OUTPUT = "0f0d2a8ab84271f0f7a08d8b9051cf85ef113c55"
PHASE4_VALIDATOR = "paper/mlsys2027/scripts/validate_claim_calibration_v083.py"
RELATED = "paper/mlsys2027/manuscript/sections/08_related_work.tex"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def run_script(label, name):
    result = subprocess.run([sys.executable, str(SCRIPTS / name)], cwd=ROOT,
                            capture_output=True, text=True)
    if result.returncode:
        raise AssertionError(f"{label}: FAIL\n{result.stdout}{result.stderr}")
    print(f"{label}: PASS")


def verify_phase4_receipt():
    receipt = json.loads((EVIDENCE / "PHASE4_CHECKPOINT_VALIDATION_V083.json").read_text())
    for commit in (PHASE4_INPUT, PHASE4_OUTPUT, PHASE5_OUTPUT):
        check(git("cat-file", "-t", commit).strip() == b"commit", "missing checkpoint: " + commit)
    check(subprocess.run(["git", "merge-base", "--is-ancestor", PHASE4_INPUT, PHASE4_OUTPUT],
                         cwd=ROOT).returncode == 0, "Phase-4 input/output ancestry")
    check(subprocess.run(["git", "merge-base", "--is-ancestor", PHASE4_OUTPUT, PHASE5_OUTPUT],
                         cwd=ROOT).returncode == 0, "Phase-4/5 ancestry")
    check(subprocess.run(["git", "merge-base", "--is-ancestor", PHASE5_OUTPUT, "HEAD"],
                         cwd=ROOT).returncode == 0, "current branch does not descend from Phase 5")
    original = git("show", f"{PHASE4_OUTPUT}:{PHASE4_VALIDATOR}")
    check(receipt.get("phase") == 4 and
          receipt.get("checkpoint_commit") == PHASE4_OUTPUT and
          receipt.get("validator_path") == PHASE4_VALIDATOR and
          receipt.get("validator_sha256") == hashlib.sha256(original).hexdigest() and
          receipt.get("result") == "PASS" and
          receipt.get("checkpoint_local_checks", {}).get("related_work_unchanged") == "PASS",
          "Phase-4 checkpoint receipt binding")
    check(git("show", f"{PHASE4_INPUT}:{RELATED}") ==
          git("show", f"{PHASE4_OUTPUT}:{RELATED}"), "Related Work changed during Phase 4")
    check(git("show", f"{PHASE4_OUTPUT}:{RELATED}") !=
          git("show", f"{PHASE5_OUTPUT}:{RELATED}"), "Phase-5 Related Work change absent")
    print("Phase 4 checkpoint: PASS")


def main():
    run_script("Phase 1 current-state", "validate_b570_prediction_ledger_v083.py")
    run_script("Phase 2 current-state", "validate_b570_commitment_appendix_v083.py")
    run_script("Phase 3 current-state", "validate_evidence_classes_v083.py")
    verify_phase4_receipt()
    run_script("Phase 5 current-state", "validate_novelty_and_secondary_boundaries_v083.py")
    run_script("Phase 4/5 current scientific invariants", "validate_current_scientific_invariants_v083.py")
    figure3 = ROOT / "paper/mlsys2027/manuscript/figures/presentation_v07/validate.py"
    result = runpy.run_path(str(figure3))["validate"]()
    check(result["status"] == "PASS", "Figure 3 validator")
    print("Figure 3: PASS")
    print("--------------------------------")
    print("PRIOR PHASES: PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("PRIOR PHASES: FAIL:", error, file=sys.stderr)
        sys.exit(1)
