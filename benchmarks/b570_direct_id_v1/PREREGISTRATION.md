# B570 direct-generated-ID qualification replication v1

This is a new, prospectively frozen replication with known historical outcomes,
starting exactly from main `483c4cbd6cd72ae1cdcdbba4534a62fc1786f885`, on branch
`experiment/b570-direct-id-qualification-v1`. This is not blinded discovery.
Historical B570 materials remain closed and unchanged.

Historical fast 45/90 (15/30 wholly matching prompts) and serialized 60/90
(20/30) were prompt-stripped/count-normalized re-tokenized-text agreement.
They are not direct generated-ID certificates. Historical fast V2 at 512/2048
was about 1.2426/1.6373; serialized V2 about 1.9827/1.9917. These known
observations cannot override this study's direct-ID endpoint.

## Frozen execution paths

Use llama.cpp b10839, upstream
`0cae43063cf15170e91a2ff4d034da0ecef4a1b2`, with the committed observational
instrumentation patch. Use Vulkan0 / Intel Arc B570, full target 37/37 and
draft 29/29 offload. No AUTO/HETERO/CPU model-layer fallback.

- TARGET_REFERENCE: llama-completion, batch 512, ubatch 128, no draft.
- B570_FAST_K2: llama-speculative, batch 512, ubatch 128, draft k=2.
- B570_SERIALIZED_K2: same speculative command with ubatch 1 as its sole
  intended execution-path difference from B570_FAST_K2.

Common settings: greedy, temperature 0, top-k 0, top-p 1, min-p 0, seed 123,
context 1024, flash attention off, maximum 128 semantic generated tokens.
Preserve historical CLI n-predict 128 for completion and 127 for speculative.
Models are Qwen3-8B-Q8_0 target and Qwen3-0.6B-Q8_0 draft with the frozen
authoritative hashes listed in protocol_v1.json. The dataset hash is
`b796127e635a67f93fb35c04f4cb03cf06f38c8072ee7cee8833d7bee06979ef`.

## Direct-ID endpoint

Record actual final committed generated token IDs, excluding prompt and
uncommitted draft candidates by instrumentation location. Preserve the entire
raw committed-ID stream and its runtime EOG flags in a sidecar. Compare the
first 128 IDs, or terminate at and include the first runtime EOG token when
earlier. No output text is tokenized again for the primary endpoint.

b10839 may finish a speculative verification block beyond its CLI budget.
The observational sidecar retains any extra IDs. Applying the common maximum
128 to an array of actual committed IDs does not change runtime execution or
stop conditions. R0 must confirm this mapping before formal execution.

R0 uses the fixed six sanity prompts (3, 10, 19, 20, 106, 129), original versus
instrumented text-byte checks for all three paths, fresh-process repeated
request checks, and a separate forced-EOG mechanistic probe. Its results
qualify the instrumentation only; they are not formal study observations.

## Workload and schedule

Exactly the 30 historical HumanEval IDs listed in protocol_v1.json, three
repetitions, all three conditions: 270 executions. Iterate frozen prompt order
within each repetition; randomize condition order within each prompt x
repetition using Python Random seed **20260928**. Save the complete schedule
before formal execution. No prompts or mismatches are selectively rerun.

Compare both candidates to TARGET_REFERENCE within each block: 180 direct-ID
pairs, 90 per candidate. A prompt is wholly exact only when all three paired
repetitions are exact. A path is **QUALIFIED only at 90/90**; any lower count is
**BLOCKED**. Record first divergence, both token IDs, both sequence lengths.
Continue the entire schedule after true mismatches. Operational, provenance,
offload or parser failure invalidates the attempt and retains all evidence.
Any semantic repair after freeze requires a new protocol version.

## Provenance, validation and closeout

protocol_v1.json, BUILD_ENVIRONMENT.json, instrumentation.patch and
FREEZE_MANIFEST.json record complete commands, upstream/source HEAD,
instrumentation hash, all binary and DLL hashes, driver/device environment,
models/dataset, schedule and runner/verifier file hashes. Commit these before
formal data starts. Record the resulting study HEAD in each execution.
No code, parameter, driver, model or branch changes follow that freeze.

Independent verify.py must check 270-run coverage, raw hashes, direct arrays,
model/dataset/binary provenance, offload/device evidence, all 180 comparisons,
counts and divergence positions without importing the primary comparator.
Publish FORMAL_ANALYSIS.json, FORMAL_REPORT.md and CLOSEOUT.md and a
content-addressed, hardware-free-verifiable evidence bundle under
artifacts/b570_direct_id_v1/ with raw sidecars and stdout/stderr.

Operational elapsed times may be retained for execution monitoring. Energy is
out of scope; no PresentMon, V2 campaign or historical performance/energy
reanalysis is authorized. No further candidate, ubatch, k, context, model,
quantization, flash-attention or backend search. No manuscript, Figure 3 or
historical figure CSV edits. Integration awaits joint review with the
independent RTX arm. Open a draft PR and do not merge automatically.
