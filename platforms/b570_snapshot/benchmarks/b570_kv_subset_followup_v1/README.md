# B570 boundary-0 KV subset follow-up

**Status: native study COMPLETE; PR remains Draft.** See [RESULTS.md](RESULTS.md), [ANALYSIS.json](ANALYSIS.json) and [causal interpretation](CAUSAL_INTERPRETATION.md). All 32 controls pass, all 160 subset requests complete, all 80 independent repeat pairs agree, and scientific failures/retries are zero. Final local raw archive restoration and CPU reanalysis pass; raw archive remote publication is not performed.

The following implementation description predates host execution; original synthetic validation remains separate evidence. This PR includes executable CPU preparation, a Windows adapter to the pinned PR101 worker, CPU result analysis and synthetic tests. The new host results and local restoration certificate are added separately under this benchmark directory. The local synthetic suite has 16 test methods; passing it does not establish native import correctness.

## Scientific question and fixed scope

Can an explicitly selected subset of boundary-0 K/V values reproduce, remove or change the suffix difference between historical full versus partitioned prefill? The baseline is PR101 commit `26706c9fb4818ec3465e45acea029c4ab88a390f`, not whatever happens to be at main. Use its restored `code/`, `build/Release/`, `baseline/pr99/`, donors and model prerequisites. PR101 is not merged by this PR.

The four fixed, **previously exposed** inputs are GSM8K/test/1248, /831, /1011 and /1249. The first two are historical affected inputs; the last two are stable controls. This is not new-input validation. Both donor directions retain recipient initial logits, empty committed prefix, native greedy sampling, first pending token consumed once and the existing clean UB512 receiver. Import and exact reserialization are checked by the unchanged native worker.

Primary selectors: `K_layer0`, `V_layer0`, `KV_layer0`. Prespecified descriptive selectors: all K, all V, KV layers [0,8), [8,24), [24,32), positions [0,128), and positions [128,N). The position cutoff follows the inherited partition, not a proposed universal threshold. Transposed V is feature-major; the implementation selects token positions using its actual serialized layout, not contiguous row assumptions.

Every selected reconstruction first passes a byte-identical own-source CPU sham. Because these shams produce the same entire state bytes, the native EMPTY receiver controls cover the shared import path; they are not falsely counted as 80 additional native sham experiments. Then **32 native controls** (4 tasks × 2 recipient directions × EMPTY/ALL × 2 independent processes) must all match the corresponding immutable historical full endpoints. Only then may **160 subset crosses** run (4 × 2 × 10 × 2). All inputs, selectors, order, source bodies, runtime and model hashes must be remotely registered before the first new native request.

Hard budget: **192 whole native request starts, including failures; no scientific retries; 6 hours cumulative owned GPU-process time**. Each request uses a new worker process. A 4 GiB output-size admission check runs before each request; it is not a continuous filesystem quota. Preserve incomplete and failed attempts. The adapter must never terminate unrelated processes. No new model family, quantization, speculative budget, numerical DLL, shader or paid-cost study is authorized.

## What the code does

`prepare` validates fixed Git blob identities, parses source-defined state metadata, splices only selected value bytes, emits immutable CAS payloads and records selected versus actually changed bytes. `run` authenticates the freeze against a specified full Git commit and GitHub bytes, then reuses the original worker's module identity, same-PID memory checks, no-forward import, native endpoint and continuation geometry. `analyze` reconstructs the prescribed mixtures again and rechecks raw result/trace hashes using the pinned independent PR101 auditor. This is not a wholly separate reimplementation of that auditor.

Allowed outcomes include a structural null (no bytes changed), a valid endpoint null despite changed bytes, donor-endpoint reproduction and a third valid trajectory. Report both repeats and both directions. A failed own-path gate invalidates causal claims; a valid null effect is not a failed experiment. Layer-0, role, region and whole-KV results must remain distinct. These interventions do **not** establish a unique projection kernel, complete mediation from a projection perturbation, or natural reachability of mixed states. No speedup claim is authorized.

## Host execution

Use a new worktree on this PR branch and a separate run directory. Never patch the inherited PR101 archive. Python >=3.11; do not use `-O`. Git and authenticated `gh` are required for the freeze readback. The baseline path below is the historical host path; substitute an independently restored equivalent only when the source/model/runtime gates pass.

```powershell
cd benchmarks/b570_kv_subset_followup_v1
python -m unittest -v
python experiment.py prepare --baseline "C:/Users/DIANG/Documents/ChatGPT/HeteroSpec/work/b570-final-causal-closeout-v1" --out "C:/hs/b570-kv-subset-v1"
```

Before any GPU start, independently inspect the generated PLAN, RECONSTRUCTION and FREEZE, check actual driver/runtime identity and available disk, and validate the Windows adapter with the inherited sources. Resolve an integration defect only through an explicit pre-execution amendment; do not change a started experiment in place. Commit the exact generated `FREEZE.json` to `benchmarks/b570_kv_subset_followup_v1/registration/F0.json` on this new branch and push. Use that full commit SHA for both stages. The local copy and authenticated remote bytes must match. Keep secrets and model weights out of Git.

```powershell
# Replace COMMIT and the repository path with the actual registered values.
python experiment.py run --out "C:/hs/b570-kv-subset-v1" --repo "C:/path/to/new-worktree" --freeze-commit COMMIT --registration "benchmarks/b570_kv_subset_followup_v1/registration/F0.json" --stage control
# Read ANALYSIS-control.json. Cross execution itself also requires all 32 controls.
python experiment.py run --out "C:/hs/b570-kv-subset-v1" --repo "C:/path/to/new-worktree" --freeze-commit COMMIT --registration "benchmarks/b570_kv_subset_followup_v1/registration/F0.json" --stage cross
python experiment.py analyze --out "C:/hs/b570-kv-subset-v1"
```

A stale execution lock, failed load/request or incomplete started slot is evidence to investigate, not permission to delete/retry a scientific coordinate. Analysis recomputes large state mixtures and may take appreciable CPU/disk time. The original implementation author had not exercised host-native execution; this follow-up records the completed native host validation separately.

## Agent handoff and acceptance

Complete this specific bounded experiment, not a new search for a positive result. Keep the PR in Draft. After host integration review and registration, execute controls before crosses, retain every attempted slot and raw native output, and provide a separate result summary with the control gate, all subset/direction/repeat endpoints, changed-byte counts, first difference from recipient, elapsed owned-process budget and explicit blocked capabilities. Seal and restore the new evidence in a fresh directory; independently compare the reconstructed raw bytes and rerun the CPU analysis before calling the result archived. Do not claim the current synthetic tests are that restoration.

Modify only this new benchmark directory and this branch. Do not edit/merge PR100/101/102, main, manuscript, arXiv, Zenodo, releases, licenses or existing result archives. Original R_stock qualification failures and NULL qualified costs remain unchanged.
