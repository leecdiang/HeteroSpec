# B570 producer × consumer boundary experiment

**Native extension implemented and compiled; native qualification is pending.**
No new model/GPU request has yet been executed. See [IMPLEMENTATION.md](IMPLEMENTATION.md)
for the new driver and bounded executor, and [INPUT_SOURCE_AMENDMENT.md](INPUT_SOURCE_AMENDMENT.md)
for the visible pre-forward input-source revisions and retained static stops.

This experiment asks whether Qwen3 producer state changes the reference that a local PQ/QB consumer can preserve. It builds on the completed PR148 native reproduction and PR150 delivery; it does not repeat delivery or promise a speedup.

## Fixed scope

- Base: PR150, `9f03bead68462326497b03edb0d2d80f8f2fd4c3`.
- Target/draft: exact Qwen3-8B / Qwen3-0.6B Q8_0, both B570 Vulkan, 8threads, F16KV, FAoff.
- **152 primary full model requests**: B0=32 historical control/sham requests; B1=8 new inputs×15=120.
- Producer: P1 serial caller; P4T width4 with a frozen tail3→2+1 rule.
- Consumer: C1 target-only, or original k1 speculation using PQ/QB q2.
- B1 includes a separate strict UB1/output1 R per input, natural producer C1, own-path C1 restore shams, and PQ/QB off/on cross-cells.
- B0 additionally requires natural-vs-resumed PQ and QB own-path checks on both historical controls. A C1 restore check alone is insufficient.
- The main causal endpoint is explicitly a **boundary0 clean-receiver contract**. P4T failure is not automatically a failure of an untested natural production path.
- No formal timing, new q4 operator grid, cost model, KV×logits decomposition, or automatic model retry.

`plan.json` preserves the original deterministic **DRAFT_UNBOUND** inventory of all152 coordinates. It is not an execution plan or result. The new executor requires a separate bound `FROZEN_PLAN.json` after static input selection and actual runtime hashing. `CONTROL_INPUTS.json` contains the real immutable HumanEval/38 (181IDs) and HumanEval/115 (349IDs), both original cap64. New inputs use cap128.

## What is implemented here

`work_package.py` is a Python3.11+ stdlib CPU tool. It creates/validates the exact152-slot matrix and verifies record structure, frozen identity fields, complete endpoint/EOG rules, k1 cycle conservation, row inventories, donor identities, actual restored KV/initial payloads, observer/own-path comparisons, B0 dependencies, missing/failed coordinates, and raw payload hashes. Restored-boundary qualification requires actual payload rehash; metadata-only records cannot open B0. Nonterminal k1 acceptance must commit its bonus, while a genuine cap/EOG terminal acceptance may omit it.

It **never invokes a compiler, native executable, model, GPU, network request, or remote write**. Its audit-controls subcommand independently compares new natural B0 records with the delivered PR148 complete vectors, cycles and per-decode geometry. This numerical comparison does not claim historical binary/context identity or a second-machine native run.

Files:

| File | Purpose |
|---|---|
| `PROTOCOL.md` | Scientific question, estimands, complete matrix, interpretation and stop conditions |
| `HOST_HANDOFF.md` | Existing callable commands versus the explicitly unimplemented native extension |
| `SOURCE_PINS.json` | Actual source paths, immutable commits/Git blobs and SHA256 |
| `CONTROL_INPUTS.json` | Existing exact native control IDs and cap64 |
| `INPUT_PANEL_TEMPLATE.json` | Eight real new inputs must be bound before forward; no placeholder may execute |
| `RUNTIME_TEMPLATE.json` | Actual new build/vocabulary must be bound before forward |
| `plan.json` | Current draft152-slot inventory; all new results null |
| `work_package.py` | CPU generation and record validation |
| `test_work_package.py` | Synthetic CPU contract tests, not model results |
| `CPU_VALIDATION.json` | Only the CPU commands actually run while preparing this PR |

## Immediately callable CPU commands

Run from the repository root:

```powershell
$work = 'benchmarks/b570_producer_consumer_boundary_v1'
python "$work/work_package.py" validate-plan "$work/plan.json"
python -m unittest discover -s $work -p test_work_package.py -v
python "$work/work_package.py" verify-source --checkout .
```

`verify-source` checks the explicitly listed PR150 source files against this checkout. It does not claim a full upstream rebuild or revalidate old experiments. A checkout without the stacked PR150 files will report those exact missing paths.

To regenerate a draft into a **new** path:

```powershell
python "$work/work_package.py" make-plan --out C:/hs/b570-boundary-new/draft-plan.json
```

After completing static input selection, bind real copies of the two templates using `execute.py freeze` (see IMPLEMENTATION.md). The lower-level builder checks eight unique token sequences, four inputs per length band, exact caps/model identity, and actual build/vocabulary fields:

```powershell
python "$work/work_package.py" make-plan --panel C:/hs/b570-boundary-new/INPUT_PANEL.json --runtime C:/hs/b570-boundary-new/RUNTIME.json --out C:/hs/b570-boundary-new/FROZEN_PLAN.json
python "$work/work_package.py" validate-plan C:/hs/b570-boundary-new/FROZEN_PLAN.json
```

This freezes a plan; it does not execute it. B0 still must pass before B1.

As the host appends **one final disposition per started or explicitly not-run primary slot**, first audit the historical natural controls, then audit the saved records:

```powershell
python "$work/work_package.py" audit-controls --plan C:/hs/b570-boundary-new/FROZEN_PLAN.json --records C:/hs/b570-boundary-new/REQUESTS.jsonl --reference-root $referenceRoot --payload-root C:/hs/b570-boundary-new/raw --out C:/hs/b570-boundary-new/CONTROL_AUDIT.json
python "$work/work_package.py" validate-records --plan C:/hs/b570-boundary-new/FROZEN_PLAN.json --records C:/hs/b570-boundary-new/REQUESTS.jsonl --payload-root C:/hs/b570-boundary-new/raw --control-audit C:/hs/b570-boundary-new/CONTROL_AUDIT.json --report C:/hs/b570-boundary-new/CPU_AUDIT.json --require-complete
```

Omit `--require-complete` for a progress audit. Missing coordinates are listed as missing; they are never filled with fake PASS/NOT_RUN records. `--require-complete` means every coordinate has an explicit final disposition, not that every experiment succeeded. Numerical counterexamples and no-trigger outcomes remain valid scientific results; failed shams prevent dependent causal claims.

Output files are created exclusively: use a fresh filename for each report. There are no automatic retries. A technical rerun needs a separately recorded amended plan/attempt inventory and must not overwrite the152 primary records.

## Present limitations

The new driver is `boundary.exe`; the existing `formal.exe` still accepts only the historical four-input qual triplets and cannot execute this design by changing CLI flags. A successful compilation and CPU tests do not establish native qualification. Only the independent native B0 audit can open B1.

The input-source amendment preserves the two length bands and the fixed count of8. Scientific factors are producer×consumer. Length and domain are selection descriptors; impossible domain×length cells must not be manufactured with truncated/concatenated prompts. If the final census cannot support the8-input plan, stop before new forwards; do not change152 slots during execution.

All new result fields are null. Historical references remain unchanged.

