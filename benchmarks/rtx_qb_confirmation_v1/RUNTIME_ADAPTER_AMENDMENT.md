# Prospective runtime adapter correction, 2026-10-14

This amendment fixes only the inherited per-family/arm runtime binding identified by the Phase 0 stop at `ccfbc2e4c3ab3026a6bbec5caf4c98646781913c`. That failure commit, its `RESULT.md`, and the complete `execution_20261014/` receipt are retained unchanged. No scientific request was started by that attempt.

The original PR98 executable remains selected for Qwen in every arm and for SmolLM2/Llama R, M_QB and C_QB. SmolLM2/Llama M_PQ and C_PQ select the original PR98 metadata-capacity-corrected executable, with its corresponding source/build identity. Both executables use the same 21 numerical DLLs. No binary is rebuilt and no historical file is edited.

`RUNTIME_MANIFEST.json` enumerates all 15 family/arm coordinates, fixed executable names and SHA-256, associated build-manifest SHA-256 and source-inventory identity. The adapter uses the selected build for command admission, request runtime identity and actual loaded-module verification. The pinned inherited helper modules are not modified.

Execution FREEZE schema 2 binds the runtime manifest, a passing prospective Phase 0 receipt, host identity, both executables, both inherited build manifests, numerical DLLs, all six models, full driver scripts, Python executable and NVIDIA driver binary. Registration/readback checks require this schema and the passing gate. Each actual E2 load still separately checks full offload and actual numerical modules.

The deterministic seed, exposed panel, task IDs/token sequences, warmups, block order, six sessions, AB/BA balancing, process/request budgets, time separation, request timer, reference contract, statistical unit, qualification and 1.02 threshold are unchanged. The new Phase 0 compares the generated panel and schedule to the stopped attempt byte-for-data. No scientific retry or budget reset occurred.

At the user's explicit request for automatic attendance, `supervise_e2.py` launches each session once, waits until its original admitted time, and stops on a nonzero exit. It cannot replace failed slots or start E1. A separate chat heartbeat monitors this supervisor and undertakes E1 only after E2 completion and its own authenticated freeze. Waiting time is not native owned-process lifetime. The supervisor targets only its own child; no existing GPU job is killed.

CPU adapter tests exercise all 15 routes, executable/source identity binding, wrong-loaded-executable rejection, helper restoration, manifest tampering and unchanged schedule. These tests do not supply GPU scientific evidence.
