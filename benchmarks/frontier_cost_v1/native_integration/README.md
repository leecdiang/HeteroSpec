# Native request integration for the deferred draft tail

This is an implementation check of the actual HeteroSpec worker's `provision` and
`request` functions. The CPU harness includes the unchanged candidate worker and
uses its real draft sampling, target verification, acceptance, correction/bonus,
termination, trim and resident-reset code. It is separate from the original
guarded production command-line entry. No GPU performance or production-model
qualification is claimed.

## Recorded result

The final matrix completed **32 request pairs / 64 CPU requests** using the fresh
numerical build supplied by the preparation workflow. Independent byte comparison
passed for **552 complete frontend-read vector pairs and 272 native sequence
pairs**, totaling 76,633,984 bytes per side. The deferred arm omitted 29 last q1
calls and recovered 19; each request's actual draft-call difference exactly equals
its omitted count.

Actual coverage was: 20 CAP and 12 EOG requests, including four initial-CAP and
four initial-EOG stops; eight all-accepted terminal cycles, twelve shorter accepted
terminal cycles, two bonus-terminal cycles and seventeen correction cycles. The
same resident contexts were reused across 28 dirty-reset boundaries, and four
requests crossed the 256-cell physical extent boundary. These counts are from the
executed receipts, not merely from the fixture design. See `RESULT_SUMMARY.json`.
One earlier single-request implementation preflight is retained separately: the
module executed 65 synthetic CPU requests in total, of which 64 belong to this
final paired matrix. It performed zero GPU requests.

The independent reviewer read every raw pair, recomputed argmax, and reconstructed
acceptance, stop reason, correction/bonus and retained frontiers using another
literal walker. That audit also passed; it did not import the implementation's
comparator or execute another model. `INDEPENDENT_AUDIT.json` records its bindings
and complete counts. Its source is in the parent `review/` module.

## Source and entry boundaries

The candidate worker SHA256 is
`05e395aa3082b08229946139c1f0d298bfc1c3064f001ba5c10aefcc9487eecb`.
Its shared tail helper SHA256 is
`8602ac1e2ad93972d36ff8fc3f7dca5e16c0a8385ac058bd1b367331f6c2f62f`.
The build script rejects other bytes and records the rest of the frontend,
numerical libraries and harness identities. The two CPU executables differ only
in the explicit `HETEROSPEC_DEFER_DRAFT_TAIL=0` or `=1` build definition.

The F32 scope is deliberate. The source kit marks certain wide Q8_0 matmuls for
its CUDA loop4 backend and rejects those marked operations on CPU. That backend
restriction is preserved. F32 request-function success does not qualify the
quantized production path or transfer the earlier Q8_0 controlled-probe result
to this complete request harness.

`guarded_entry_eager` and `guarded_entry` compile the original M2 `entry.cpp` with
those two definitions. That entry still requires a real GPU and its original M2
contract. The CPU experiment records the expected `GPU required` failure rather
than weakening the gate or fabricating an old production binding. These two
native-entry builds are candidates, not qualified production binaries.

`cpu_request_0` and `cpu_request_1` are a new, explicitly synthetic CPU harness.
They call the worker's request function in the existing counts-observer mode.
The GPU-only placement observer is therefore not used. Actual target/draft
physical microbatch sizes are recorded and checked as 32 and 4, with output
reserve 8 and context capacity 1024. They do not inherit qualification from the
earlier controlled-frontier probe, whose target microbatch was different.

## What is observed

The harness saves native function pointers before its local include-time
wrappers. The shared numerical libraries are unchanged. Wrappers only:

- Copy every complete vector actually returned by `llama_get_logits_ith` to the
  worker or its `PhaseContext`, retaining context role, row and call order.
- Capture the active native sequence after each real trim and reset, and at
  request end, for both target and draft.
- Record dense-cell geometry and call the original append guard to check the
  next position, allocator head and extent requirements.

The eager arm's unused final draft-logit buffer is deliberately not added to the
comparison: no frontend read requests it before the next seed sync overwrites
it. The claim is complete frontend-read target/proposal vectors, active sequence
bytes, geometry and subsequent request behavior. Native sequence serialization
is not a whole-context memory image and does not cover inactive padding or every
private field.

