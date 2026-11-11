# Rebuild and execute the Linux deployment

This recipe extends PR196 at `2cfe56e13296d6b81463a9228c4fbfafa6f23e0c`.
Read README, ENVIRONMENT, PROTOCOL and HOST_ADAPTER first. The run directory is
private. A result report must distinguish compilation, independent reference
repeatability, numerical qualification, and the complete comparative panel.
Do not infer any later stage from an earlier stage's successful exit.

## Inputs and tools

Use Linux x86-64, a CUDA toolkit supporting the explicitly allocated GPU, GCC,
Ninja, CMake >=3.24 and Python with NumPy. The observed build used GCC11.4,
CUDA12.5.40, CMake3.31.6, Python3.11.14 and NumPy2.3.5. These are observations,
not permission to change an installed system. User-space tools suffice.

`pins.json` binds the source ZIP size/SHA256, pristine upstream commit, and all
four GGUF hashes. `acquire_models.py` and `acquire_ranges.py` bind the public
model revisions. Network retries are input acquisition, not inference retries.
The final complete-file hash is mandatory even after a resumed/ranged download.
An alternate distribution is acceptable only for the identical pinned bytes.
Never expose partial files to native workers.

The source ZIP is the `rtx-phase1-source.zip` asset of the pinned repository's
`tpds-phase1-rtx-review-v2-evidence-20261107` release. Fetch pristine llama.cpp at
`0cae43063cf15170e91a2ff4d034da0ecef4a1b2`, with clean checkout and all files.
Its complete Git tree is `21455f0751564fc633b58ec481a05eeb514a6650`.
If a codeload archive replaces Git transport, verify the entire imported tree and
original Git commit object; the expected SHA written into an arbitrary new commit
is insufficient. Preserve the import receipt. No latest-branch fallback is used.

The checked fallback is reproducible with the public pinned GitHub objects:

```sh
curl --fail --location --output "$ROOT/upstream.tar.gz" \
  https://codeload.github.com/ggml-org/llama.cpp/tar.gz/0cae43063cf15170e91a2ff4d034da0ecef4a1b2
curl --fail --location --output "$ROOT/upstream-commit.json" \
  https://api.github.com/repos/ggml-org/llama.cpp/git/commits/0cae43063cf15170e91a2ff4d034da0ecef4a1b2
python "$B/import_upstream.py" --archive "$ROOT/upstream.tar.gz" \
  --metadata "$ROOT/upstream-commit.json" --out "$ROOT/pristine-upstream" \
  --receipt "$WORK/UPSTREAM_ARCHIVE_IMPORT.json"
```

Set the `B`, `ROOT` and `WORK` variables as below before these commands. The
importer requires the observed archive SHA256 as well as the exact Git tree and
commit. If transport regenerates different archive bytes, retain the failure and
review that packaging change; do not weaken the tree/commit identity checks.

## Read-only inventory and allocation

```sh
B="$PWD/benchmarks/linux_transfer_v1"
ROOT="$HOME/heterospec-linux-transfer"
WORK="$ROOT/run-01"
mkdir -p "$WORK"
umask 077
python "$B/host.py" inspect --out "$WORK/inventory.json"
```

Obtain one explicit idle UUID allocation and CPU limit before CUDA initialization.
Copy `config.example.json` to `$WORK/config-01.json` and fill the actual approved
allocation, UUID and private work root. Keep this file and raw inventory private.
The example protects GPU0; neither availability nor a cooperative flock grants
allocation. `host.py` rejects foreign processes on the selected card and stops
only its own worker process group. Keep the default reserves and budget caps.

## Source and native build

```sh
python "$B/sources.py" --out "$WORK/stage-01" \
  --archive "$ROOT/rtx-phase1-source.zip" --upstream "$ROOT/pristine-upstream"
python "$B/adapt_host.py" --source "$WORK/stage-01" --out "$WORK/stage-04"
python "$B/build.py" --staged "$WORK/stage-04" --out "$WORK/build-R-01" \
  --role reference --arch 86 --jobs 2
python "$B/build.py" --staged "$WORK/stage-04" --out "$WORK/build-loop4-01" \
  --role loop4 --arch 86 --jobs 2
python "$B/build.py" --staged "$WORK/stage-04" --out "$WORK/build-packed-01" \
  --role packed --arch 86 --jobs 2
```

Replace architecture86 only with the observed capability of the allocated GPU.
The original attempt used separate retained stages: R from stage03, candidates
from stage04. Stage04 adds all-boundary heavy observations; the reference driver
does not include the historical candidate worker. A fresh reproduction may use
stage04 for all three roles. Fresh output paths are required, including after a
failed build. No Windows numerical module participates.

`adapt_host.py` records exact source anchors and a patch. Changes cover POSIX
file/clock/hash operations, exclusion of the historical Windows CLI, the observed
GPU placement guard, allocated thread count, and heavy state capture coverage.
The numerical cores remain untouched. Reference output reserve1 and candidate
reserve4, inherited CUDA graph defaults and `-use_fast_math` are explicit; their
equivalence must be established by numerical observations. This is not a claim
of Windows/Ampere bit identity. The optional Windows profiler remains disabled.

