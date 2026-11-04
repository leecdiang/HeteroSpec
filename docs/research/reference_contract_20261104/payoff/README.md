# Saved-data payoff audit

This folder is a standalone CPU-only companion to the reference-contract research. Start with [REPORT.md](REPORT.md). It does not modify historical measurements or establish new GPU performance.

## Reproduce

Run from any directory:

```sh
python /path/to/payoff/analyze_payoff.py --out /tmp/payoff-analysis.json
```

Python 3 standard library only; no model, compiler, CUDA, GPU, network, or package install is required. The script authenticates `data.json` against `sources.json`, checks all 36 PR171 service records and all 48 PR177 disjoint phase sums, verifies the two pinned checkpoint headers match, and regenerates `analysis.json` calculations.

`data.json` is a compact deterministic field projection of existing frozen repository artifacts, not new observations. Full source URLs, exact commit IDs and original-file SHA256 values are in `sources.json`. To independently regenerate this projection, download those originals using the local filenames used as manifest keys, then run:

```sh
python build_inputs.py /path/to/original-downloads
```

This authenticates every original byte and requires the regenerated projection hash to match. It performs no downloads itself. `analysis.json` is a saved result; values can be regenerated from the packaged input alone. The compact-data calculation was also checked for semantic equality against a run using the complete original artifacts.

## Interpretation boundaries

- Phase budgets are optimistic opportunity ceilings/sensitivity calculations, not measured speedups over backend-loop4.
- PR177's eight conditioned roots cannot be generalized to a representative or production population.
- The 20% phase-reduction and 1% added-service-cost scenarios are explicitly hypothetical.
- PR174 cumulative import is not subtracted to claim isolated GPU append timing.
- Full-logit and last-row service observations are different contracts; the former cannot silently drop required outputs.
- No experimental PR is merged and no original results or manuscript are changed by this folder.
