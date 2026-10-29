# Continue the frozen RTX cohort

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
The next unit is `formal/d1/s0/SmolLM2` on **October 31**, followed by Qwen,
then the second independently loaded session for SmolLM2 and Qwen.
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
Keep the separate 54-request Llama diagnostic out of `REQUESTS.jsonl`; its
host stream/report are still pending. No state transplant, extra replay or
repair search is authorized by this continuation file.

The user plans to return to this chat to continue; no recurring automation has
been installed and no future model requests are running unattended.
