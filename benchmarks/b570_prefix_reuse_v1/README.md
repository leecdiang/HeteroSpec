# B570 native prefix reuse execution

This result branch starts at PR173 design head
`bba256cf04bbd2038029fd59447df9722b24c197`. Its scientific ancestor remains
PR169 `8ca17478c292275b3515a91b51d0e791a8fae256`. Historical references,
failed k1 admissions, shaders, and prior results are never overwritten.
The original [PR169 raw release](https://github.com/leecdiang/HeteroSpec/releases/tag/b570-reference-parallel-v1-evidence-20261103)
continues to provide authenticated historical objects. This delivery additionally
retains the original R manifests and K1_REGRESSION bytes and verifies their hashes
during CPU reconstruction. Target-only success here cannot establish dual-model
k1 capacity or speculative speedup.

The four-session primary experiment is complete:512 measurements and512 matched
warmups. All three AUTO family intervals cross1 and the registered3% engineering
screen fails. See [RESULTS.md](RESULTS.md) for complete results, separate aligned
controls, costs and limits. Both genuine source/policy freezes were published
and inspected before any B570 held-out output. B570 froze at
`6517c79b59ad3d813a35fa087d15751b825dad34`; RTX froze at
`efd92438a08a4e9c37a422731ddd6850d8907f1b`. The shared test runner checks the
receipt hashes, exact token/cohort identity and frozen source before launch.
The freeze receipts establish order and identity; the results come from the
qualified native observations and complete registered schedule.

## Deployment and timer

Qwen3-8B Q8_0 SHA256
`408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6`, target only,
C4096, F16 K/V, non-flash, q32, ordinary greedy cap128/native EOG. No draft
model is loaded. Logs report 37/37 layers offloaded to Vulkan, a 576 MiB Vulkan
KV allocation, and the framework's 630.59 MiB CPU_Mapped model buffer. This
is the unchanged native full-layer-offload placement, not a new CPU fallback.

The service is **immutable host snapshot-backed exact-token prefix replay**.
It is not a claim of resident zero-copy prefix caching. Scalar prefix production
requests no output rows. Its snapshot therefore has no pending output logits or
sampled token; every admitted request has a nonempty known append. Snapshot
bytes, token ownership, logical positions, native physical head, complete service
logits and final sequence state are checked. The retained cache object is hashed
again after heavy execution to check mutation isolation.

The service clock encloses key lookup, constant AUTO policy lookup, fresh context
creation, real sequence-state import, append, ordinary decode, synchronization,
response/state commit and context destruction. Model loading and host cache
preload are recorded separately. Actual scalar prefix construction is measured
separately and included in cumulative owned cost. Every measurement has one
immediate same-arm warmup with a fresh restored context. Heavy qualification
times are never formal performance samples.

This is a native ready-token request boundary. Corpus rendering/tokenization,
JSON harness parsing and construction of the fixed token vector precede that
boundary; process/trace costs retain their actual execution lifetime. It is not
an HTTP end-to-end latency measurement. Clean service does not dump final-state
or full-vector objects; those observers are confined to qualification.

WB-cut retains the original q32 origin. WB-rechunk queries `hs_parallel_groups`
at the current physical head, consumes only the first admitted run and starts
the next full-width query there. All arms use the same PR169 Vulkan/ggml DLLs,
including F32 activation and p021. Only the llama library is relinked to add an
output-free allocator inspection API; numerical source files are unchanged.

The fixed calibration panel happens to occupy only the zero extra-call-density
bin. The published selector rule therefore necessarily yields a constant table.
The native AUTO path checks this condition and performs its actual table lookup
inside service. It refuses a nonconstant table, rather than accepting free
offline per-input policy decisions. No optimum or selector gain is presumed.

## Corpus and coordination

The pinned OASST1 `all.messages.jsonl.gz` contains 161443 messages. Here
"complete terminal path" means an actual user leaf with no children; ancestors
are recovered through the root without truncation. The filters retain 6423
English, nondeleted, nonsynthetic alternating paths. Complete cached and request
strings use native `llama_chat_apply_template` and native tokenization with
`add_special=true, parse_special=true`. The cache renderer ends at the preceding
assistant without an assistant-generation suffix; the request renderer includes
that suffix after the terminal user.

`corpus.py` records every path exclusion and the inherited exposure audit, then
uses the design's unmodified root/path hash selection. Source IDs and text do
not influence the selector. Oversized paths are recorded, never truncated.
The native allocator sweep exercises real `find_slot/apply_ubatch` for every
head in disposable metadata-only contexts without model forwards. No such
uncomputed KV is used for inference. Qualification separately rechecks each
real restored physical head. Granularity16/32/64 entries are output-free
scenarios, not measured third-party serving engines.

The initial RTX provisional cohort used a different terminal interpretation.
The saved provisional receipt and GitHub coordination comments retain that
difference. B570's selected test roots do not overlap RTX's initial calibration
roots. RTX independently accepted the actual-user-leaf interpretation and all44
selected paths/token arrays at `3e326ecafa5fb74a65b8f22acf5d10175f015a9f`.
Both sides verified all44 root IDs, cached/request hashes and physical heads.
The provisional RTX panel remains an earlier epoch, not the shared blind panel.
RTX's declared file-backed replay charges file read/index construction inside
service. B570 preloads immutable snapshots into host memory and charges preload
separately. Report within-host policy contrasts, not pooled or pure-hardware
timing comparisons.

B570 completed exactly144 calibration warm/measured slots. The resulting AUTO
table is constant WB-rechunk. Its3193.093745-second observed calibration window
includes earlier engineering and orchestration; it is not a free offline fit.
The earlier incomplete observer-state epoch and explicitly interrupted slot are
retained with their costs. Candidate03 qualification passed every calibration
root/arm with final-state objects captured in both heavy and OFF controls.

## Host execution and read-only reconstruction

The host scripts use `HS_PREFIX_ROOT` (default
`I:/HeteroSpec/b570-prefix-reuse-20261104`) for new evidence. Each native unit has
an immutable JOB, budget reservation, command, Windows Job supervisor record,
loaded DLL hashes, stdout/stderr, native result and owned-cost receipt. Workers
are created suspended, assigned to a kill-on-close Job, then resumed, with a
finite7200-second limit and20GiB disk/2GiB RAM/128MiB device reserve. The device
guard checks both `free<=total` and the reserve. The2048-request tranche and
original1936-slot design remain unchanged; no extra timing follows a poor mean.

The source-host preparation entry points are `host.py setup`, `host.py build`,
`corpus.py prepare`, `corpus.py tokens` and `corpus.py select`. Existing evidence
must not be reused as a new writable output root. Development controls use an
old input, distinct from the OASST panel. They probe all appended logits only as
a separate output-shape diagnostic. Ordinary heavy/off qualification requests
exactly the clean service's output rows.

`campaign.py references`, `qualify`, and `calibrate` run the fixed calibration
stages. `main-references`, `main-qualify`, `main-time`, and `aligned` require the
coordination release. Main timing requires every root/arm qualification. A failed
gate cannot fit a passing subset or produce a qualified aggregate.

Run `python verify_raw.py RESTORED_ROOT` for independent full-vector hashes,
finite-value/argmax reconstruction, runtime identity, state/endpoint comparisons,
raw schedule and measured cost checks. The inherited `study.py` additionally
checks the exact1024 warm/timed schedule and root-cluster statistics. CPU package
reconstruction is explicitly different from native replication on another GPU.

## Delivered-byte restoration

Download every asset from the dedicated
[evidence release](https://github.com/leecdiang/HeteroSpec/releases/tag/b570-prefix-reuse-v1-evidence-20261104)
into a fresh `evidence-download` directory using an account with repository
access. `DELIVERY_ASSETS.json` pins the assets; `INDEX.json` pins every raw object
part and `MEMBERS.json` maps all retained logical paths. With GitHub CLI and
Python3.11 or newer, the complete read-only reconstruction is:

```powershell
gh release download b570-prefix-reuse-v1-evidence-20261104 --repo leecdiang/HeteroSpec --dir evidence-download
python evidence-download/object_archive.py verify --root evidence-download
python evidence-download/object_archive.py restore --root evidence-download --out restored-native-evidence
python restored-native-evidence/repro/recompute.py restored-native-evidence > recomputed.json
```

Use a new restore directory. Reconstruction independently checks full vector
bytes/argmax, state objects, native runtime identities, schedules, qualification,
both freeze receipts, untouched old R/k1 hashes, selector fit, root bootstrap,
aligned controls and costs. The published `evidence/DELIVERY_READBACK.json`
records actual same-host fresh-download restoration and exact agreement with
local CPU reconstruction. Authenticated access and package verification do not
claim anonymous access or third-party native replication.

## Portable native kit

The archive's `portable-final` directory includes both original and candidate source,
the adapter, historical import libraries/DLLs, and an actual calibration fixture.
It contains no model weights. Supply the exact model hash above.
The same frozen files are also offered as the separate
`b570-prefix-native-source-kit.zip` release asset (117696092 bytes). All7133
manifest members were independently rehashed after ZIP readback; both variants
compiled successfully from this portable directory layout on the source host.
With Visual Studio2022 and CMake, configure the adapter using:

```powershell
cmake -S portable-final/adapter -B candidate-build -G "Visual Studio 17 2022" -A x64 -DCANDIDATE=ON -DLLAMA_SOURCE=ABSOLUTE/portable-final/candidate-source -DHISTORICAL_LIBS=ABSOLUTE/portable-final/historical-libs/candidate
cmake --build candidate-build --config Release --parallel 4
```

For the original worker use `CANDIDATE=OFF`, `original-source`, and
`historical-libs/original`. Stage all corresponding historical DLLs next to the
executable, replacing only the candidate's `llama.dll` with the freshly linked
one. Create a fresh JOB/OUT pair: `frontier.exe JOB.json OUT`. `fixture.json`
contains complete native request and cached token arrays; the native `seed`
slot creates its prefix snapshot, and the `service` slot performs real restore.
The supervised jobs in `units` are complete executable examples. Rebind paths
and runtime manifests on the receiving host; never reuse source-host loaded-file
attestations as proof of a different host's run. The earlier `portable` directory
is retained as a development epoch; use `portable-final` for the final source.

No automatic merge, paper modification, submission or GPU rental is performed.
