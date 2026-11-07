# 358H formal-execution amendment

Status: **POST-HOC DISCLOSURE — NO FORMAL DATA CHANGED**

This amendment records execution and provenance details discovered during the
repository-closeout audit. It does not alter the frozen workload, measurements,
estimators, confidence intervals, or platform conclusion.

## Formal host state

Immediately before the replacement AC-qualified campaign, the operator and the
interactive qualification session checked the following state:

- external power online; battery approximately 99% and not discharging;
- Windows Balanced power scheme;
- Windows 11 build 26200;
- Intel Arc B390 driver `32.0.101.8991`;
- Intel NPU driver `32.0.100.5540`;
- OpenVINO `2026.3.1` and Python `3.11.9`;
- no pending Windows Update reboot was observed.

These checks were performed before formal generation but were not serialized as
one machine-readable Phase-3 start snapshot. This is a documentation limitation:
the statements above are retrospective records of contemporaneous checks, not a
newly reconstructed hardware measurement. The complete Phase-0 AC evidence
remains under `runs/358h/qualification_ac_20260918/`.

## Interactive monitoring deviation

Brief progress inspections and Windows Task Manager observation occurred during
the formal campaign. The frozen protocol requested avoiding interactive load and
recording any such activity, but the activity was not written into the campaign
status file at run time. It is disclosed here as a protocol deviation.

No formal observation was retried or discarded. All 270 full-campaign records
completed without an error or warning. A post-hoc stability check found:

| Path | repetition 0 GM | repetition 1 GM | repetition 2 GM |
|---|---:|---:|---:|
| CPU draft | 0.725711 | 0.735703 | 0.734567 |
| NPU draft | 0.352073 | 0.352074 | 0.351758 |

Chronological target-only baseline medians by successive thirds were 9533.93,
9545.58, and 9625.73 ms. The deviation therefore shows no material discontinuity
and cannot plausibly move either confidence interval across 1.0. This check is a
robustness diagnostic, not a replacement measurement or a basis for removing any
sample.

## Randomization implementation note

The frozen addendum described an independent three-condition shuffle for every
`task_id x repetition` unit using the frozen condition-order seed. The frozen
driver implemented this deterministically as:

`random.Random(seed + task_id * 1009 + repetition).shuffle(conditions)`

The complete schedule was persisted at `2026-09-18T06:45:04Z`, before the first
formal generation at `2026-09-18T06:45:46Z`. This implementation was frozen in
the pre-formal driver SHA256
`1948e2ecde23b056a0c925952f9e0c8ff1d3055d57af0629be4ed501346ade12`.
It did not depend on observed outcomes. The realized first/second/third position
counts were CPU 28/35/27, NPU 25/27/38, and baseline 37/28/25.

## Metric and correctness boundaries

- The primary Phase-3 metric is **post-prefill decode end-to-end time**. Prompt
  tokenization and prompt prefill are excluded by the frozen boundary. It is not
  a whole-request user-perceived latency measurement.
- Correctness means exact generated token-ID equality with the shared explicit
  Vulkan0 target-only baseline. HumanEval functional execution/pass@k was not
  evaluated and is not claimed.
- The NPU device claim relies on the frozen explicit-NPU cache-binding and
  low-level `EXECUTION_DEVICES=NPU` qualification evidence. OpenVINO GenAI's
  LLMPipeline does not expose that property for every formal observation.
- `FORMAL_PHASE3_STATUS.json.repo_head` records the runner-freeze commit used by
  the campaign record. The separately frozen campaign driver and its SHA256 are
  the authoritative executable provenance; the field must not be interpreted as
  the final PR branch head.

## Rerun decision

No rerun is introduced by this amendment. The paired estimates are stable across
repetitions, both confidence intervals remain far below 1.0, and the complete
local raw evidence is retained byte-for-byte. A future study requiring a
machine-verifiable power snapshot in the formal session itself must preregister
and run a new campaign rather than silently rewriting this record.

