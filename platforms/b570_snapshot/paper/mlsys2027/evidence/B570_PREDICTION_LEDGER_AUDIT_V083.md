# B570 Prediction Ledger Audit — Phase 1

## Inputs

- `benchmarks/b570_mechanism_v08/hypothesis_freeze.json`
- `benchmarks/b570_mechanism_v08/RESERVED_PREDICTIONS.json`
- `benchmarks/b570_mechanism_v08/RESERVED_VALIDATION_SET.json`
- `benchmarks/b570_mechanism_v08/VALIDATION_ANALYSIS.json`
- `benchmarks/b570_mechanism_v08/DISCOVERY_ANALYSIS.json`
- `benchmarks/b570_mechanism_v08/exposure_inventory.json`
- `benchmarks/b570_mechanism_v08/INDEPENDENT_VALIDATION.json`
- `benchmarks/b570_mechanism_v08/POST_RUN_INPUT_AUDIT.json`
- `benchmarks/b570_mechanism_v08/PREDICTION_RAW_MANIFEST.json`
- `benchmarks/b570_mechanism_v08/OUTCOME_RAW_MANIFEST.json`
- `benchmarks/b570_mechanism_v08/HYPOTHESIS_FREEZE.md`
- `benchmarks/b570_mechanism_v08/PREDICTION_FREEZE.md`
- `benchmarks/b570_mechanism_v08/RESERVED_PREDICTIONS_SHA256.txt`
- `benchmarks/b570_mechanism_v08/VALIDATION_REPORT.md`
- `scripts/platform/b570_mechanism_v08/study.py`
- `scripts/platform/b570_direct_id_v1/common.py`
- `artifacts/b570_mechanism_v08/raw/reserved_predictions/executions.json`
- `artifacts/b570_mechanism_v08/raw/reserved_outcomes/executions.json`
- `artifacts/b570_mechanism_v08/raw/reserved_predictions/checkpoint.json`
- `artifacts/b570_mechanism_v08/raw/reserved_outcomes/checkpoint.json`

The two raw execution JSON files are retrieved from tracked Git objects when absent from the checkout. Their bytes match their canonical manifests.

## Reconstruction

72 run rows, 24 prompts, 3 repetitions. Complete generated-token IDs, prompt IDs excluded, cap 128, earlier EOG inclusive; full-array equality and zero-based first divergence.

## Commitment verification

Recomputed prediction-file SHA-256: `0201ccd1f67492510d34be567aa83f1c38d3bd1f162a970c05d3cea9d3957826`. Frozen expected SHA-256: `0201ccd1f67492510d34be567aa83f1c38d3bd1f162a970c05d3cea9d3957826`. **PASS**. Git prediction commit contains byte-identical content. Hypothesis content digest is byte-verified against the prediction record and freeze commit.

## Chronology

H1 freeze 2026-09-29T10:35:04.415251Z; reserved inference begins 2026-09-29T10:35:41.602565Z; prediction file completed 2026-09-29T11:03:46.794920Z; prediction checkpoint commit 2026-09-29T11:04:57Z; first live run 2026-09-29T11:05:18.166783Z. Push time UNKNOWN; the outcome stage records that it checked the pushed checkpoint. Git commit times are repository metadata, not independent publication proof.

## Recomputed outcomes

UB1 predictor/live 72/72; UB128 reference/live 60/72; prompt classification 24/24; first divergence 12/12 over 4 divergent prompts. Discovery supports H1 in 36/36 archived pairs.

## Evidence completeness

All 72 predictions and 72 live outcomes exist. Each pair is bound by complete-array SHA-256 and an exact task/repetition key. All 24 prompts fit the compact ledger. The audited retained records report no known B570 exposure; they cannot prove no earlier exposure anywhere.

## CR-01 verdict

**FULLY ADDRESSABLE FROM EXISTING RECORDS.** The evidence gap is NO; the presentation/inspectability gap is YES.

## CR-02 verdict

**ADDRESSABLE FROM EXISTING RECORDS.** Reference trajectory agreement is 60/72 versus frozen UB1 predictor agreement 72/72, without a new experiment. UB128 was a reference trajectory, not a prospectively registered failed mechanism predictor.

## Anonymity verdict

Anonymous appendix candidates: content digest, task IDs, lengths, truncated per-sequence digests, event ordering. Review UTC timestamps for linkage risk. Keep Git SHA, repository URL, username, local path, hostname, public artifact URL and identifying branch name out of the anonymous PDF.

## Scientific integrity

No new inference, data substitution, manual result entry, or modification of closed evidence. This Phase 1 file does not revise the manuscript.
