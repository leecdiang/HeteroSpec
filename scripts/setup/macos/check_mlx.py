#!/usr/bin/env python3
from importlib.metadata import version

import mlx.core as mx
import mlx_lm

print("mlx:", version("mlx"))
print("mlx-lm:", version("mlx-lm"))
print("mlx-lm path:", mlx_lm.__file__)
print("default device:", mx.default_device())
print("Metal available:", mx.metal.is_available())
if not mx.metal.is_available():
    raise SystemExit("FAIL: MLX Metal is unavailable")
print("PASS: MLX Metal runtime is available")
