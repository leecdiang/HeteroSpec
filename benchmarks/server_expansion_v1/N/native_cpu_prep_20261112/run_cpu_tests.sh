#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# No native shared libraries, model files, drivers, device queries or GPU contexts.
build=$(mktemp -d)
trap 'rm -rf "$build"' EXIT
for flags in '' '-DNDEBUG'; do
  g++ -std=c++17 -O2 -Wall -Wextra -Werror $flags test_lifecycle.cpp -o "$build/lifecycle"
  "$build/lifecycle"
done
for flags in '' '-O'; do
  (cd budget && python $flags test_budget.py)
  (cd writer && python $flags test_raw_writer.py)
  python $flags test_source_gate.py
done
python writer/interop_test.py ../n1a_lifecycle_20261112/plan/raw_compare.js