State capture synchronizes and writes data inside the CPU request. All recorded
times are instrumented diagnostics and are excluded from performance conclusions.
The comparison checks complete logical receipts and the precise expected native
call-count difference, while excluding timing fields and unused buffer contents.

Actual loaded `libllama*.so` and `libggml*.so` modules are inventoried and hashed
before and after requests. The set must exactly match the four bound numerical
libraries. An extra ISA-specific CPU plugin is rejected rather than silently
used. The runner fixes `LD_LIBRARY_PATH` and `GGML_BACKEND_PATH` to the supplied
library directory and removes preload/audit overrides. The CPU harness refuses
an enumerated GPU backend; it is not the remote GPU qualification runner.

## Fixed synthetic matrix

The fixture generator creates two untrained F32 variants of one small Llama
architecture: two layers, 256 embedding dimensions and 128 vocabulary items.
Both retain nonzero random attention and feed-forward weights. A dominant output
projection makes one variant follow a simple token transition and the draft
variant occasionally disagree. These are designed test fixtures, not additional
real task-model families.

The GGUF files contain an explicit SPM token list, types, scores and EOS ID 127.
The native vocabulary reports EOS and the unchanged worker calls
`llama_vocab_is_eog`. No wrapper overrides EOG or replaces sampled token values.
Requests use explicit token IDs; text tokenization is not tested.

The plan fixes target-equals-draft and mismatching-draft relations at k3 and k7.
Each cell contains eight requests: initial CAP, short accepted CAP, all-accepted
CAP, bonus CAP, multiple cycles, all-accepted EOG, short accepted EOG and initial
EOG. Prompts include lengths 7, 248, 253 and 257. All acceptance and termination
coverage is counted from the actual receipts after execution; designed fixture
transitions are never used as substitute model outputs.

`PLAN.json` is written before the matrix starts. There are 32 request pairs, or
64 actual CPU requests, with a fixed 120-second process timeout. Missing required
coverage, any vector/state mismatch, incorrect call saving, a module change or an
unexpected process exit produces a retained failure. Output directories are new;
there is no automatic retry or overwrite.

## Reproduction

Obtain the authenticated source kit, reconstructed frontend and unchanged CPU
libraries using the parent directory's preparation workflow. Supply their actual
paths explicitly; the code does not depend on a particular workstation path.

```sh
python build_integration.py \
  --core "$HETEROSPEC_CORE" \
  --frontend "$HETEROSPEC_FRONTEND" \
  --lib-dir "$HETEROSPEC_CPU_LIBS" \
  --out build_fresh

python make_integration_fixture.py \
  --gguf-python "$HETEROSPEC_CORE/gguf-py" \
  --out fixture_fresh

python run_integration.py \
  --build build_fresh --fixture fixture_fresh \
  --lib-dir "$HETEROSPEC_CPU_LIBS" --out run_fresh

python compare_integration.py run_fresh --out comparison_fresh.json
```

The builder requires a C/C++ compiler; the generator requires NumPy and the
source kit's `gguf-py`. The comparison uses Python's standard library. Source,
binary, model and module hashes belong to the particular run. Rebuilding creates
a new binary identity until explicitly compared and qualified.

## Remote follow-up

For the original GPU entry, build both macro modes against the new frozen CUDA
numerical-library identity. Use the real model/tokenizer manifest and a newly
allocated device and experiment scope. Neither the old S3 execution budget nor
its reference captures are inherited. GPU numerical qualification must precede
timing, and both comparison arms must share any subsequently qualified common
engineering repair. This CPU module does not launch SSH, rent a GPU, modify
drivers or submit a remote job.

## Packaging

Source, fixture generator, comparison tools and compact verification receipts can
be reviewed in the repository. Model weights, raw state/vector captures, binaries
and build caches remain outside the GitHub source tree. A separate evidence
archive contains the new fixture/capture files needed for byte-level replay.
Build failures and the one-request implementation preflight are retained as
separate attempts and do not increase the final matrix's request count.
