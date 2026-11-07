#!/usr/bin/env python3
"""Non-formal pinned-backend comparison against a saved historical-prompt reference."""

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "runs/m4/runtime_profitability_control_20260924/r0"
BIN = ROOT / "runs/m4/runtime_profitability_control_20260924/build/m4-runtime-runner"
TARGET = Path("/Users/lee/.cache/heterospec/models/gguf-qwen3-q8/Qwen3-8B-Q8_0.gguf")
DRAFT = Path("/Users/lee/.cache/heterospec/models/gguf-qwen3-q8/Qwen3-0.6B-Q8_0.gguf")


def main():
    ref = json.loads((RUN / "server_reference.json").read_text())
    command = [str(BIN), "--model", str(TARGET), "--model-draft", str(DRAFT),
               "--device", "MTL0", "--n-gpu-layers", "all", "--spec-type", "draft-simple",
               "--spec-draft-device", "MTL0", "--spec-draft-ngl", "all", "--spec-draft-n-max", "2",
               "--spec-draft-n-min", "0", "--temp", "0", "--top-k", "0", "--top-p", "1",
               "--min-p", "0", "--seed", "123", "--ctx-size", "2048", "--batch-size", "2048"]
    cases = [("TARGET_ONLY", 2, 0), ("ALWAYS_SPEC_K2", 2, 0),
             ("GUARD_K2", 2, 1), ("GUARD_K2", 2, 1e12),
             ("GUARD_K2", 8, 1), ("TARGET_ONLY", 2, 0)]
    records = []
    with (RUN / "runner_stderr.txt").open("w") as err:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=err, text=True, bufsize=1)
        if process.stdout.readline().strip() != "READY":
            raise RuntimeError("Runner did not initialize")
        for condition, E, rate in cases:
            line = "\t".join([condition, str(E), "0.05", str(rate), "32",
                              ",".join(map(str, ref["prompt_token_ids"]))]) + "\n"
            process.stdin.write(line)
            process.stdin.flush()
            row = json.loads(process.stdout.readline())
            records.append(row)
            print(condition, "status", row.get("status", "OK"),
                  "exact_vs_server", row.get("generated_token_ids") == ref["target_token_ids"],
                  "fallback_round", row.get("fallback_round"))
        process.stdin.write("QUIT\n")
        process.stdin.flush()
        process.wait(timeout=20)
    (RUN / "qualification_smoke.json").write_text(json.dumps({
        "records": records, "reference_token_ids": ref["target_token_ids"]}, indent=2))
    if process.returncode:
        raise RuntimeError(f"Runner exit {process.returncode}")


if __name__ == "__main__":
    main()
