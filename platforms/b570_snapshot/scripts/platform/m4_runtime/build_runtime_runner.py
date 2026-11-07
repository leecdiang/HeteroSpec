#!/usr/bin/env python3
"""Build the M4 guard against the pinned installed llama.cpp common library."""

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "scripts/platform/m4_runtime/runtime_runner.cpp"
HEADERS = ROOT / "scripts/platform/m4_runtime/upstream_headers"
OUT = ROOT / "runs/m4/runtime_profitability_control_20260924/build"
EXPECTED = "5266f24da"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    version = subprocess.check_output(["/opt/homebrew/bin/llama-server", "--version"],
                                      text=True, stderr=subprocess.STDOUT)
    if EXPECTED not in version:
        raise SystemExit(f"Pinned llama.cpp commit missing: {version.strip()}")
    OUT.mkdir(parents=True, exist_ok=True)
    binary = OUT / "m4-runtime-runner"
    command = ["clang++", "-std=c++17", "-O2", "-I", str(HEADERS),
               "-I", "/opt/homebrew/include", str(SRC), "-L", "/opt/homebrew/lib",
               "-Wl,-rpath,/opt/homebrew/lib", "-lllama-common", "-lllama", "-lggml",
               "-lggml-base", "-o", str(binary)]
    subprocess.run(command, check=True)
    manifest = {
        "schema": "heterospec.m4_runtime.build.v0.1",
        "upstream_version": version.strip(),
        "source_sha256": sha(SRC),
        "headers_sha256": {p.name: sha(p) for p in sorted(HEADERS.glob("*.h"))},
        "binary_sha256": sha(binary),
        "compiler": subprocess.check_output(["clang++", "--version"], text=True).splitlines()[0],
        "command": command,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"binary": str(binary), "binary_sha256": manifest["binary_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
