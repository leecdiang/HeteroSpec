# Independent native CPU bridge review

This bundle contains the independent review, exact reviewed-file hashes, reproducible tests, retained before-fix counterexamples, and final results. It does not supply a runtime admission gate or a GPU result.

Set BRIDGE to the reviewed native bridge directory, SOURCE to the pinned candidate source, LIB to its CPU library directory, MODELS to the stress-model directory, and OUT to a fresh writable directory. Python scripts use the standard library. Native builds additionally need the dependencies required by the bridge.

```
python "$BRIDGE/build.py" --source "$SOURCE" --library-dir "$LIB" --output "$OUT/build"
python "$BRIDGE/run_matrix.py" --source "$SOURCE" --library-dir "$LIB" --binary "$OUT/build/bridge" --models "$MODELS" --output "$OUT/matrix"
python -O check_parser.py --parser "$BRIDGE/parse_state.py" --output "$OUT/parser.json" --native-blob "$OUT/matrix/dense-reject0/candidate/1-sequence.bin"
python check_native_inputs.py --binary "$OUT/build/bridge" --model "$MODELS/dense.gguf" --output "$OUT/inputs"
python -O check_evidence.py --auditor "$BRIDGE/offline/replay_audit.py" --run "$OUT/matrix/q8-reject0" --output "$OUT/corruptions"
python check_controller_failures.py --controller "$BRIDGE/run_bridge.py" --output "$OUT/failures"
for model in q8 dense; do
  python -O check_fresh_queries.py --parser "$BRIDGE/parse_state.py" --binary "$OUT/build/bridge" --run "$OUT/matrix/$model-reject0" --model "$MODELS/$model.gguf" --output "$OUT/fresh-$model"
  python "$BRIDGE/run_bridge.py" --source "$SOURCE" --library-dir "$LIB" --binary "$OUT/build/bridge" --model "$MODELS/$model.gguf" --output "$OUT/extended-$model" --cap 9 --reject 0 --draft-ubatch 4
done
python -O check_matrix.py --auditor "$BRIDGE/offline/replay_audit.py" --runs "$OUT"/matrix/*/ "$OUT/extended-q8" "$OUT/extended-dense" --output "$OUT/matrix-result.json"
sha256sum -c SHA256SUMS
```

Exact paths, PIDs, timings, module paths, identity/evidence hashes and host details may differ on reproduction. Compare explicit semantic/byte-equality results, not those incidental fields.

Historical counterexamples are not claims about the final version:
- historical/bridge_pre_uint64_fix.cpp is byte-exact source hash 0ea4d783369fa8084d2b710fd7b0e95442cbf2ab309d71c05baa20b01e71db3e. Build it beside the pinned fixture with the recorded build command adapted to a fresh directory. check_native_inputs.py with --expect-accepted forced_reject_index_18446744073709551615 reproduces the old acceptance.
- historical/run_bridge_pre_ownership_fix.py is byte-exact hash 8af79773a30965c07319ad4fc922e6435ee550a7f959aae963237b0cebc857cb. Set PYTHONPATH to the reviewed bridge and its offline directory, then run check_controller_failures.py against this file. It intentionally exits nonzero and records the old overwrite/missing-receipt failures.

Parser sentinels include explicit Inf/NaN/signed-zero F16 bit patterns, but perform no attention arithmetic. Neither these tests nor the tiny real-model runs prove all-value numerical correctness.
