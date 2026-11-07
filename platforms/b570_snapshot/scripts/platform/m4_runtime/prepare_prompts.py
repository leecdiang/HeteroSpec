#!/usr/bin/env python3
"""Freeze direct GGUF chat-template token IDs through the pinned llama-server."""

import argparse
import gzip
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from workload_inventory import HUMAN, SPEC, TEMPLATE


ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "benchmarks/m4_runtime"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def post(base, route, body):
    request = urllib.request.Request(
        base.rstrip("/") + route,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-url", default="http://127.0.0.1:8399")
    args = parser.parse_args()
    spec = {str(row["question_id"]): row["turns"][0]
            for row in (json.loads(line) for line in SPEC.read_text().splitlines())}
    with gzip.open(HUMAN, "rt", encoding="utf-8") as stream:
        human = {row["task_id"]: TEMPLATE.replace("{humaneval_prompt}", row["prompt"])
                 for row in (json.loads(line) for line in stream)}
    rows = []
    for name in ("CALIBRATION", "QUALIFICATION", "HELDOUT"):
        split = json.loads((BASE / f"{name}_SPLIT.json").read_text())
        for item in split["tasks"]:
            family, task_id = item["workload_family"], item["task_id"]
            raw = (spec if family == "Spec-Bench" else human)[task_id]
            if sha(raw.encode()) != item["prompt_hash"]:
                raise RuntimeError(f"Raw prompt hash changed: {family}/{task_id}")
            formatted = post(args.server_url, "/apply-template", {
                "messages": [{"role": "user", "content": raw}],
                "chat_template_kwargs": {"enable_thinking": False},
            })["prompt"]
            token_ids = post(args.server_url, "/tokenize", {
                "content": formatted, "add_special": True, "parse_special": True,
            })["tokens"]
            if not token_ids or not all(isinstance(x, int) and x >= 0 for x in token_ids):
                raise RuntimeError(f"Invalid token IDs: {family}/{task_id}")
            rows.append({
                "split": name,
                "workload_family": family,
                "stratum": item["stratum"],
                "task_id": task_id,
                "raw_prompt_sha256": item["prompt_hash"],
                "formatted_prompt_sha256": sha(formatted.encode()),
                "prompt_token_ids": token_ids,
                "prompt_token_count": len(token_ids),
            })
    if len(rows) != 116:
        raise RuntimeError(f"Expected 116 tasks, got {len(rows)}")
    out = {
        "schema": "heterospec.m4_runtime.prompt_tokens.v0.1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "method": "Pinned llama-server /apply-template then /tokenize with GGUF and thinking disabled",
        "server_url_local": args.server_url,
        "tasks": rows,
    }
    path = BASE / "PROMPT_TOKENS.json"
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"tasks": len(rows), "max_prompt_tokens": max(x["prompt_token_count"] for x in rows),
                      "over_2048_with_cap128": sum(x["prompt_token_count"] + 131 > 2048 for x in rows)}, indent=2))


if __name__ == "__main__":
    main()
