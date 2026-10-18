# RTX dispatch intervention v1

DESIGN_ONLY; stacked on PR122. Read [PROTOCOL.md](PROTOCOL.md) for the scientific
contract and [RTX_PROMPT.md](RTX_PROMPT.md) for the Chinese execution handoff.

This package contains a CPU-only schedule generator, visibility specification,
regression tests and a generated frozen design plan. Windows native adaptation,
measurement, admission manifests and scientific analysis are RTX-platform work;
there are no new GPU results here. Do not mistake PLAN.json for an executable
GPU job manifest or the mask helper for a strided tensor implementation.

```
python -m unittest discover -s benchmarks/rtx_dispatch_intervention_v1 -v
python benchmarks/rtx_dispatch_intervention_v1/plan.py --output NEW_PLAN.json
```

Outputs use exclusive creation; do not overwrite a prior run. The plan hash is
SHA256 of sorted compact JSON excluding the plan_sha256 field. Platform freeze
must also bind actual source/runtime/input/reference hashes and admission.

Default B0/T0: 128 clean hosts each, 48 qualification and 40 fresh reference hosts
in total. Only qualified arms execute their reserved clean slots; report all gaps.
No old GPU run is resumed. Negative qualification is a valid stopping outcome.
