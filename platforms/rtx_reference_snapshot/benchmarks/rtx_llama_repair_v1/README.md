# Llama mechanism repair — executed-history-first successor to PR159

**Implementation and CPU validation only. No new model, CUDA or Windows execution has been performed in this authoring environment. The Llama counterexample is not claimed fixed.**

Base commit: `38b3d3d3929dc958e6a2a7e0bdc8abd61ff38ab1` (PR159).
Start with [HOST_PROMPT.md](HOST_PROMPT.md), [HISTORY_AND_PROTOCOL.md](HISTORY_AND_PROTOCOL.md), then the commands below. The actual numerical repair is selected from new causal evidence; this PR supplies most history/build/run/probe/audit/confirmation plumbing.

## Why this is not another Qwen patch

The old Llama failure is CodeContests/valid/108, 737 formatted prompt tokens, first output disagreement at zero-based index 81. PQ and QB agree with each other. PR151 already tried P1 and P4_NATIVE: M_PQ preserves R under both, while C_PQ/C_QB fail under both. Those were natural recipes, **not common-state interventions**. PR159 reproduced the same failure while fixing Qwen14B. Default new numerical patch = none. Do not enable Qwen's head-normalization offload rule merely because it fixed another model.

## What is implemented

* `history.py`: pins and reconstructs the 54 old diagnostic requests and 5,916 complete Llama vectors. Maps the first endpoint/logit disagreement to the **actual** verification cycle/row, including partial acceptance and bonus. Exports exact three-input development data, original binding and R endpoints. Reads old raw; never generates a replacement oracle.
* `parent.py` / `native_stage.py`: materialize the exact PR159 helpers, parameterize its already-executed metadata4 Llama adapter, retain the fresh-context lifetime fix, compile from the original capsule and 21 libraries. All introduced sources and optional mechanism extension are bound.
* `llama_probe.hpp`: checkpoint actual pre-verification KV/pending state. Optional fresh q1/q4 consumers receive identical bytes; q4 own-path replay must reproduce actual natural verification rows. Shadow execution cannot mutate the live context. Extra calls are explicitly diagnostic and charged. Shared state is the captured C state, **not asserted to be canonical R**.
* `triage.py`: complete-row replay comparison and stride-aware layer-output alignment. Outputs/producing-node checkpoints are not mislabeled as pre-operation operands.
* `host.py`: reuses the source-bound Windows Job/lock/handshake/cleanup runner. Development counterexamples remain data rather than a permanent stop. Resource reservations may be increased with reasoned hash-chained amendments. Existing completed units are re-audited before reuse.
* `panel.py` / `schedule.py` / `lr_audit.py`: deterministic unseen crossed panel, true original-binary oracle, complete qualification, six-period Williams arm order, matched warmups, full costs and dual-PQ noise check. Output exposure is registered before launch and prevents reusing a failed confirmation panel as unseen.

## Native preparation

Use the already authenticated Llama assets and original runtime, not freshly substituted models/libraries. Paths in the example JSON files must be resolved on the host. A separate folder such as `D:/llama-repair-20261102` is recommended; do not put new output under the old raw root.

From the repository root:

```powershell
$code = 'scripts/experiments/rtx_llama_repair_v1'
python -B -m unittest discover -s "$code/tests" -v
python -B "$code/history.py" --repo . --raw-root <restored-PR151-diagnostic-root> --out <new-history-directory>
python -B "$code/native_stage.py" --config <filled-build-config.json>
python -B "$code/host.py" prepare --config <filled-host-config.json> --out <fresh-epoch-directory>
python -B "$code/host.py" admit --bundle <epoch>
python -B "$code/host.py" development --bundle <epoch>
```

`history.py` expects the old request-manifest relative paths under `--raw-root`. Recover them from the original release or authenticated local history; do not replace missing historical bytes with a new run. Inspect PR159's `LLAMA_HISTORICAL_BEHAVIOR.json` for the old-to-new comparison provenance. The initial development matrix is 36 requests: three inputs × six recipes × off/heavy. It is not a cap on further development.

## Evidence-led probes

Read `HISTORY.json`, then identify the real failing cycle from `candidate_vector.cycle`. No `output_index // k` shortcut. Probe the nearest observed earlier logit difference as appropriate; first output mismatch need not be first numerical difference.

