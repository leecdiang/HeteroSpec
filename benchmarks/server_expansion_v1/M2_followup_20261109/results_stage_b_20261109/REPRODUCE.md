# Saved-data replay and native reconstruction

Use the immutable result commit and the same published part/index files together.
Node18+ and Python3.10+ built-ins suffice for saved-data replay; no model or GPU
is used. From the repository root:

```sh
node benchmarks/server_expansion_v1/M2_followup_20261109/stage_b/assemble_archive.cjs \
  benchmarks/server_expansion_v1/M2_followup_20261109/results_stage_b_20261109 \
  /path/to/FRESH-bundle
python -B benchmarks/server_expansion_v1/M2_followup_20261109/stage_b/record_adapter_v2/replay_archive.py \
  --bundle /path/to/FRESH-bundle --out /path/to/FRESH-replay
node benchmarks/server_expansion_v1/M2_followup_20261109/stage_b/analyze_saved.cjs \
  /path/to/FRESH-bundle /path/to/FRESH-analysis
```

Compare CHECKED.json and DIAGNOSIS.json. Replay reconciles native receipt scalars,
32 qualification commitments, frozen oracle identities, physical counters and
costs. It does not reproduce original host clocks or prove GPU numerical equality
from hashes alone. Public readback and original private capture availability are
separate claims.

Native reconstruction starts with the exact Linux reference and numerical
archive closure in [M2/REBUILD.md](../../M2/REBUILD.md) and its source packet.
Read the original Linux environment/protocol
first. A new host needs its own independent R and allocation; public redacted
receipts are not a transferable scheduler allocation or ready-made private path.
Do not use Windows libraries, upgrade upstream, replace GGUF hashes, relax
criteria or reset the original cumulative budget on the retained host.

The actual source sequence is retained under pr210-stage-b-source-* in the text
bundle. Source02 builds the two frontends via build.py, copying the exact M2
frontend preamble and appending equalwork_main.cpp, against the fully built and
hash-checked original numerical archives. BUILD_PUBLIC.json commits generated
files, binaries and dependencies. Driver05 explicitly registers four full R
replays, three extensions and four scalar trunks. Historical formal captures
are absent, so newly replayed endpoints and payload bridges are required. R0
from completed attempt04 is reused after its complete commitment checks; it is
still charged. This is retained-host history, not a claim that a fresh host can
invent that operand or reuse its old counter.

All32 heavy candidate cells must pass before the immutable TIMING_PLAN.json is
written. Actual timing jobs, strings, counters, resources and modules are in the
archive. Use only the record_adapter_v2 repair for the retained duplicate-field
postprocessing error: it keeps exact slots and never repeats a reserved worker.
Numerical source/binaries and criteria do not change. A different parent failure
does not admit that adapter.

The detached supervisor's archive-log collision is retained as a failure; no
native work was lost. Actual closeout03 ran archive.py and replay_archive.py in
fresh directories. stage_b/finalize.py now provides this data-only recovery with
unique caller-supplied output/log paths, after verifying native completion and
absence of exact-study workers. Preserve the previous failure and all source
epochs. Native qualification cannot be inferred from a successful finalizer.
