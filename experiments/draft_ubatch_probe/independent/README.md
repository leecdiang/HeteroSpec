# Reproduce the independent checks

All scripts are local and read-only with respect to the study and runtime sources. Use new output directories. Requirements are Python 3, a C++17 compiler, and the already-built candidate CPU runtime with its source headers and bundled nlohmann/json.hpp. No model download, repository mutation, Windows build, or GPU use is performed.

Set STUDY, SOURCE, LIB, and MODEL to the study directory, runtime source directory, CPU library directory, and one pinned GGUF. Paths in SUMMARY.json are names, not absolute workspace dependencies.

```
python3 check_stage.py --study "$STUDY" --output /tmp/fresh-stage-review
python3 make_mutants.py --fixture fixture/test_native.cpp --output /tmp/fresh-mutants
python3 run_native.py --fixture fixture/test_native.cpp --source "$SOURCE" \
  --library-dir "$LIB" --model "$MODEL" --output /tmp/fresh-normal \
  --expected-exit 0 --expected-status PASS
python3 run_native.py --fixture /tmp/fresh-mutants/early_stop.cpp --source "$SOURCE" \
  --library-dir "$LIB" --model "$MODEL" --output /tmp/fresh-early-stop \
  --expected-exit 2 --stderr-contains 'independent expected output length'
python3 run_native.py --fixture /tmp/fresh-mutants/discard_committed_state.cpp \
  --source "$SOURCE" --library-dir "$LIB" --model "$MODEL" \
  --output /tmp/fresh-discard-state --expected-exit 1 --expected-status OBSERVED_MISMATCH
```

The two historical/*.cpp fixtures are intentionally invalid. Running either with the original Q8 model and expected exit 0 / status PASS reproduces the old test false positive. That PASS is the defect, not evidence of a correct transaction.

For independent history sensitivity:

```
c++ -std=c++17 -O2 -I "$SOURCE/include" -I "$SOURCE/ggml/include" \
  -I "$SOURCE/vendor" history_sensitivity.cpp -L "$LIB" -Wl,-rpath,"$LIB" \
  -lllama -lggml -lggml-base -o /tmp/history-sensitivity
/tmp/history-sensitivity "$MODEL" > /tmp/history-result.json
```

The program compares six prefixes with the same final token. `different_logit_elements` counts float elements with different bytes, not bytes or tokens. The bundled four result files retain each model's separate outcome. The program includes the pinned fixture for context construction and scalar replay; it is a new input-sensitivity probe, not an independent runtime implementation.

run_native.py retains compile/run commands, stdout, stderr, exact hashes, and a fresh per-case journal. Its UBSan claim applies only to the executable. Follow the study's separate source/model generation and build instructions; no trained-model or full-runtime-sanitizer claim is implied.
