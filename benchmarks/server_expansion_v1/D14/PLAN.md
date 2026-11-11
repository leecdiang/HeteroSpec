# D14 — Qwen3-14B Q8 full-GPU scale and capacity transfer

## Fixed model specification

Target: official Qwen/Qwen3-14B-GGUF, Qwen3-14B-Q8_0.gguf, revision
c75e7b2d0234068f674a1bacf548ea32e27ccd29;15,698,533,728 bytes;
SHA256 a0dfe649137410b7d82f06a209240508e218f32f5b6fd81b69d6932160cfcd9d.
Draft: existing Qwen3-0.6B Q8_0, exact identity in models.json.
Target geometry:40 layers,40 query heads,8 KV heads,head dimension128; validate
actual GGUF metadata. The public configuration is not a substitute for file checks.

Read-only acquisition can start now, coordinated around PR196 timing:

```sh
python3 benchmarks/server_expansion_v1/shared/acquire.py \
  benchmarks/server_expansion_v1/D14/models.json target \
  "$HOME/heterospec-models/Qwen3-14B-Q8_0.gguf"
```

No model loading follows download. Preserve20GiB free after the remaining transfer.
Reuse a matching existing file rather than re-download; never overwrite a mismatch.

## Scientific increment

PR166 already tested14B with partial CPU offload. This is **not first14B support**;
it tests the final method with the entire target and draft on one allocated24GB
GPU, eliminating that placement mixture. It is scale/shape evidence within Qwen,
not another model family. Do not compare old/offloaded and new/full-GPU timings as
an isolated algorithm speedup.

## Staged implementation

1. Bind the actual Linux successor source, modules and Qwen8B method freeze.
   `gguf_inventory.py` and `capacity.py` produce metadata/planning only. At C4096,
   the target+draft file/KV planning base is about16.28GiB; workspace, graphs,
   output, alignment and driver allocations still need real measurement.
2. Perform zero-forward C1024 admission, retaining safety reserves. Observe all
   target/draft layers and KV on the selected GPU, not only n_gpu_layers=999.
   CPU fallback/offload is a different configuration and cannot count as admission.
3. Freeze independent R_14B_C1024 before candidate outputs, preserving whole-prompt
   producer/UB1, F16KV, greedy stop, template and output semantics. Reference does
   not come from an8B model or from the best matching candidate.
4. Apply unchanged shared rules first. Use real exposed code/math/tail/boundary
   cases, including historical14B cases when already available. If a generic
   structural repair is needed, retain initial transfer result, version the repair,
   requalify and report extended rather than zero-change transfer.
5. Qualify all four real target-only M paths and SIMPLE-D4/LOCAL-D4, fixed k3 and
   draft prefillUB4. One target context per method, equivalent graph/lifecycle
   optimizations. Do not omit the stronger mixed M because development is unfinished.
6. Freeze16 existing PR195 Qwen text/token roots as **scale/deployment transfer**,
   four sessions/six arms:384 tests +48 primers. Revalidate native vocab/template
   compatibility; no padding, truncation or favorable acceptance selection.

## C4096 is an independent second deployment

Only after C1024 qualification, configure real C4096 reference and candidate
contexts/output buffers/workspace. Bind actual allocation and modules, not just a
JSON field. Use a finite known-query matrix across q4/q8/q32, inside/crossing/tails;
observe append time after valid state preparation, including synchronization and
output copying. Capacity and active prefix length must be reported separately.

A natural long-input panel is conditional on an unanswered deployment question:
12 prospectively selected native-tokenized long roots (roughly2K-3K tokens while
respecting cap/transient limits), six fixed arms/four sessions:288 tests +48 primers.
Freeze before outputs. Do not manufacture length strata by repetition/truncation.
C1024's scalar outputs are not C4096's oracle; no timing pool across capacities.
If no new question is left, finish the structural qualification and stop that
optional panel rather than running more samples.

## Complete costs and decisions

Report actual target-only residency, startup, request burst, complete service,
phase coverage, measured memory and target/draft physical work. D4 benefits are
application gains, not automatically local-cut gains. Keep every fixed M and
same-k SIMPLE comparator. One failed capacity branch does not erase successful
C1024 work; fix ordinary allocation/ABI faults without reducing reserves to force
success. No new larger draft or tensor parallel. Initial envelope2560 requests/
12M rows; preserve all failed and inherited evidence separately. Deliver an
independent results PR, not a manuscript edit or automatic merge.
