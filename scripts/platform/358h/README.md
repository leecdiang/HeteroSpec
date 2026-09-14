# 358H platform scripts

Status: **PREFLIGHT READY — FORMAL MEASUREMENT STILL BLOCKED**

These tools prepare and qualify the Core Ultra X7 358H environment without claiming a result.

## First boot on the 358H machine

From PowerShell at the repository root:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\platform\358h\setup_358h.ps1
```

The bootstrap creates `.venv-358h`, installs `requirements/358h.txt`, and writes a non-formal device inventory under `runs/358h/qualification/`. The inventory intentionally exits non-zero until an exact OpenVINO IR is supplied.

After exporting the frozen draft representation, run:

```powershell
.\.venv-358h\Scripts\python.exe scripts\platform\358h\qualify_environment.py `
  --model-xml "$env:HETEROSPEC_MODEL_ROOT\qwen3-0.6b-ov\openvino_model.xml" `
  --devices CPU GPU NPU `
  --output runs\358h\qualification\environment_with_model.json
```

Qualification passes only if all three requested devices exist, the exact IR compiles on each, and `EXECUTION_DEVICES` reports the requested physical device. `AUTO`, `MULTI`, and `HETERO` are rejected.

## Phase boundaries

1. Run the inventory and model compile probe. Copy the resulting versions, exact device names, hashes, and limitations into `reports/358h/358H_ENVIRONMENT_QUALIFICATION.md`.
2. Freeze `pip freeze`, model export command, IR hashes, contexts `[512, 2048, 8192]`, warm-up/repetition counts, telemetry boundaries, target placement, and the numeric threshold rule in the preregistration.
3. Commit the completed preregistration before collecting formal timing.
4. Record Phase-1 summaries as CSV with columns `device,context,draft_k2_ms` plus the full raw provenance.
5. Run `threshold_gate.py`. Only `BORDERLINE` or `GO` paths may enter Phase 3.

Threshold invocation after assigning the preregistered, measured inputs:

```powershell
.\.venv-358h\Scripts\python.exe scripts\platform\358h\threshold_gate.py `
  --draft-csv analysis\358h_draft_device_summary.csv `
  --target-token-ms $TbMs `
  --verification-factor $V2Exact `
  --residual-ms $TxMs `
  --central-committed $CentralCommitted `
  --output analysis\358h_threshold_summary.json
```

Define those four variables from values frozen before the gate. Never reuse M4, CUDA, or B570 timing constants as though they were measurements of the 358H execution path.

The formal draft runner is deliberately not fabricated here: the exact exported graph, stateful-generation API, target placement, NPU compile support, and telemetry boundary must be established on the physical machine first.
