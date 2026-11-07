#!/usr/bin/env sh
set -eu

REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-$(command -v python3.11 || true)}"
VENV_PATH="${HETEROSPEC_M4_VENV:-$REPO_ROOT/.venv-m4}"

if [ -z "$PYTHON_BIN" ]; then
  echo "FAIL: Python 3.11 is required (install it with Homebrew)." >&2
  exit 1
fi

"$PYTHON_BIN" -m venv "$VENV_PATH"
"$VENV_PATH/bin/python" -m pip install --upgrade pip
"$VENV_PATH/bin/python" -m pip install -r "$REPO_ROOT/requirements/macos-mlx.txt"
echo "PASS: isolated environment ready at $VENV_PATH"
