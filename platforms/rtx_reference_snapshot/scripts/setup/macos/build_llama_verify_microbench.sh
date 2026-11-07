#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
c++ -std=c++17 -O2 \
  -I/opt/homebrew/include \
  "$repo_root/scripts/setup/macos/llama_verify_microbench.cpp" \
  -L/opt/homebrew/lib -Wl,-rpath,/opt/homebrew/lib \
  -lllama -lggml -lggml-base \
  -o "$repo_root/work/m4/llama_verify_microbench"
