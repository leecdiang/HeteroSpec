# Qualification tools and frozen expectations

`CASES.json` binds the 11 positive and 11 negative/failure cases from #221 to explicit expectations for A (backend-loop4), B (current packed), and C (same-CTA pair4). All 66 arm/case native results begin `NOT_RUN`. C admits only Q8_0 weights, F32 activation/output, q=8 and g=2. Cases outside C's domain require rejection before native work. The prospective host policy is deliberately stricter than the historical packed branch; it does not retroactively add guards to old binaries.

`src/admission.py` uses explicit `AdmissionError` checks. Full vocabulary vectors require exact F32 byte length, finite entries, and a bound artifact SHA-256. Complete native sequence state is parsed independently, with exact active positions, layer/row types and widths, dense sequence-0 mapping, and no trailing bytes. The bundle requires both untrimmed/pre-trim target/draft exports and committed exports with matching stage geometry. A state from a different frontier cannot stand in for the required pre-trim evidence. The active hash has a new canonical header and must not be compared to old validators' active hashes without recomputing both inputs here.

Identity checks bind model and vocabulary separately from core, frontend, executable, compiler, loaded DLLs, producer, KV, graph policy and actual device. `validate_bundle` requires independently supplied frozen vocabulary size and complete requested row IDs; a record cannot shrink its own declared request contract. `admit_descriptor` requires an independently frozen authorized physical UUID and rejects a different SM120 device. Logical and dispatched projection descriptors are checked independently for each arm. Requested outputs must be owned copies. Shape alone is insufficient for graph reuse: changed prefix vector, active/layout policy, head placement, output count, topology or recipe requires rebuilding.

Pre-execution rejection, separately qualified fallback, and owner invalidation are different decisions. `FALLBACK_ALLOWLIST.json` is empty. A fallback's self-reported `NATIVE_QUALIFIED` status is insufficient; its complete receipt digest must appear in a separately frozen trusted allowlist. The new wrapper owner invalidates after failures once native work has started, including trim/draft/sample/reset-postcheck failures. This host model has not been wired into or tested as a native persistent service; the historical worker retains its own target-poison/CLI-termination boundaries.

Clean binding requires a source-bound always-on guard receipt. A heavy capture observer or its default `bad=false` cannot supply that receipt. Host success, capture success, native correctness and clean performance qualification remain separate evidence layers.

Run the host tests with a real Python executable:

```powershell
python -m unittest discover -s tests -p test_admission.py -v
python -O -m unittest discover -s tests -p test_admission.py -v
```

`compare_operator_pair` checks complete quantized activation buffers including padding and every finite output element using independent frozen expected sizes. Equal argmax with changed nonmaximal outputs is rejected.

`host-checks-v1` preserves the initial checks. Independent review found two missing external bindings in that version: request row/vocabulary declarations and the authorized device UUID. `host-checks-v2` records the corrected sources. `host-checks-v3` adds the complete-buffer operator comparison and records ordinary/optimized checks without overwriting either earlier receipt. These are constructed CPU fixtures, not model or GPU observations. No native numerical or performance claim follows from them.
