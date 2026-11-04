# Independent review reproductions

These are standard-library-only Python tests of a design abstraction, not native inference or GPU tests. Read [the review](INDEPENDENT_REVIEW_20261104.md) before interpreting their results.

Requires Python 3.10+ without `-O` (assertions are the checks). The scripts pin the exact reviewed model SHA256 and fail if it changes. By default, they expect `check_transaction_model.py` in their parent directory. `--model` can point to another copy of those same bytes.

From the repository root after placing this directory at `runtime_qualification/independent/`:

```sh
D=docs/research/reference_contract_20261104/runtime_qualification
python "$D/independent/review_transaction_adversarial.py" --model "$D/check_transaction_model.py"
python "$D/independent/review_schedule_premises.py" --model "$D/check_transaction_model.py"
```

Compare the printed JSON with `transaction_adversarial_results.json` and `schedule_premise_results.json`. An optional `--output /path/to/result.json` saves the same JSON; omit it for a read-only run. These scripts do not download data or access the network.

The 500 special-value scalar-toy cases and the 200 bounded-input padded-QK/softmax/PV cases are distinct tests, with distinct numerical domains. Neither is a real-attention, GPU, universal-value, or performance result. Observer and unsafe-alias fixtures intentionally violate stated premises; the final candidate is separately required to reject aliases.

`source_identity_results.json` records the independent check of 12 staged-source file hashes. Reproduce using the parent `verify_source_manifest.py` and an authorized staged source copy. The review's identity check did not include the source-kit archive.

`SHA256SUMS` lists the exact review, scripts, and result files in this bundle. It excludes itself. `reviewed_artifacts.json` records the separate design/model/source-manifest hashes to which this review applies.
