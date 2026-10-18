# RTX dispatch intervention v1 — completed with negative qualification

Actual result: **302 native hosts / 9,228 graph calls**; both sessions and8 blocks
finished. **208/256 clean slots qualified;48 never started** after twelve planned
qualification hosts exposed exact-reference mismatches. All failures retained.

L1023→S1024 does not preserve reference bytes. L1023→S1025 qualifies, retains8
kernels and costs about1.5% more than both controls. T0 ON compact-QH integrated
transactions show no practical benefit against both identical QB controls.
Keep QB and **SOFTWARE_FIRST/HOLD**. No further precision hunting for these inputs.

Read [RESULT.md](RESULT.md), [EVIDENCE_NOTES.md](EVIDENCE_NOTES.md), generated
[results](results/) and exact [execution artifacts](execution/). Full raw is local;
all7,860 members restored and a new interpreter reproduced scientific exports.
Local restore, remote compact-artifact verification and external review are
separate claim levels. UUID is permanently closed; no old experiment resumed.

The original design below is historical. No model/decoder/actor/hardware tasks.

---

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