Each native build records actual compile/link commands, map, response files,
static archives, generated files, compiler dependency closure and tool hashes.
Keep these artifacts, including failed epochs. Runtime receipts separately bind
the actual loaded ELF dependencies. Compilation status remains
`BUILT_NOT_QUALIFIED` even when later numerical qualification succeeds.

## Reference first, then finite qualification and panel

Place the four full-hash-verified models in `$ROOT/models-final`, using the exact
filenames recorded in `prepare_study.py`. Then:

```sh
python "$B/prepare_study.py" --work "$WORK" --stage "$WORK/stage-04" --repo "$PWD"
python "$B/panel_native.py" prepare --work "$WORK" --repo "$PWD"
python "$B/run_reference.py" --work "$WORK" --config "$WORK/config-01.json" \
  --build "$WORK/build-R-01/BUILD.json"
python "$B/qualify_partitioned.py" --work "$WORK" --repo "$PWD" --epoch qualification-01
python "$B/panel_native.py" run --work "$WORK" --repo "$PWD" \
  --qualification "$WORK/qualification-01"
```

Stop a command chain on any failure and retain its epoch. These commands are
sequential; do not launch candidate forwards during reference establishment.
`run_reference.py --family Smol` is an optional input-download overlap: it writes
only a family repeat receipt, grants no candidate eligibility, and the global
reference command validates/reuses those exact completed runs without recharging
or replaying them. The global freeze checks the budget ledger contains reference
jobs only. Original Windows references remain unchanged.

The optional `execute_study.py` coordinator waits for the four complete verified
receipts in `$ROOT/models-ms-01`, binds exact model paths, then invokes the same
phases. Its `--resume-input-wait` is restricted to a wait before model binding;
it never retries model jobs. It assumes the three build receipts and prepared
`inputs-01` already exist.

The observed initial `qualify_native.py` attempt packed all12 geometry cases into
one heavy worker. Each completed Qwen W_L4 case took about95s, exceeding the900s
ceiling for the complete matrix. `qualify_partitioned.py` applies identical
comparison and natural-transaction rules with3 geometry cases per candidate
worker, uniformly across all arms and both families. It changes no numerical
binary or formal worker and keeps the900s ceiling. Use it directly for a fresh
reproduction as above. `continue_partitioned_study.py` is a one-time recorded
continuation of that specific retained timeout: no formal reservations may
exist, the old status/budget are preserved, the previously completed independent
R matrix is validated before reuse, and no candidate captures from the failed
worker count as completed qualification. It cannot retry a partially observed
formal panel. The original coordinator still records its own original outcome.

One later admission defect was observed after the first complete formal worker:
loop4 and packed M controls can have identical request JSON, while using different
frozen numerical builds. The original job-hash-only repeat guard blocked the
second control before reservation/native launch. `host.py` now binds execution
identity to the original frozen plan's slot, numerical build and request file.
It still rejects every reserved slot, wrong core, changed plan and invented output
slot. Six regression cases cover these distinctions normally and under `-O`.

`panel_native.py run --resume-unstarted` is an explicit recorded continuation for
this admission failure. It requires every previously reserved native slot to have
COMPLETE HOST/CHECKED records, validates their request/reference/launch/module
hashes, preserves them without execution, archives only the empty unreserved
blocked output, and executes the remaining original slots in original order. It
reuses the original completed free-reference endpoints and unchanged numerical
freeze/jobs. It rejects an attempted incomplete/failed native slot; it cannot
selectively rerun one. The first-worker interruption and old statuses remain in
the final record. Numerical binaries, service timing and input population do not
change. `PIPELINE_STATUS-03.json` records this continuation independently of the
retained original coordinator outcomes.

Qualification uses independent free R endpoints and separately rebuilt forced
prefixes for requested vectors and committed states. It covers all fixed
q1/4/8/32 geometries, four M controls, both D4 paths, all observed rejection,
pending/trim/frontier boundaries, cap1/cap128 and native EOG. Exact finite full
vocabulary floats and all active F16 K/V values are checked. Missing native EOG
or other required coverage closes the qualification; helper tests cannot replace
it. `native_checks.py` remaps imports of the previously reviewed readers only.

The panel is frozen before opening its sixteen old deployment-transfer roots.
It retains all24 worker slots, 384 tests and48 primers. Clean requests have no
heavy observer, online R, state export/import or extra context creation inside
service. Actual clocks, reset/request traces, physical widths, startup and memory
observations are retained. First complete response is not TTFT. A failed arm
closes that version's complete comparison; do not rerun a favorable subset.

## Evidence and scope

Keep the complete private work directory, not just CHECKED booleans. Large binary
captures should have a complete path/size/SHA256 index and explicit archive
readback scope. Public export must remove company paths, UUIDs, allocation IDs,
raw process inventories and signed download redirects. A transformed public JSON
has its own hash; its `*_sha256` fields continue to identify original raw files.
Do not pretend transformed receipts have the original byte hashes.

Report numerical failures and every planned slot status even if no timing panel
opens. The finite result is deployment transfer on exposed roots, not fresh blind
input confirmation, multi-GPU replication, or third-party reproduction. Do not
merge the results PR or modify the manuscript automatically.
