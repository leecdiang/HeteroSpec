# Local input records (no synthetic task is supplied for science)

`candidates.json`: `{"inputs":[...]}`. Each item has `id`, `domain` (`code`/`math`), `stratum` (`short`/`long`), exact `prompt_ids`, `prompt_ids_sha256`, `cap:128`, `source_revision`, normalized natural-source `text_sha256`, and `tokenization_receipt_sha256`. Hash prompt IDs as SHA256 of compact integer-array JSON (`[1,2]`, not spaced JSON). Source/rendering receipts include raw natural text, tokenizer/template hashes and actual tokenization command. IDs and all hashes are checked for historical exposure across previous branches and local manifests. Output quality or time never enters selection.

`exposure.json`: `coverage_review_complete:true`, arrays `input_ids`, `text_sha256`, `prompt_ids_sha256`, plus inventory sources. Include four calibration items. An incomplete inventory blocks an unseen-input claim; it cannot be asserted complete just to satisfy the parser.

`calibration.json`: `{"inputs":[four already-exposed items]}` with the same item fields. It is deliberately separate from the12 selected tasks. Use both domains and representative lengths where available; do not choose inputs by new14B output.

`preparation_receipt.json`: booleans `natural_inputs_checked`, `exposure_scan_complete`, `tokenizer_template_checked`, `gpu_exclusive`, with the inspected artifact hashes, hardware/power data and reviewer notes. These booleans are a host attestation, not a replacement for the underlying evidence. The preparation receipt is asset-hashed by the runner.

Initial target-only R is generated under this new frozen14B model/runtime/placement. It is not an imported8B answer and is never retrospectively substituted after a candidate fails. R repeatability is checked on heavy/off executions. The same strict reference applies to all candidate arms at each input.
