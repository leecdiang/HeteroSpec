# Completed RTX cohort: retained continuation history

All registered work is complete:1288 primary requests (196 qualification,
1008 formal measurements,84 warmups) and the separate54 Llama diagnostics.
Both families passed the complete three-date audit and analysis. No technical
retry reserve was used. There is no next unit: do not rerun the commands below.
They are retained as execution history. See
[final results](host_execution/day2/RESULTS.md) and
[date2 status](host_execution/day2/DAY2_STATUS.json).

Use the checkout at
`C:\Users\ASUS\Documents\ChatGPT\HeteroSpec\repo`.
The retained bundle is
`C:\Users\ASUS\Documents\ChatGPT\HeteroSpec\repo\work\scope-transfer-bundle-v1`.
Python is `D:\HeteroSpec-PC\python311\python.exe`.

The original execution/source freeze is commit
`011e484b0ec98be800cae4dbcf75e8d9cfdfcbb2`. The current CPU-auditor source binding
is recorded in `host_execution/CURRENT_SOURCE_BINDING.json` and the bundle's
`FREEZE_COMMIT.json`. Read [AUDIT_METADATA_CORRECTION.md](AUDIT_METADATA_CORRECTION.md):
the metadata4 tensor-name correction adds no GPU request and changes no native
runtime or raw record. The original source binding and failed audit are retained.
Do not rebuild, change source, replace a model, re-run qualification or silently
move a frozen date while continuing this cohort.

First inspect `ATTEMPTS.json`, `Qwen-QUALIFICATION.json` and
`SmolLM2-QUALIFICATION.json` in the bundle. Numerical qualification requires the
exact status `NUMERICALLY_QUALIFIED`. `COMPLETE` on a process receipt alone is
insufficient. Inspect any `HOST.lock` and process identity; never delete a lock
or retry an existing attempt merely because a previous chat ended.

Closeout status on 2026-10-29: Qwen and SmolLM2 are both numerically qualified,
98 requests each. Formal measurements, charged formal warmups and Llama
diagnostics are all still zero. No technical retry reserve was consumed.

## Authorized calendar amendment

Before any formal request, the user explicitly approved moving the dates to
October 30, October 31 and November 1. The original October 29 first date
was missed and remains recorded as an incomplete original calendar. This is
a disclosed amendment, not completion of the original calendar or a technical
retry. See [CALENDAR_AMENDMENT.md](CALENDAR_AMENDMENT.md). Qualification is
retained without rerunning any request.

## Formal order

All four date0 units completed on October 30 (Asia/Shanghai):

| Unit | Process interval | Measurements | Warmups |
|---|---|---:|---:|
| `formal/d0/s0/Qwen` | 00:46:08–00:57:35 | 84 | 7 |
| `formal/d0/s0/SmolLM2` | 01:05:42–01:09:13 | 84 | 7 |
| `formal/d0/s1/Qwen` | 01:12:29–01:23:56 | 84 | 7 |
| `formal/d0/s1/SmolLM2` | 01:28:24–01:31:54 | 84 | 7 |

All four processes returned normally and cleanup was verified. The first-unit
snapshot remains under `host_execution/formal-d0-s0-Qwen-a0/`; the first-day
closeout is `host_execution/day0/DAY0_STATUS.json`. Do not rerun any date0 unit.
All four date1 units also completed on October31 (Asia/Shanghai):

| Unit | Process interval | Measurements | Warmups |
|---|---|---:|---:|
| `formal/d1/s0/SmolLM2` | 03:45:01–03:47:55 | 84 | 7 |
| `formal/d1/s0/Qwen` | 03:53:13–04:03:03 | 84 | 7 |
| `formal/d1/s1/SmolLM2` | 04:08:03–04:10:56 | 84 | 7 |
| `formal/d1/s1/Qwen` | 04:14:08–04:24:13 | 84 | 7 |