```powershell
python -B "$code/schedule.py" probe --panel <epoch/DEV.json> --input 0 --arm C_QB --cycle <actual-cycle> --out <probe-slots.json>
python -B "$code/host.py" run --bundle <epoch> --name probe01 --panel <epoch/DEV.json> --slots <probe-slots.json>
python -B "$code/triage.py" --checkpoint <native-slot/checkpoint> --parent-snapshot <parent-snapshot> --out <fresh-probe-review.json>
```

Use trace/no-trace pairs and both shadow execution orders. `--trace` captures layer checkpoints; narrow `repair.trace` names/position ranges after localization. `llama_diag.mode='checkpoint'` saves actual pre-verification state without extra decoding. The natural uninstrumented request remains a separate control. For Q/K/attention axes, supply source-reviewed maps rather than assuming axis 1. If an operator replay is needed, build it for the implicated operator with complete captured parameters and own-path controls; PR159's RoPE runner is reusable only when RoPE is actually implicated.

The common-state probe compares consumers at the same **candidate** checkpoint. If they agree but natural R/C differ, inspect state provenance/reconciliation, or add an independently checked canonical-state checkpoint. Do not infer state equivalence from equal output tokens. The supplied canonical producer bridge remains available as an intervention, not the presumed fix.

## Implement a mechanism, then freeze

`native_stage.py` accepts a build-config `extension` pointing to a local Python module implementing:

```python
def apply(source, code):
    # Patch the fresh extracted source only, with exact anchors and before/after hashes.
    # Return a JSON-serializable provenance record. Never edit the original R runtime.
    return {"mechanism": "...", "changed_files": {...}}
```

The default is **no extension**, rowwise roles 0, Qwen norm-offload fix disabled. Existing rowwise support is available as an optional source-bound candidate, not a promised fix. Parameterize by semantic operator/shape/backend conditions, not task IDs, expected tokens, output positions, model-name lookup or tuned logit margins. Ordinary integration bugs may be fixed immediately with tests, receipts and a successor epoch. Preserve the fresh-context live-state capture fix.

Require causal intervention/own-path/observer controls, old Llama failure + both controls, and Qwen8B/14B regressions before freezing. Qwen regression integration uses the existing PR159 harness with the same source policy; it is not automatically executed by this Llama-only CLI. Bind its raw report hashes in the regression review; do not label the old Qwen PASS as a new regression.

Use `panel.py` with an actually tokenized source pool and complete project exposure list to select 24 unseen inputs (12 allowed when declared before outputs). Code/math × short/long, equal cells; context 1024, cap128/natural EOG remain fixed. Tokenization must use the exact original Llama tokenizer/template. The pool interface is implemented; dataset acquisition/tokenization may reuse the existing host tools and must be source-reviewed, not silently use Qwen's vocabulary.

```powershell
python -B "$code/panel.py" --pool <tokenized-pool.json> --exposures <all-old-exposures.json> --n 24 --out <new-heldout.json>
python -B "$code/host.py" seal --bundle <epoch> --panel <new-heldout.json> --mechanism <mechanism-review.json> --development <epoch/DEVELOPMENT_AUDIT.json> --regression <cross-model-review.json>
python -B "$code/host.py" confirm --bundle <epoch>
```

After sealing, `confirm` automatically runs true original-binary references, candidate qualification and all six timing sessions when gates pass. It rechecks saved raw on resume. A numerical confirmation failure prevents timing and exposes that panel. Further development is authorized, but requires a new candidate epoch and new unexposed confirmation panel. No success-subset timing.

## Flexible resources, not optional stopping

Initial example: 8,192 work credits (6,144 development), finite per-worker timeouts and host-measured memory/disk reservations. This is a generously sized first tranche, not a scientific cap. The agent is authorized to extend it without re-asking the author:

```powershell
python -B "$code/host.py" budget --research-root <shared-root> --limits <new-limits.json> --reason 'Specific next mechanism experiment and expected evidence'
```

The original ledger is never reset. A normal request costs one credit; each extra shadow decode is also charged. Admissions/builds are separately reported, not model observations. Do not extend formal timing because a favorable estimate has not appeared. Failed/partial attempts remain charged and preserved. Safety limits and actual memory admission are always finite.

## Closeout

Deliver a separate result PR: old failure → source/localization → own-path and counterfactual replay → structural fix/ablation → frozen unseen qualification → regressions → complete costs. Include every failed candidate, raw access hashes, remote readback, source/runtime/graph-policy identities and a PAPER_ADDENDUM. Reuse the pinned parent's `archive.py` and delivery tools after reviewing paths and permissions. No manuscript rewrite, main merge, new model family, Strata or arXiv submission is automatic.
