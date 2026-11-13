# Optional canonical-append A/B — design only, not authorized or implemented

Purpose: determine whether the one fewer whole-graph/caller invocation has measurable **append-stage** value when the projection/attention four-column grouping tradeoff is absent. This does not test free generation, complete natural-session latency, third-turn state handoff, EOG, or the original261 suite. Do not use it as a substitute for any of those claims.

Use only [MINIMAL_AB_FIXTURE.json](RESULTS/MINIMAL_AB_FIXTURE.json): the first original source-order node satisfying the inherited short supplied-EOG contract and a positive outer-call gap. No scan for favorable head, speed or acceptance selected it. Its actual saved canonical vector Q has321 IDs, retained prefix232, append89. Keep all original messages, template, model and canonical IDs. W appends24+32+32+1; L appends32+32+25. Both have23 source-derived four-column projection/query groups. No speculative draft or sampling is involved. This is supplied-history **replay**; real free output could change the geometry.

Reuse fixed Qwen3-8B Q8_0, C4096/F16 KV, original sequential R and unchanged loop4 archives. Two independent reference processes run the same Q; one candidate process/model/context then runs both arms, reset between requests. Before every candidate append, rebuild the identical232-token prefix sequentially outside the append timer, and compare its **complete** full-vocabulary frontier and all active KV against R. Decode the exact suffix and compare the complete final vector, all active KV/map/frontier and output ownership against R; finite exact bits, no tolerance or argmax substitute. Every initial prefix reconstruction is explicitly charged. No opaque KV restore, uncharged helper forward or invented producer is used.

| Request | Model deployment | Operation | Prefix setup rows | Append rows | Total rows |
|---|---|---|---:|---:|---:|
|1|R1|independent sequential oracle, capture at232 and321|232|89|321|
|2|R2|independent process repeat, same captures|232|89|321|
|3|candidate|W matched counts-mode warm + full qualification|232|89|321|
|4|same candidate|L matched counts-mode warm + full qualification|232|89|321|
|5|same candidate|round0 W|232|89|321|
|6|same candidate|round0 L|232|89|321|
|7|same candidate|round1 L|232|89|321|
|8|same candidate|round1 W|232|89|321|
|**Upper bound**|**3 deployments / contexts**|**8 logical model requests**|**1,856**|**712**|**2,568**|

Setup is part of each request. Placement is counted before each of the three model loads; reset/capture/CPU byte comparisons do not perform forward work. No failure margin or automatic retry: stop on the first incomplete capture, mismatch, lost resource identity/ownership or deadline, retain debit and mark any remaining panel partial/NOT_RUN. Reference repeat must pass before candidate; both actual warm modes must pass before timing. A failed qualification cannot be offset by a later matching token.

The primary reported timer includes append planning, existing admission/accounting, decode/synchronization, owned final output and controller transport. Report prefix setup and audit separately. **Time the existing per-decode durable budget/guard span separately**, since W4 versus L3 also changes the number of accounting operations. Do not label a saving from fewer durable writes as GPU/backend execution gain, or subtract overlapping timers into a fictitious kernel result. If this small instrumentation cannot be added clearly to the existing runner, stop preparation rather than build another controller. Model loading, prefix rebuilding and all raw comparison/storage still count toward occupation/cost. Preserve both rounds, paired order and per-stage values; no confidence interval or whole-service claim from two pairs.

Resource proposal, requiring new approval:

- 8 requests /2,568 rows /3 model deployments; no old allowance is available. Known rows permit strict pre-admission and per-decode charging under the existing ledger scheme. No separate ledger may evade these totals.
- 30-minute maximum GPU window from first placement, with no new measurement after minute20 and10 minutes retained for exit/archival; a watchdog does not promise recovery of hung hardware. This is a proposed ceiling, not a measured duration or booked quiet window.
- Two captured full F32 vectors per request:16×607,744 bytes. Full active KV at heads232 and321 per request:8×553×147,456 bytes. Total raw upper662,069,248 bytes, plus zero-byte reset captures; propose raw hard cap1GiB and metadata/log cap256MiB.
- Allow8GiB for new raw/builds/metadata plus private archive and readback/restoration copies. Require80GiB free at admission and keep the existing64GiB rolling reserve. No deletion of historical data. The original archives/libraries are reused, not recopied or upgraded.
- Reuse the existing actual user-systemd/cgroup controls, MemoryMax24GiB/swap0/pids128/two CPU equivalents; require host available RAM48GiB and at least12GiB free target VRAM at admission. Reconfirm the device, quiet interval, relevant model/source/image identity, other work and known lease immediately before a separately approved launch. No second GPU or system-policy change.

This prompt authorizes review, not this experiment. The old PR236 state remains closed at43/43 requests and4/4 deployments. The prototype currently lacks this exact fixed-prefix replay entry and the separate accounting timer; this document and the token fixture are **not an executable launcher or a claim of readiness**. Do not open an old deny gate or rerun an old STATE. If the paper does not need this narrow mechanism distinction, stop at the present CPU/previous-GPU evidence instead of spending another allocation.
