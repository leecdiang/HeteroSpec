# CPU reproduction and review

Use a fresh Linux directory and the exact parent+successor Git commits. Read the
status and limits first. These instructions never admit native execution.
Python3.10 and the frozen compiler/header inputs are identified in the receipts.
The numerical R/loop4 builders compile/link and inspect only; never execute their
artifacts, even help/selftest. The old numerical libraries and source locks must
match before any native compilation.

## Pure CPU tests

From this directory, use a new output path for every invocation:

```sh
python3 tests/bridge_tests.py --out /ABS/FRESH/bridge-tests -v
python3 -O tests/bridge_tests.py --out /ABS/FRESH/bridge-tests-optimized -v
python3 tests/resource_tests.py --out /ABS/FRESH/resource-tests -v
```

The final ordinary/optimized evidence has32 controller tests,27 resource tests
and9 resource-manifest finalizer tests in each mode. The finalizer's own test
CLI and actual invocation are recorded in its receipt. These are synthetic
fixtures; they cannot produce a native numerical PASS. `NATIVE_261_NOT_RUN.json`
lists the exact still-unexecuted native graph.

The immutable unapproved resource manifest is reproducible with:

```sh
python3 finalize_resource_manifest.py \
  --selection review/MEASURED_SELECTION_FINAL02.json \
  --out /ABS/FRESH/FINAL_EXECUTION_MANIFEST_NOT_ADMITTED.json
```

Compare exact bytes with the checked-in final manifest. Its72 request limits,
69,354 planned rows, ten initialization/deployment actions and four inaccessible
failure slots are inherited unchanged. The manifest and a reproduced hash are
neither permission nor a launch command.

## Fixed std-only process bridge

`build_cpp.py` builds and statically inspects the two std-only fixtures without
executing them. The exact reference vendor-header SHA, compiler, commands and
source hashes are in `CPU_EVIDENCE/cpp-bridge-final-03/`. The final CPU launcher
is from launcher build03; the worker remains from build02. Rebuilding the current
CPU sources with the frozen recipe must reproduce those pinned hashes before
the runner accepts them. Another ELF with a caller-supplied matching SHA is not
accepted. A different compiler artifact needs a separately reviewed pin change.

With the reviewed artifacts present, the actual CPU fault suite is:

```sh
python3 tests/interop_faults.py --out /ABS/FRESH/cpu-suite \
  --launcher /ABS/FROZEN/cpp_bridge_launcher \
  --worker /ABS/FROZEN/cpp_fixed_worker
```

It executes the real pre-exec bind/launcher close/worker HELLO/supervisor chain
against the ordinary-file ResourceDomain factory. It runs14 cases, including
crashes, connection loss, changed job input, missing closure/result, bounded
output failure, short output and sync failure. It creates no model or real
resource domain. Failed states and spent reservations remain in each case.
The original final suite's40 request/row reservations are mock accounting only.

`export_cpu_evidence.py` independently checks the original CPU journal hashes,
reconstructs full STATE and counters, and exports a public derived trace plus
an index of privately retained original bytes. Public traces intentionally omit
kernel/process/job identity contents. Their replay is not a new kernel binding
test or a numerical/GPU execution.

The four std-only supervisor tests specifically cover deadline/owner boundaries;
they do not prove that blocked filesystem or device operations can be preempted.
Full compile records for the real R/loop4/v3 native launcher are distinct from
their execution: all three remain unexecuted.

## Archive and safe stopping

`package_cpu.py` selects reviewed UTF-8 files only; no ELF, weights, objects or
libraries enter the public packet. The inherited strict archive reader verifies
the full index, byte lengths and SHA values before restoring to a fresh path.
Public readback is CPU text integrity, never independent native validation.

Never resume an existing STATE or remove a lock to make a test start. Read the
original STATE/journal/STOP and preserve them. An unknown, partial or failed
result retains the conservative charge and blocks subsequent workers. No
automatic retry, fallback reference, relaxed tolerance, timing or new GPU is
part of this reproduction. Future N1a requires the software/resource gaps and
separate device/window/budget review listed in STATUS.json.
