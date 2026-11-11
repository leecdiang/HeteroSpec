# Original seven-arm recorded-work audit

This is a retrospective CPU audit of the original RTX seven-arm campaign, pinned
at paper PR145 commit `85b3f2d6e43ea7d19fb4b0f6827cbd7f492f6fdb`. It adds no model
execution, no input, and no session, and changes none of the original request
clocks, cost values, or statistical weights.

## What was actually checked

All 2,058 archived formal-run `RECORD.json` files were opened and verified against
the original archive `INDEX.json` SHA256 entries. Forty-two warmups were excluded.
The remaining 2,016 records exactly cover the slots in `FORMAL_PLAN_V02.json`:
three families, 12 inputs per family, two adjacent sessions, four repeats, and
seven arms. Matching uses **family, task ID, session, and repeat**, not array order
or an average over different requests. There are 288 matched seven-arm audit groups. The original execution used 42 family/session/arm workers, each with 48 formal requests. These reconstructed groups are not adjacent randomized execution blocks. The schema field `seven_arm_blocks` counts these matched audit groups.

Within each audit group, GS, PQ, and QB form one target-only M triple and one speculative
C triple: 576 triples, or 1,728 pairwise comparisons. Every one matches in all
33 recorded logical-work/decision fields, including proposals generated and
verified, committed acceptance, accepted-prefix and cycle-progress histograms,
target and draft caller rows, caller widths, and rollback counts. The six
fixed-UB1 draft physical-work fields also match in every pair. PQ and QB agree in
all 50 recorded workload fields. GS differs in target physical batching and graph
reuse as expected; those are treatment effects, not failed logical-work controls.

The audit also compares the **complete native token ID arrays and recorded EOG flags**,
output length, terminal ID, stop reason, cached-token count, and truncation flag
with the paired R request. All 1,728 non-R-to-R comparisons match. Before forming
the projection, every original formal record was checked to ensure its normalized
output IDs equal the native response token array, and its normalized workload
equals `response.hs_closeout.workload`. Full endpoint arrays are retained in the
small compressed projection, rather than replaced with lengths or endpoint hashes.

These are exact comparisons on this fixed artifact, not new independent
replications. The statistical unit remains the original two adjacent sessions.
Recorded counters and histograms do **not** establish identical per-cycle event
order or bitwise KV/logit states. They do not allocate the complete-request cost
difference among projections, FFN, attention, graph reuse, or counter overhead.

## Counter meaning and physical/logical distinction

`COUNTER_SEMANTICS.md` is the byte-exact archived semantics document; its SHA256
matches the semantics identity carried by all original formal responses.
`counter_definitions.h` and `counter_export.h` are byte-exact source files, also
unchanged between the original and corrected source hash manifests.

- `target_prefill_calls`, `target_continuation_calls`, and the target caller-width
  histogram count `llama_decode` API submissions. Their row fields count submitted
  logical token rows.
- `draft_continuation_caller_*` are also API-level counts/rows.
- `draft_continuation_*`, `draft_proposal_*`, and `draft_catchup_*` without
  `caller` are physical graph-compute quantities. They are compared separately:
  the draft remains UB1 in every speculative arm, and all six fields match.
- `physical_micrograph_*`, target/draft physical-width histograms, physical
  prefill calls, and `graphs_reused` describe implementation execution. In
  particular, GS changes target physical width and calls by design. A physical
  token-row count is not GPU occupancy or a hardware utilization measurement.
- `accepted_prefix_hist`, `cycle_progress_hist`, attempted/accepted-position
  counts, and verification-width histograms summarize actual committed work.
  Histograms alone do not retain the complete chronological cycle sequence.

The script additionally checks 22 per-request conservation identities, including
proposal destinations, committed output origins, histogram totals, and caller /
physical row accounting, for 44,352 checks over the 2,016 formal records.