The date1 audit is `host_execution/day1/DAY1_STATUS.json`. All364 records pass
the public unit gates and the additional date1 PQ/QB canonical-state check.
The original560-request prefix and original six process receipts are unchanged.
Total main requests are924; the independent Llama stream remains54, with zero
new diagnostic requests. Do not rerun date0, date1 or qualification.

All four date2 units completed on November1 (Asia/Shanghai):

| Unit | Process interval | Measurements | Warmups |
|---|---|---:|---:|
| `formal/d2/s0/Qwen` | 00:09:15–00:19:06 | 84 | 7 |
| `formal/d2/s0/SmolLM2` | 00:24:12–00:27:05 | 84 | 7 |
| `formal/d2/s1/Qwen` | 00:30:19–00:40:16 | 84 | 7 |
| `formal/d2/s1/SmolLM2` | 00:44:48–00:47:42 | 84 | 7 |

The earlier924-request byte prefix and ten process receipts remain unchanged;
date2 appended364 requests. All twelve formal processes independently loaded
models, completed on their registered actual dates and cleaned up.
For the retained date2 admission history: November1 at00:00 Shanghai is after the actual
date1 first-session20-hour lower bounds (Qwen October31 23:53:13;
SmolLM2 and daily first October31 23:45:01). The host still checks all gates.
Remaining requests:0. No retry reserve was used.

For the retained date1 admission history:
October 31 at 00:00 Shanghai is later than both first-session 20-hour lower
bounds from October 30. Returning only 20 hours after this day's work can
still be October 30 and cannot start date1. The host must verify the exact
current date, all first-session gaps and midnight headroom at every launch.

Each command below starts a new owned process and reloads both models. Run one
unit at a time, checking the retained receipt before the next unit. The common
command, from the checkout, is:

```powershell
& D:\HeteroSpec-PC\python311\python.exe -B scripts\experiments\rtx_scope_transfer_v1\host.py --bundle work\scope-transfer-bundle-v1 --unit UNIT
```

| Shanghai date | Units in order |
|---|---|
| 2026-10-30 | `formal/d0/s0/Qwen`, `formal/d0/s0/SmolLM2`, `formal/d0/s1/Qwen`, `formal/d0/s1/SmolLM2` |
| 2026-10-31 | `formal/d1/s0/SmolLM2`, `formal/d1/s0/Qwen`, `formal/d1/s1/SmolLM2`, `formal/d1/s1/Qwen` |
| 2026-11-01 | `formal/d2/s0/Qwen`, `formal/d2/s0/SmolLM2`, `formal/d2/s1/Qwen`, `formal/d2/s1/SmolLM2` |

The host checks both per-family and daily first-session gaps of at least 20 hours.
Qualification on October 28 is not a formal date and does not count as date0.
Leave at least the frozen 1,800-second worker limit before local midnight for
each launch. If a date becomes unavailable, retain an incomplete-date result;
do not substitute another date after observing results.

Each family-session has exactly seven charged warmups and 84 measurements.
Neither missing slots nor failed attempts may be filled from another process.
The automatic host command does not spend the optional technical retry reserve.
No numerical failure permits a retry.

## After collection

Run the public `study.py audit` and `study.py analyze` on the retained bundle.
Only a complete family passing every audit gate may contribute a performance
estimate. Preserve all twelve inputs, six sessions and three date points.
The separate 54-request Llama diagnostic completed on October30 and passed its
independent audit. Its stream is outside the main `REQUESTS.jsonl`, at
`D:\rtx151-llama-diagnostic-v2`, with committed evidence under
`sidecar_execution/diagnostic/`. Do not rerun A1/A2 or add diagnostic requests.
No state transplant, extra replay or repair search is authorized.
Incremental archive and readback receipts are tracked under `sidecar_execution`;
historical qualification/day0 closeout snapshots are not live delivery status.

No recurring automation is installed and no future model requests are queued.
The completed protocol does not authorize additional experiments.
