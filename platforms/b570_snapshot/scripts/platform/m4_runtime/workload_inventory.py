#!/usr/bin/env python3
"""Inventory M4-exposed prompts without reading their performance values."""

import csv
import gzip
import hashlib
import json
import re
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "benchmarks/m4_runtime/WORKLOAD_INVENTORY.json"
SPEC = ROOT / "datasets/Spec-Bench/data/spec_bench/question.jsonl"
HUMAN = ROOT / "datasets/human-eval/data/HumanEval.jsonl.gz"
TEMPLATE = (
    "Complete the following Python function. Return only the completed Python "
    "code, without Markdown fences.\n\n{humaneval_prompt}"
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def rel(path):
    return str(path.relative_to(ROOT))


def walk_ids(value, family):
    if isinstance(value, dict):
        for key, item in value.items():
            if family == "Spec-Bench" and key == "question_id" and isinstance(item, int):
                yield str(item)
            elif family == "HumanEval" and key == "task_id" and isinstance(item, str):
                yield item
            elif family == "Spec-Bench" and key == "question_ids" and isinstance(item, list):
                yield from (str(x) for x in item if isinstance(x, int))
            elif family == "HumanEval" and key == "task_ids" and isinstance(item, list):
                yield from (x for x in item if isinstance(x, str))
            else:
                yield from walk_ids(item, family)
    elif isinstance(value, list):
        for item in value:
            yield from walk_ids(item, family)


def main():
    if not SPEC.is_file() or not HUMAN.is_file():
        raise SystemExit("Both pinned local datasets are required for the inventory")
    exposed = defaultdict(set)
    evidence = defaultdict(set)
    sources = [
        ROOT / "work/m4",
        ROOT / "artifacts/m4_humaneval_code_conditioned",
        ROOT / "analysis",
        ROOT / "benchmarks/m4_confirmatory_24q",
        ROOT / "benchmarks/m4_code_conditioned_30q",
        ROOT / "benchmarks/root_cause_12q",
    ]
    scanned = []
    for source in sources:
        paths = sorted(source.rglob("*")) if source.is_dir() else [source]
        for path in paths:
            if not path.is_file() or path.suffix not in {".json", ".csv", ".txt"}:
                continue
            if source == ROOT / "analysis" and not path.name.startswith("m4_"):
                continue
            if path.stat().st_size > 30_000_000:
                continue
            scanned.append(rel(path))
            found = {"Spec-Bench": set(), "HumanEval": set()}
            try:
                if path.suffix == ".json":
                    obj = json.loads(path.read_text(encoding="utf-8"))
                    for family in found:
                        found[family].update(walk_ids(obj, family))
                elif path.suffix == ".csv":
                    with path.open(newline="", encoding="utf-8") as stream:
                        for row in csv.DictReader(stream):
                            if row.get("question_id", "").isdigit():
                                found["Spec-Bench"].add(row["question_id"])
                            if row.get("task_id", "").startswith("HumanEval/"):
                                found["HumanEval"].add(row["task_id"])
            except (ValueError, UnicodeError, csv.Error):
                pass
            match = re.search(r"(?:^|[_-])q(\d+)(?:[_.-]|$)", path.name, re.I)
            if source == ROOT / "work/m4" and match:
                found["Spec-Bench"].add(match.group(1))
            match = re.search(r"HumanEval_(\d+)", path.name)
            if match:
                found["HumanEval"].add(f"HumanEval/{match.group(1)}")
            for family, ids in found.items():
                for task_id in ids:
                    exposed[(family, task_id)].add("prior_m4_execution_or_selection")
                    evidence[(family, task_id)].add(rel(path))

    rows = []
    spec_rows = [json.loads(line) for line in SPEC.read_text(encoding="utf-8").splitlines()]
    with gzip.open(HUMAN, "rt", encoding="utf-8") as stream:
        human_rows = [json.loads(line) for line in stream]
    for item in spec_rows:
        task_id = str(item["question_id"])
        key = ("Spec-Bench", task_id)
        prior = bool(exposed[key])
        prompt = item["turns"][0]
        rows.append({
            "workload_family": "Spec-Bench", "stratum": item["category"],
            "task_id": task_id, "prompt_hash": sha(prompt.encode("utf-8")),
            "seen_in_historical_m4_execution": prior,
            "historical_outcome_exposed": prior,
            "eligible_for_calibration": not prior,
            "eligible_for_heldout": not prior,
            "evidence": sorted(evidence[key]),
        })
    for item in human_rows:
        task_id = item["task_id"]
        key = ("HumanEval", task_id)
        prior = bool(exposed[key])
        prompt = TEMPLATE.replace("{humaneval_prompt}", item["prompt"])
        rows.append({
            "workload_family": "HumanEval", "stratum": "code_completion",
            "task_id": task_id, "prompt_hash": sha(prompt.encode("utf-8")),
            "seen_in_historical_m4_execution": prior,
            "historical_outcome_exposed": prior,
            "eligible_for_calibration": not prior,
            "eligible_for_heldout": not prior,
            "evidence": sorted(evidence[key]),
        })
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    out = {
        "schema": "heterospec.m4_runtime.workload_inventory.v0.1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": head,
        "method": "Conservative ID extraction from historical M4 raw JSON, CSV summaries, selections, and local prompt filenames; performance values are never used for eligibility.",
        "datasets": {rel(path): sha(path.read_bytes()) for path in (SPEC, HUMAN)},
        "scanned_files": scanned,
        "summary": {
            family: {
                "total": sum(x["workload_family"] == family for x in rows),
                "exposed": sum(x["workload_family"] == family and x["historical_outcome_exposed"] for x in rows),
                "eligible": sum(x["workload_family"] == family and x["eligible_for_heldout"] for x in rows),
            } for family in ("Spec-Bench", "HumanEval")
        },
        "candidates": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(out["summary"], indent=2))


if __name__ == "__main__":
    main()