The prospective v02 correction explicitly retained the 96 already-completed Qwen
**session0 R/M_QB** records: 48 per arm, covering all 12 tasks and rounds0--3.
Those records retain their original freeze and correction-version metadata.
The remaining 1,920 v02 record labels describe prospective control/freeze, not a
universal executable replacement. Of 42 formal workers, 34 (1,632 formal requests)
use the original `llama-server.exe`; only the eight SmolLM2/Llama M_PQ/C_PQ workers
in both sessions (384 formal requests) use `llama-server-pq-metadata4.exe`.
The full original/corrected source inventories differ only in
`src/llama-context.cpp`, which reserves four times the graph metadata for PQ.
All 21 numerical DLL hashes are identical. Counter definitions/export and the
observer are byte-identical. The QB alias adjustment accepts the actual compiled
tensor alias in the qualification gate; it is not a numerical operator rewrite.
Thus this audit does not assert a single executable for every seven-arm row.
The GS and QB arms retain the original executable throughout. Exact worker
command hashes and runtime identities are retained in the source receipt.

## Reproduce using only this paper package

From the paper root:

```bash
python -B scripts/generate_seven_arm_work_audit.py --check
```

This checks the compressed and expanded input identities, the pinned original
archive INDEX and registered plan, recomputes all pairing/conservation/endpoint
checks from the field projection, and requires exact reproduction of:

- `anc/seven_arm_work_audit/pairwise.csv`;
- `anc/seven_arm_work_audit/summary.json`;
- `tables/seven_arm_work_audit.tex`.

`outputs(root)` returns those relative paths and their deterministic bytes.
`verify(check, root)` integrates with `anc/check.py` using its existing
`check(name, condition)` callback. `--write` regenerates only these three derived
files. Gzip inputs use `mtime=0`; no network, GPU, or third-party Python package is
needed.

## Stronger verification against original records

The compact projection is independently hashable and sufficient for reproducing
the comparisons, but its hash alone cannot prove that omitted raw response bytes
were projected correctly. `source_receipt.json` distinguishes these evidence
levels and records the original-byte audit actually performed. `record_index.csv`
lists each original member, size, and SHA256, including excluded warmups. The
original complete INDEX is preserved byte-exact inside `archive_index.json.gz`.

To independently re-read the original formal response bytes, use one of:

```bash
python -B scripts/generate_seven_arm_work_audit.py --check --raw-root /path/to/extracted_archive
python -B scripts/generate_seven_arm_work_audit.py --check --archive /path/to/RAW_EVIDENCE.zip
python -B scripts/generate_seven_arm_work_audit.py --check --parts-dir /path/to/archive_parts
```

`--raw-root` needs the 2,016 formal original records at the archive-relative paths
in `record_index.csv`; the rest of the large archive need not be extracted.
The script checks every original record's SHA256 against the pinned INDEX,
rechecks the native-response / normalized-field bindings, regenerates the selected
fields, and compares them exactly with the supplied projection.

The split-part route needs only `RAW_EVIDENCE.part001`, `.part007`, and `.part009`
for this subset. These three original files were downloaded and each verified
against both its committed Git blob identity and the archive manifest SHA256.
They contain the original INDEX, all formal-run records, plan and source-package
evidence, and the ZIP directory. No missing part is filled with zeros. This route
does not claim to recompute the full nine-part concatenated archive SHA256; full
ZIP mode does. All archive URLs in the receipt are canonical fixed-commit GitHub
URLs. Access uses the repository's existing permissions; no credential material
is part of this package.

## Suggested paper wording

> A retrospective audit of all 2,016 original formal requests matches GS, PQ,
> and QB by family, task, session, and repeat. Across 576 within-path triples
> (1,728 pairwise comparisons), the recorded proposal, committed-acceptance,
> target/draft logical-work, rollback, and histogram fields agree exactly. All
> 1,728 non-R endpoints also match the paired R request in complete native token IDs and
> recorded EOG flags and terminal metadata. GS changes physical target batching and
> graph reuse as intended. The audit adds no sessions and does not establish
> bitwise internal-state or complete chronological-trace equality.

Do not write that all counters or internal states are identical across GS/PQ/QB,
that physical call counts were held fixed, that the audit adds 1,728 independent
replications, or that all measured service-time savings have been isolated to
projection/FFN execution. E2 remains a separate six-session PQ/QB study and is not
the source of these GS comparisons.
