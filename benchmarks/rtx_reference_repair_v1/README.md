# Reference repair: canonical state, numerical-path localization, then transfer

**Implementation and protocol, not an executed fix.** This successor starts from PR156
`47c93985010d0f3c0c55f975f4cd7761e64bcae2`. The existing 14B counterexamples remain
unchanged. The goal is to remove the mechanism causing them while preserving useful
parallel execution, not to redefine the reference or add another limitation paragraph.

## What is implemented

| Code under `scripts/experiments/rtx_reference_repair_v1/` | Function |
|---|---|
| `bootstrap.py`, `build.py`, `native.py` | Reuse original assets, authenticate exact source, stage new worker/core, invoke the existing Windows build |
| `repair_boundary.hpp` | Real UB1/unscoped producer; sequence-state + positions + initial-logit handoff; R→R sham and reverse producer controls |
| `repair_observer.inc`, `repair_runtime.hpp` | Actual scheduler-node backend assignment, distinct buffer owner; bounded post-evaluation tensor capture |
| `probes.py`, `tensors.py` | Same-token-prefix replay, trace/no-trace controls, strided logical-value comparison; no diagnostic result used for performance |
| `repair_mm.hpp`, `operator_patch.py` | Opt-in per-operator Q8 single-row matmul graph primitive; source-bound and off by default |
| `plan.py`, `audit.py`, `run.py` | Development matrix, exact endpoints/transactions/vectors/state audit, versioned execution, frozen held-out gate and matched cost |
| `archive.py` | Local evidence sharding and every-member hash readback; no upload claim |

The inherited acceptance/correction/bonus loop is not rewritten. A reference producer
copies its actual initial logits and carries the pending token without consuming it
into KV. Do not read stale logits from a newly restored receiver. Every producer creation,
execution, state transfer and destruction is inside the candidate service timer.

## Exact start commands (Windows; adapt actual local paths)

Use a clean worktree of `experiment/reference-repair-20261101`, published through
the GitHub connector and stacked on PR156's `codex/pr155-qwen14b` branch. Read back
the PR/head before execution. The earlier offline `publish_pr.py` is no longer
needed for this already-published branch; do not run it to create a duplicate PR.
See `HOST_PROMPT.md` and `PUBLICATION_STATUS.md`.

From the repository root:

```powershell
$code = "scripts/experiments/rtx_reference_repair_v1"
python -B -m unittest discover -s "$code/tests" -v
python -B "$code/bootstrap.py" --repo . --parent <PR156-execution-bundle> --research D:/hs-reference-repair --out D:/hs-repair-config01 --source-archive <authenticated-original-source.zip>
python -B "$code/build.py" --config D:/hs-repair-config01/BUILD_CONFIG.json
python -B "$code/run.py" prepare --config D:/hs-repair-config01/HOST_CONFIG.json --out D:/hs-reference-repair/epoch01
python -B "$code/run.py" admit --bundle D:/hs-reference-repair/epoch01
python -B "$code/run.py" develop --bundle D:/hs-reference-repair/epoch01 --attempt development01
```

`--parent` is the original directory containing `BINDING.json`, `LOCAL_PATHS.json`
and `CONFIG.json`, not merely the project directory. Bootstrap makes no model request.
Its default safety budgets are adjustable ceilings, not finish-time estimates; review
memory/disk reservations and coordinate the inherited GPU lock with other agents.

If canonical prefill fails, continue mechanism work; do NOT declare the successor
finished merely because a development matrix has a counterexample. Read PROTOCOL.md.

```powershell
python -B "$code/probes.py" make --bundle D:/hs-reference-repair/epoch01 --input GSM8K/test/111 --index 0 --out D:/hs-reference-repair/probe-initial.json
python -B "$code/run.py" probe --bundle D:/hs-reference-repair/epoch01 --slots D:/hs-reference-repair/probe-initial.json --attempt probe-initial01
python -B "$code/probes.py" audit --root D:/hs-reference-repair/epoch01/units/probe-initial01/native --slots D:/hs-reference-repair/probe-initial.json --out D:/hs-reference-repair/probe-initial-audit.json
```

Indices 16 and 82 target the previously observed first output divergences. Earlier
checkpoints are needed to find the first *observed internal* difference. For narrower
captures use `--pattern` with source-verified node names. A captured mismatch is not
by itself the causal operator. Q/K/V layouts may need an explicit logical axis/row
mapping; default comparisons refuse incompatible shapes.

## Candidate development and final verification

Start with `rowwise_roles=0`. Once evidence points to an operator class, change the
build config to mask 1 (Q/K/V), 2 (attention output), 4 (FFN), or a justified combination.
Use a fresh build/epoch and preserve the old source, binary, results and budget. The
row wrapper is an implementation primitive, not a proven native numerical fix.
Unknown exact source anchors fail rather than patch arbitrary call sites.

After a consistent mechanism, own-path controls and regressions are established,
complete the mechanism record and freeze:

```powershell
python -B "$code/run.py" freeze --bundle D:/hs-reference-repair/epoch01 --audit D:/hs-reference-repair/epoch01/development01_AUDIT.json --mechanism <completed-mechanism-record.json>
python -B "$code/run.py" confirm --bundle D:/hs-reference-repair/epoch01
```

Confirmation runs 24 old-binary reference requests, 120 new-binary qualification
requests and, only if all pass, 576 timing/warmup requests. A new R implementation
is compared against the original PR156 EXE/DLLs; it cannot become its own oracle.

## Host-specific work still required

1. Actual Windows compilation/linking and ABI acceptance of the staged worker.
2. Inspect exact graph-node names and compare scheduler metadata to frozen source;
   unknown mapping is a source-review task, not permission to guess a device.
3. Choose a minimal repair from observed evidence; no algorithmic success is asserted.
4. Original 8B and prior Llama regressions use their pinned native harnesses. Their
   execution integration is not automated by this 14B runner. Reserve those requests
   in the shared development budget and retain their original references.
5. Review license/privacy, upload evidence, download it again and verify members.

No independent subagents or GPU were available in the authoring environment. Tests
include pure-Python checks, exact source-transform fixtures, and a compiled mock CPU
API test of the row-wise graph/stride primitive—not real Q8 or CUDA qualification.

Capacity admission additionally allocates a transient UB1/PQ/QB producer context over the resident pools, checking the observed RAM/VRAM reserve before any generated token. It is a provisioning sample, not a guarantee of every transient peak. Clean timing skips the new geometry inventory; diagnostic and clean output controls remain mandatory.
