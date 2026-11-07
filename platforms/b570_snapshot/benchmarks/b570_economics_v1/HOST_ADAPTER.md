# Original-host integration contract

## Restore once; no work on frozen originals

Use PR187's already restored `secondary-smol/campaign02` and pinned source/model
manifests. The inputs to `stage_costs.py` are ONE frozen arm's frontend folder
with `observer.h`, `native.cpp`, `target.cpp`, `CMakeLists.txt` plus its headers.
Create a pins JSON `{ "receipt": "actual freeze path + SHA256", "files":
{"observer.h":"...", "native.cpp":"...", "target.cpp":"...", "CMakeLists.txt":"..."}}`
by checking against the published execution freeze, not by blessing arbitrary bytes.

```
python stage_costs.py --source RESTORED_ARM --pins bound-sources.json --out FRESH_MODE0 --mode 0 --active target
python stage_costs.py --source RESTORED_ARM --pins bound-sources.json --out FRESH_MODE1 --mode 1 --active target
python stage_costs.py --source RESTORED_ARM --pins bound-sources.json --out FRESH_MODE2 --mode 2 --active target
```

Use `--active target` for M and `--active native` for speculative arms. Each
actual PR187 arm froze its measured frontend with the full-service clock; the
unused companion can retain its earlier clock. The stager authenticates both
source files and instruments only the selected frontend. Its active full-service
clock check remains mandatory; never relabel the unused legacy clock.

The new frontend must link the same original numerical DLLs for Stage A.
Bridge mode0 against the untouched frozen executable; it must preserve output
masks, target vectors/state/frontier, cap/EOG and request lifecycle. Mode1 adds
host clock calls but no synchronization. Mode2 adds explicit boundary drains and
is a separate synchronized diagnostic, not the clean benchmark.

The patch covers `observer.begin/end` because M uses direct
`common_prompt_batch_decode` and bypasses `observer.decode`. A missing anchor is
an engineering task: inspect frozen descendants, update the stager with a narrow
source diff and tests, re-bridge. Do not remove the check or substitute a different R.

Current draft continuation may combine logical sync/proposal in one native call.
The default reports `draft_continuation_unsplit`. At genuine separate caller
sites, add dedicated scopes; if they cannot be separated without changing work,
report the combined time and null separate fields. Never invent two components.

## Resident integration

```
python stage_resident_core.py --source PINNED_LLAMA --pins bound-core.json \
  --out FRESH_OVERLAY --widths 1 128
```

`bound-core.json` uses SHA256 keys `src/llama-context.h` and `.cpp`, tied to the
actual selected reference family. Stage B initially reuses the old phase widths;
Stage C can explicitly add supported verification/prefill widths in a NEW overlay
and candidate identity. The setter only synchronizes, updates capacity and invokes
scheduler reservation. It does not install F32/p021/extent policies by itself.

Build a private candidate core from recovered source; keep old R independent.
Bridge unchanged arithmetic and effective flags first. Resolve the new C export,
abort/poison on nonzero return. Keep the live sampler and positioned pending token;
sample the already-live prompt frontier once before a phase transition. Never
resample missing restored logits or decode the terminal token to make KV look full.

Port the caller/graph policy from existing qualified phase/scoped source (PR64,
PR165 and PR169) as needed. Numerical mapping is based on actual type/stride/head
geometry, cache occupancy and dispatch, not a model label. SIMPLE and LOCAL share
all legitimate arithmetic fixes and graph reuse improvements. SAME target state,
no online full-state export/import or oracle on supported clean resident transitions.
Do not simply set HS_NO_TRANSFER: that may retain the wrong phase arithmetic.

Record actual context/KV ownership, scheduler-plan rebuild/reuse, required output
rows and capacity. Graph identity includes numerical policy, physical extents and
relevant stride/shape. Metadata equality is not a proof of numerical equality.

## Physical-work observations

Count unique occupied target micrographs, rows per micrograph, actual verify
requests, proposal/accepted/correction tokens, and host/device synchronization.
Do not count every layer's `embd` callback as a new forward, or call width2 a
physical width2 without an actual scheduler observation. Use a separate
mechanism run; profiling/dumps are absent from clean service. Optional timestamp
queries are permitted only on a diagnostic copy and remain separate from host time.

## Reference and evidence reuse

Reuse PR187's autonomous original R, independent forced-prefix bank, active-state
codec and observer/off checker. Requalify the NEW candidate's actual trajectories.
Keep the current requested-output flags, source-derived layer map, frontier row,
accepted/correction/bonus/EOG/cap branches and positioned unmaterialized suffix.
Use artificial branch cases only as separately labelled protocol coverage.

Use PR187's Job-object supervisor and durable request/row reservations. Exposed
input selection is structural and fixed before this new pilot; blind roots are
not used for implementation choices. Actual dependencies, manifests and commands
belong in a compact receipt. Do not rebuild another audit system or duplicate the
entire old raw archive. Preserve original receipts and lossless evidence needed
for new claims; chunk/reuse existing objects once.
