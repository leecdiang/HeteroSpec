#!/usr/bin/env python3
"""Pre-formal static gates; this is not a formal-run authorization."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BASE = "b80bdbc67f6e19829245ad732390cd6aef941675"
ALLOWED = ("benchmarks/m4_runtime/", "scripts/platform/m4_runtime/")


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def check():
    errors = []
    if git("merge-base", "HEAD", BASE) != BASE:
        errors.append("Study branch is not based on the audited main SHA")
    paths = set(git("diff", "--name-only", BASE).splitlines())
    paths.update(git("ls-files", "--others", "--exclude-standard").splitlines())
    illegal = sorted(p for p in paths if p and not p.startswith(ALLOWED))
    if illegal:
        errors.append(f"Files outside runtime-study paths changed: {illegal}")
    b = ROOT / "benchmarks/m4_runtime"
    protocol = json.loads((b / "runtime_policy_protocol_v0.json").read_text())
    for key, expected in (
        ("study_type", "PROSPECTIVE_RUNTIME_POLICY_STUDY"),
        ("energy", "NOT_CLAIMED"),
        ("formal_heldout_data_seen", False),
    ):
        if protocol.get(key) != expected:
            errors.append(f"Protocol {key} mismatch")
    inventory_bytes = (b / "WORKLOAD_INVENTORY.json").read_bytes()
    inventory = json.loads(inventory_bytes)
    seen = set()
    expected_prompts = set()
    for key in ("QUALIFICATION", "CALIBRATION", "HELDOUT"):
        split = json.loads((b / f"{key}_SPLIT.json").read_text())
        if split["inventory_sha256"] != hashlib.sha256(inventory_bytes).hexdigest():
            errors.append(f"{key} inventory hash mismatch")
        for row in split["tasks"]:
            identity = (row["workload_family"], row["task_id"])
            if identity in seen:
                errors.append(f"Split overlap: {identity}")
            seen.add(identity)
            expected_prompts.add((key, *identity))
            original = next((x for x in inventory["candidates"] if (x["workload_family"], x["task_id"]) == identity), None)
            if not original or not original["eligible_for_heldout"] or row["prompt_hash"] != original["prompt_hash"]:
                errors.append(f"Ineligible or changed prompt: {identity}")
    token_file = b / "PROMPT_TOKENS.json"
    if token_file.exists():
        tokens = json.loads(token_file.read_text())["tasks"]
        actual = {(row["split"], row["workload_family"], row["task_id"]) for row in tokens}
        if actual != expected_prompts or len(tokens) != len(expected_prompts):
            errors.append("Prompt-token list does not match the frozen splits")
        if any(row["prompt_token_count"] != len(row["prompt_token_ids"]) or
               row["prompt_token_count"] + 128 + 3 > 2048 for row in tokens):
            errors.append("Prompt tokens exceed the fixed context or have invalid counts")
    else:
        errors.append("Prompt-token file missing")
    test = subprocess.run([sys.executable, str(ROOT / "scripts/platform/m4_runtime/runtime_logic_unit_tests.py")], capture_output=True, text=True)
    if test.returncode:
        errors.append(f"Logic tests failed: {test.stderr}")
    return errors


if __name__ == "__main__":
    problems = check()
    print(json.dumps({"status": "PASS" if not problems else "FAIL", "errors": problems}, indent=2))
    raise SystemExit(bool(problems))
