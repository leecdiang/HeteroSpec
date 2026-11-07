# Decisions before G0 completion and formal freeze

The native path remains the pinned b10839 CLI/server implementation. It is rebuilt
additively with metadata capture and context replacement; the original CUDA DLLs
remain byte-identical. Full original/instrumented baseline qualification is required.
The H path remains the independent V4 P/R orchestration and the pinned DLL samplers.
R is the original released CLI, unchanged. Source/destination contexts and the source
post-sample sampler are retained through teardown. Source sample is accepted exactly
once before replacement; the continuation sampler is a post-accept clone.

Native draft sampling calls common_sampler_sample to populate top-k probabilities,
then overwrites its returned distribution draw with candidate0 after descending
probability sort. This is preserved, including default-seed behavior. Raw overwritten
draw IDs/scores are retained. The plain/sham behavioral comparison uses actual sorted
proposals (verify_decision), target selected IDs/scores, top draft scores, caller
tokens/positions/masks, graph observations and rollback positions. It does not assert
equal overwritten random draws or opaque sampler bytes. Event sequence, loaded-module
paths and transfer-only bookkeeping are excluded from paired trace comparisons.
H captures preserve actual selected proposal IDs/scores. Legacy full-logit payloads
are retained as binary blobs; new full pending logits and KV state witnesses are
retained. No omitted logit bytes are called independently byte-checked.

Official sanitized MBPP is a JSON array of427 rows, with257 IDs in the test-range
intersection. Static audit conservatively excludes matching descriptions and duplicate
descriptions. Before any new-task forward, SHA256 ordering selected engineering
460,433,162,445,82,294 and formal
310,91,267,273,438,257,444,89,68,463,304,65,456,17,266,224,394,283,86,305,246,268,164,419.
No reference code or tests enter prompts. The exact template, tokenizer IDs, exclusions
and inspected project/archival scope are recorded. New means no known execution
exposure within that checked project scope, not absence from model training.

The local run root is work/rtx-target-v1 within the dedicated D: checkout. Model
weights and external runtime binaries are never uploaded. The experiment retains
their identities and explicitly limits what offline archive checking can authenticate.

Raw runtime evidence revealed that the historical native templates omit --threads
and actually select12 threads, whereas their descriptive document states24. The
initial original/native-sham qualification retains that actual default (120 arrays,
30 pairs, including10 early original arrays), not a claimed24-thread run. This new
study explicitly supplies --threads24 and --threads-batch24 to every native command.
Before freeze,75 native qualification arrays are executed again under that setting;
the45 identical H-path arrays remain valid and are reused with their exact paths.
The effective G0 denominator is120 arrays/30 pairs; the extra75 arrays and earlier
default-thread qualification remain separately identifiable. FormalR stays the
released UB1 CLI with unchanged prefill/sampling/endpoint, with the explicit scalar
thread setting required by the new specification. No historical arrays are edited.

Preparation failure retained: first build reached source reading after the three
small frontends compiled, then Python's Windows GBK default rejected the UTF8
upstream source (UnicodeDecodeError, position14123). Source reads were changed to
explicit UTF8 before native compilation or formal freeze. Build command attempts
and logs remain. The first full-history fetch was cancelled after stalled transport;
an isolated filtered exact-base clone/worktree supplied the verified source instead.

Pre-freeze recovery comparison failure retained in PREPARATION_STOP_01.json. The
controller restart left one /18N_sham-r2 attempt incomplete after four trace events.
Resume retained that attempt and produced a complete second attempt. The comparison
helper incorrectly concatenated both attempts; direct raw inspection shows the two
selected complete plain/sham attempts are exactly equal under the declared predicate.
Before freeze, both qualification and independent audit were corrected to select
the successful attempt bound by result.json.files. Abandoned bytes and the failing
helper versions remain in preparation-history. This is a bookkeeping repair, not
rerunning a scientific disagreement or changing historical expected arrays. Draft
PR53 initially records the stop and will be rewritten around the final delivery.

Final pre-freeze audit strengthened independent checks for all exact645 cohort/condition/repetition keys, protocol/cohort/asset result bindings and actual H target37/37 and draft29/29 GPU offload. Delivery transports CAS parts in bounded pushes and rewrites the existing Draft PR around the final results. Independent verifier and delivery are executed from disk after freeze; neither is imported in the active qualification controller. No numerical frontend or qualification predicate changed.

The resolved preparation stop is retained as STOP_REASON.pre-freeze-01.json and PREPARATION_STOP_01.json. The CAS archive includes an explicit pre-archive report snapshot; final archive/readback receipts and final report are later Git objects whose exact bytes are separately verified, avoiding a circular report/archive hash claim. No formal work has started at this edit.
