#!/bin/bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/../../.." && pwd)"
silemetry_root="${SILEMETRY_ROOT:-$(dirname "$repo_root")/Silemetry-mac}"
core_root="$silemetry_root/TelemetryCore"
target_root="$core_root/target/aarch64-apple-darwin/release"
library="$target_root/libthermalbench_telemetry_core.a"
output="${1:-$repo_root/work/m4/silemetry_csv_probe}"

if [[ ! -f "$core_root/Cargo.toml" ]]; then
    echo "Silemetry TelemetryCore not found at: $core_root" >&2
    echo "Set SILEMETRY_ROOT to the Silemetry-mac checkout." >&2
    exit 1
fi

cargo build --manifest-path "$core_root/Cargo.toml" --release --target aarch64-apple-darwin
mkdir -p "$(dirname "$output")"
clang -O2 \
    -I"$core_root/include" \
    "$repo_root/scripts/setup/macos/silemetry_csv_probe.c" \
    "$library" \
    -framework CoreFoundation \
    -framework IOKit \
    -lIOReport \
    -o "$output"

echo "$output"
