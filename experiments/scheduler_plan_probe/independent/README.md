# Independent native CPU plan-probe checks

These tests run against an already staged and built ggml plan-probe library. They do not build a model, access a GPU, or qualify an optimized path.

Set `SOURCE` to the staged source directory and `LIB` to its built shared-library directory, then run:

```sh
python run_independent.py --source "$SOURCE" --lib "$LIB"
```

The script requires a C++17 compiler and Python standard library. It creates only temporary test executables. Use `--output /path/to/results.json` to save results. Headers are expected under the staged source's `ggml/include` and `ggml/src`; `--probe-include` is available for a separate probe header directory.

- `test_plan_probe.cpp` verifies always-veto behavior, metadata/use-count mutation detection, rejection of a mismatched caller graph, callback non-execution, cycle/count rejection, and reset preserving the armed veto. It also demonstrates that tensor-data changes are intentionally not certified by metadata matching.
- `test_eval_false_success.cpp` runs the ordinary, unarmed CPU scheduler and reproduces its existing callback-stop behavior: the scheduler can report success after executing only the first node, leaving the final output unchanged. This is a scope counterexample, not evidence that the armed probe executes.

By default the test executables are not sanitizer-instrumented. Add `--sanitize address-undefined` when linking a separately verified ASan/UBSan native build; this option instruments the test executables, not the supplied libraries. Verify the library build flags independently. The generated JSON records exact test-source, staged-source, and library hashes. A hash match establishes identity, not correctness. Callers must externally serialize scheduler/graph/buffer access and retain valid object lifetimes.

## Recorded sanitizer run

The saved `independent_results.json` used a separately verified full ASan/UBSan native-library build and matching instrumentation of these test executables:

```sh
ASAN_OPTIONS=detect_leaks=0 python run_independent.py \
  --source "$SOURCE" --lib "$LIB" --sanitize address-undefined
```

LeakSanitizer initially failed under ptrace, so leak checking was disabled for the successful runs and is not validated. `validation_recheck.json` records a separate rerun of the implementation's 60-check, 3-split/3-transfer native CPU test and the checked library compilation flags. These are not CUDA tests.
