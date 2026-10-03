# B570 prefill diagnostic v1

360/360 formal units independently verified; archival completion pending. G0 passed; 72 T1 predictions sealed before first N1. All 24 tasks previously exposed.

 | Task | Group | T0/N0 | T1/N1 | N0/R | N1/R | Stable |
 |---|---|---:|---:|---:|---:|---|
 | HumanEval/58 | control | 3/3 | 3/3 | 3/3 | 3/3 | True |
 | HumanEval/156 | control | 3/3 | 3/3 | 3/3 | 3/3 | True |
 | HumanEval/134 | diagnostic | 3/3 | 3/3 | 0/3 | 3/3 | True |
 | HumanEval/42 | diagnostic | 3/3 | 3/3 | 0/3 | 3/3 | True |
 | HumanEval/122 | control | 3/3 | 3/3 | 3/3 | 3/3 | True |
 | HumanEval/114 | control | 3/3 | 3/3 | 3/3 | 3/3 | True |
 | HumanEval/93 | control | 3/3 | 3/3 | 3/3 | 3/3 | True |
 | HumanEval/115 | control | 3/3 | 3/3 | 3/3 | 3/3 | True |
 | HumanEval/151 | control | 3/3 | 3/3 | 3/3 | 3/3 | True |
 | HumanEval/63 | control | 3/3 | 3/3 | 3/3 | 3/3 | True |
 | HumanEval/125 | control | 3/3 | 3/3 | 3/3 | 3/3 | True |
 | HumanEval/133 | control | 3/3 | 3/3 | 3/3 | 3/3 | True |
 | HumanEval/43 | control | 3/3 | 3/3 | 3/3 | 3/3 | True |
 | HumanEval/139 | control | 3/3 | 3/3 | 3/3 | 3/3 | True |
 | HumanEval/77 | control | 3/3 | 3/3 | 3/3 | 3/3 | True |
 | HumanEval/35 | control | 3/3 | 3/3 | 3/3 | 3/3 | True |
 | HumanEval/27 | control | 3/3 | 3/3 | 3/3 | 3/3 | True |
 | HumanEval/34 | control | 3/3 | 3/3 | 3/3 | 3/3 | True |
 | HumanEval/145 | diagnostic | 3/3 | 3/3 | 0/3 | 3/3 | True |
 | HumanEval/82 | control | 3/3 | 3/3 | 3/3 | 3/3 | True |
 | HumanEval/154 | control | 3/3 | 3/3 | 3/3 | 3/3 | True |
 | HumanEval/78 | control | 3/3 | 3/3 | 3/3 | 3/3 | True |
 | HumanEval/96 | control | 3/3 | 3/3 | 3/3 | 3/3 | True |
 | HumanEval/138 | diagnostic | 3/3 | 3/3 | 0/3 | 3/3 | True |

Simplified predictor transfers to this prefill intervention across preserved native/H1 callers; reference recovery is separately bounded to listed tasks.

{
  "status": "MEASUREMENTS_VERIFIED_PENDING_ARCHIVE",
  "planned": 360,
  "valid": 360,
  "failed_units": 0,
  "attempts": 360,
  "task_units": 24,
  "repeat_stable_tasks": 24,
  "g0": "PASS",
  "seal": "PASS_LOCAL_ORDER_ONLY",
  "comparisons": {
    "T0_N0": 72,
    "T1_N1": 72,
    "N0_R": 60,
    "N1_R": 72
  },
  "diagnostic_reference_recovery": {
    "count": 4,
    "denominator": 4,
    "tasks": [
      "HumanEval/134",
      "HumanEval/42",
      "HumanEval/145",
      "HumanEval/138"
    ]
  },
  "controls_reference_regressions": {
    "count": 0,
    "denominator": 20,
    "tasks": []
  },
  "new_knowledge": "Simplified predictor transfers to this prefill intervention across preserved native/H1 callers; reference recovery is separately bounded to listed tasks.",
  "limitations": [
    "24 previously exposed tasks; repeats support stability only",
    "H1 and native preserve different caller prefill grouping; UB capacity alone is not execution shape",
    "KV serialized bytes and pending sample checked; opaque sampler bytes unavailable",
    "Graph tensor observation does not identify unique backend kernel or hardware cause",
    "Local order has no independent absolute timestamp certification",
    "Windows OS build changed; fresh G0 and all baseline regression required",
    "No performance, energy, correctness or HumanEval functional-pass-rate conclusion"
  ],
  "created": "2026-10-03T21:19:08.604733+00:00"
}
