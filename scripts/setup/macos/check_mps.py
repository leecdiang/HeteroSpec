#!/usr/bin/env python3
import torch

print("torch:", torch.__version__)
print("MPS built:", torch.backends.mps.is_built())
print("MPS available:", torch.backends.mps.is_available())
if not torch.backends.mps.is_available():
    raise SystemExit("FAIL: PyTorch MPS is unavailable")
x = torch.arange(8, dtype=torch.float32, device="mps")
y = (x * x).sum()
torch.mps.synchronize()
print("MPS smoke result:", y.item())
print("PASS: PyTorch executed an operation on MPS")
