# Linux source rebuild and independent deployment transfer

This prospective study follows reviewed RTX PR195 and B570 PR194. It **does not**
run old Windows executables under Linux. It rebuilds the llama core **and** the
CPU/base/CUDA numerical backend from pinned source, provides an independent
Linux scalar-reference driver, and reuses the final candidate transaction path.

**Authoring status:** code and local helper tests only. The private 39 MB source
asset and full upstream checkout were not materialized in the authoring container;
there is no nvcc/GPU here. Full private-source staging, CUDA compilation, original
API integration, model qualification and performance are **NOT_RUN**. The remote
agent must finish them, not stop at a source-kit or helper-test receipt.

## Start on the company server

Use a fresh worktree at this PR head and a private work directory. Do not run in
an RTL, production service or colleague's workspace. First run only:

```sh
B=benchmarks/linux_transfer_v1
WORK="$HOME/heterospec-linux-transfer/run-01"
mkdir -p "$WORK"
python3 "$B/host.py" inspect --out "$WORK/inventory.json"
python3 -m unittest discover -s "$B/tests" -v
```

Read `HOST_PROMPT.md`, `HOST_ADAPTER.md` and `PROTOCOL.md`. Inspect GPU UUIDs,
compute processes, architecture, driver, nvcc (distinct from driver), compiler,
RAM, disk, scheduler/allocation policy and CPU affinity. Historical availability
is NOT permission or current availability. Select one explicitly allocated idle
GPU; the example protects index0. No multi-GPU execution is needed. If a scheduler
is in use, obtain its allocation; this project's local flock is not a system-wide
reservation. Never reset devices or kill another user's process.

## Source acquisition and full native builds

Authentication stays in the user's existing `gh` setup. Do not print tokens.
The default download is only the source archive, not 1.27 GB of Windows binaries
or historical KV evidence. Models are separately hash-pinned inputs.

```sh
python3 "$B/sources.py" --out "$WORK/stage-01"
# Offline alternative: --archive /approved/path/rtx-phase1-source.zip \
#                      --upstream /approved/exact-clean-upstream-checkout

# Replace 86 with the selected GPU's observed capability, without a decimal.
# 86 is an example for an A5000, not an assertion about the current host.
python3 "$B/build.py" --staged "$WORK/stage-01" --out "$WORK/build-R-01" --role reference --arch 86 --jobs 2
python3 "$B/build.py" --staged "$WORK/stage-01" --out "$WORK/build-loop4-01" --role loop4 --arch 86 --jobs 2
python3 "$B/build.py" --staged "$WORK/stage-01" --out "$WORK/build-packed-01" --role packed --arch 86 --jobs 2
```

`--cpu-only` is allowed for compile diagnostics but never qualifies a GPU R.
Normal build/API/platform repairs are autonomous, versioned work. Unrecognized
Windows APIs produce an adaptation report, not silent stubs. Do not substitute
latest upstream or load an old DLL to make a build pass. The optional Windows
CUPTI collector is rejected explicitly; a Linux profiler is separate from clean
execution. Keep valid default graph reuse for all paths.

The reference core is pristine upstream at the exact commit in `pins.json`.
The candidate kit's two cores differ in projection lowering; its shared CUDA
backend is rebuilt from their pinned source, not replaced with upstream HEAD.
Numerical and OS/architecture changes can change bits: freeze this deployment's
R **before candidate outputs**, and test the method against that R. Preserve every
old Windows R and result unchanged. This is method transfer, not cross-GPU bit
identity or external production validation.

## Qualification and execution

1. Bind actual model files, vocabulary/input IDs, context/producer/output masks,
   thread count, toolchain, loaded ELF modules and GPU. Do not download corporate
   data or treat a same-named GGUF as a matching model.
2. Run the independent reference twice on exposed development cases and validate
   full requested vectors, active state and frontier; freeze it with `freeze.py`.
3. Complete the native adapter checklist, all four cut/projection paths, ordinary
   and D4 controls, pending/rollback/EOG/cap and clean-path checks. An exit code or
   `passed:true` supplied by a framework is not numerical proof.
4. Only then freeze the candidate code, proof registry and prospective job files.
   `jobs.py` generates24 resident workers/384 tests/48 primers for the fixed
   sixteen-root transfer panel; these old roots are not called unseen inputs.
5. `host.py run` executes one declared job under one authorized UUID, records real
   result-arrival clocks and loaded modules, retains failures and kills only its
   own process group on abort. Formal execution requires a qualification freeze.
6. Build CHECKED records using the independent trace adapter, then `analysis.py`.
   Keep all six arms and missing costs as null. Record startup, test burst, resident
   service, memory and observer costs separately; never add inclusive clocks.

`config.example.json` is deliberately unauthorized. Fill actual allocation and
local paths; don't copy dummy values into scientific receipts. CPU build/source
work can proceed before GPU permission. No compute rental, sudo, driver update,
clock setting, web server or network-facing inference endpoint is required.

## Outputs

An independent results PR should contain the compact method/port diff, complete
source/build/freeze identities, model hashes, reference contract, qualification
scope, all planned slot statuses, complete strong controls and concise results.
Archive raw scientific captures separately. Do not upload company hostnames,
process command lines, credentials, datasets or unrelated files. Approval to use a
company GPU does not imply approval to publish unrelated company information.

No merged manuscript is updated by this prospective study. See `MERGE_REVIEW.md`
for the actual integration of prior evidence.
