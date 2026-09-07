#!/usr/bin/env python3
"""Build a sanitized checksum manifest for the archived M4 evidence."""

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts/m4_humaneval_code_conditioned/manifest.json"

HISTORICAL = [
    "work/m4/qwen3_8b_bf16_load_smoke.json",
    "work/m4/qwen3_8b_8bit_load_smoke.json",
    "work/m4/q395_k4_postreboot_timed.json",
    "work/m4/silemetry_q395_k4_postreboot_timed.csv",
    "work/m4/q469_k2_correctness_recheck.json",
    "work/m4/q469_divergence_logits.json",
    "work/m4/q395_8bit_k2_recheck.json",
    "work/m4/q469_8bit_k2.json",
    "work/m4/m4_mlx_12q_pilot.json",
    "work/m4/llama_q503_extraction_smoke.json",
    "work/m4/llama_metal_q8_395_469_k2.json",
    "work/m4/llama_metal_q8_395_469_k4.json",
    "work/m4/llama_metal_q8_395_469_k6.json",
    "work/m4/llama_metal_q8_12q_formal.json",
    "work/m4/silemetry_llama_q8_12q_formal.csv",
    "work/m4/llama_verify_q8_synced.csv",
    "work/m4/llama_k2_decomposition.json",
    "work/m4/llama_draft_residency_control.json",
    "work/m4/llama_synthetic_crossover.json",
    "work/m4/llama_k2_repro_check.json",
    "work/m4/llama_confirmatory_24q.json",
    "work/m4/silemetry_confirmatory_24q.csv",
]


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def describe(path):
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def command(*args):
    return subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True).stdout.strip()


def main():
    current = []
    for pattern in [
        "artifacts/m4_humaneval_code_conditioned/*",
        "analysis/m4_humaneval_*",
        "reports/m4/figures/m4_humaneval_*",
    ]:
        current.extend(path for path in ROOT.glob(pattern) if path.is_file() and path != OUTPUT)
    current.extend([
        ROOT / "benchmarks/m4_code_conditioned_30q/preregistration.json",
        ROOT / "benchmarks/m4_code_conditioned_30q/README.md",
        ROOT / "reports/m4/M4_HUMANEVAL_CODE_CONDITIONED.md",
        ROOT / "reports/m4/M4_EXPERIMENT_INDEX.md",
        ROOT / "scripts/m4_humaneval_code_conditioned.py",
        ROOT / "scripts/summarize_m4_humaneval.py",
        ROOT / "scripts/build_m4_archive_manifest.py",
    ])
    result = json.loads((ROOT / "artifacts/m4_humaneval_code_conditioned/results.json").read_text())
    manifest = {
        "schema": "heterospec.m4_archive_manifest.v1",
        "authoritative": {
            "run_record": "artifacts/m4_humaneval_code_conditioned/results.json",
            "power_trace": "artifacts/m4_humaneval_code_conditioned/telemetry.csv",
            "preregistration": "benchmarks/m4_code_conditioned_30q/preregistration.json",
        },
        "run": {
            "status": result["status"],
            "started_utc": result["started"],
            "ended_utc": result["ended"],
            "runs": len(result["runs"]),
            "schedule_and_seed_embedded_in_run_record": True,
            "human_eval_git_commit": result["human_eval_git_commit"],
            "human_eval_archive_sha256": result["dataset_sha256"],
        },
        "system": {
            "model": "MacBook Air (Mac16,13)",
            "chip": "Apple M4, 10 cores (4 performance, 6 efficiency)",
            "unified_memory_gb": 24,
            "os": "macOS 26.6.2 (25G83)",
            "architecture": "arm64",
            "privacy_note": "Serial number, hardware UUID, provisioning UDID, username, and host name are intentionally omitted.",
        },
        "runtime": {
            "llama_cpp": "0.4.0, build 10809, commit 5266f24da, AppleClang 21.0.0.21000101",
            "mlx": "0.32.2",
            "mlx_lm": "0.31.3",
            "telemetry": "Silemetry probe built from scripts/setup/macos/silemetry_csv_probe.c",
        },
        "models": [
            {
                "name": "Qwen3-8B-Q8_0.gguf", "bytes": 8709518112,
                "sha256": "408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6",
                "archived": False,
            },
            {
                "name": "Qwen3-0.6B-Q8_0.gguf", "bytes": 639446688,
                "sha256": "9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031",
                "archived": False,
            },
        ],
        "current_experiment_files": [describe(path) for path in sorted(set(current))],
        "historical_m4_evidence": [
            describe(path) for path in sorted({
                *(ROOT / item for item in HISTORICAL),
                *ROOT.glob("work/m4/llama_12q_q*_prompt.txt"),
                *ROOT.glob("work/m4/confirmatory_q*.txt"),
            })
        ],
        "excluded": [
            {"path": "model weights", "reason": "9.35 GB total; hashes and artifact names retained"},
            {"path": ".venv-m4 and caches", "reason": "rebuildable environment/cache material"},
            {"path": "datasets/human-eval", "reason": "external dataset pinned by commit and archive SHA-256"},
            {"path": "work/m4/silemetry_csv_probe", "reason": "local build product; source and build script tracked"},
            {"path": "work/m4/llama_verify_microbench", "reason": "local build product; source and build script tracked"},
            {"path": "redundant warmup/debug runs", "reason": "superseded by the listed formal records"},
        ],
        "git": {
            "branch": command("git", "-C", str(ROOT), "branch", "--show-current"),
            "head_before_archive_commit": command("git", "-C", str(ROOT), "rev-parse", "HEAD"),
        },
    }
    OUTPUT.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
