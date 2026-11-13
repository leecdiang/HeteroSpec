# Reproduce CPU evidence without opening a model

Use a fresh checkout containing this successor and its exact PR227/226 ancestors.
Python3, Node and a Linux C++17 compiler/readelf are needed. No model download,
backend initialization, GPU utility or native linked executable is needed for
the following CPU tests.

From this directory, run:

    python3 -B run_cpu_tests.py --out /absolute/fresh/short-output-directory
    node --test test_assemble_checks.js
    node review/resource_budget.js CLOSEOUT_READONLY.json /absolute/fresh-resource.json
    node coverage_map/build_map.js /absolute/repository-root /absolute/fresh-map-directory

run_cpu_tests.py compiles only a recursive allowlist of standard-library/POSIX
mock sources. It inspects dynamic dependencies of every resulting mock with
readelf and rejects any library outside the CPU standard-library allowlist
before running any mock. It never builds or runs runtime.cpp, worker.cpp,
active_kv.cpp, producer_facade.cpp, the old producer helper, or a llama library.
Fresh directories are mandatory; all partial failure files remain.

The assembler tests use invented raw files and the frozen strict comparator.
They establish rejection/transport behavior, not native numerical equality.
The map is regenerated only when attached source/receipt hashes match, and must
contain261 NOT_RUN rows, zero native passes and zero cold-retention checks.
The resource script reproduces an unapproved bound from a saved actual-host
snapshot; it does not probe or admit a GPU.

prepare_jobs.js additionally needs the exact already-published PR224 N0 saved
TOKENIZER_OUTPUT.jsonl, SHA256
23e812286a06ce6e067eb89648221b4348daeb1d3b5722aab780d09c56288350.
It reads saved IDs, never instantiates or invokes a tokenizer/model. Use the exact
hash from prepare_jobs.js as authoritative; do not invent a replacement file.
The generated NATIVE_JOB_TEMPLATE.json is included for review and has no grant,
actual-R continuation certificate, quiet window or runnable permission.

For native compilation only, build_native.py requires the complete exact
original Linux source/build trees and hash-bound numerical archives listed in
ORIGINAL_BUILD_BINDINGS.json, plus the bound parser-only objects. Supply them
through its explicit path arguments in a new build directory. It verifies
complete original source/archive/object identities, compiles/links R and loop4,
and uses only file/symbol readers afterward. The current public packet does
not contain the large original backend archives, CUDA installation, model or
private host paths. Those inputs remain on the audited A5000 host and are bound
to the original immutable Linux deployment materials. A public-only replay does
not reproduce this host native link unless those exact dependencies are supplied.

NEVER execute either native ELF, even to test rejection or display help.
No CPU recipe authorizes native initialization, placement or a model request.
The final concrete ProductionGate has no grant path in this build.

The text packet is restored using packaging/archive.py replay with its exact
PACKET.json SHA256 into a fresh directory. Restore validates all payload sizes,
digests, file types and paths before writing; a readback is a public byte check,
not a GPU rerun. PUBLIC_READBACK.json records the actual anonymous closure.
