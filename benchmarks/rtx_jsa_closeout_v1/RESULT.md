# RTX JSA closeout: S0 missing coverage

**S0_BLOCKED_MISSING_COVERAGE. No calibration, E1 or E2 model request started.** This is the result disposition permitted by PR #140, not a completed numerical/performance study. The design PR stays open. No held-out panel, implementation freeze or execution authorization is claimed.

The recovered PR104 ancestry uses the original MBPP/GSM8K descriptions and instruction prefixes, target-template-once formatting, Q8_0 weights and native vocabulary. We exhaustively tokenized all 427 locally pinned sanitized MBPP tasks and 1,319 GSM8K test questions, including already exposed tasks. Each target/draft pair produced identical vocabularies and token IDs. Six vocabulary-only processes created zero inference contexts and made zero model forwards. All six exited successfully; their native stdout, stderr, identities and exit receipts are archived.

| Family | Natural inputs | 64–192 tokens | 256–448 tokens | 640–832 tokens | Maximum |
|---|---:|---:|---:|---:|---:|
| Qwen3 | 1,746 | 1,110 | 0 | 0 | 210 |
| SmolLM2 | 1,746 | 1,681 | 0 | 0 | 230 |
| Llama | 1,746 | 1,727 | 0 | 0 | 230 |

Each stratum requires four inputs per family. These are **unfiltered upper bounds**, not exposure-cleared eligible counts. Excluding prior use cannot increase a count of zero. Thus the recovered original pool cannot supply either the medium or long stratum, regardless of the outstanding all-branch/archive exposure audit. No selected-input IDs, task replacements, padding, repetition, truncation, new corpus or shorter length fallback were introduced. This establishes a gap in this recovered pool, not the absence of suitable natural inputs in other datasets.

An independent standard-library implementation rebuilt every normalized token-count/text-hash/token-ID-hash row from the native stdout and query bytes: **5,238/5,238 rows**, with exactly the same census. The verifier also passed on a fresh archive extraction in a separate interpreter. This is a same-host reconstruction, not external certification of held-out status, model outputs or runtime behavior.

## Other S0 findings

The two inherited arm executables and all 21 numerical DLLs match their recorded PR104 hashes; all six model files match the model contract. Original family-specific PQ routing is retained. The detected device and driver agree with the historical RTX 5070 Ti Laptop GPU / 616.92 identity. File recovery does not itself qualify loaded modules or numerical behavior in a new worker.

Exactly one stronger candidate was reviewed: the same pinned runtime's native flash-attention route with the original draft-simple k3 protocol, F16 KV and unchanged sampling/endpoints. The local-repair source guards require flash attention off while the unrepaired native branch exposes flash attention. Its prospective candidate therefore requires repair mask 0 and flash attention on. This is **SOURCE_ROUTE_IDENTIFIED_NOT_QUALIFIED**; no calibration ran, no family is admitted and there is no stronger-baseline speedup claim. No alternative comparator was searched by pilot speed.

The PR104 capture helper selects one layer and one matching q/phase snapshot and then marks that phase done. It cannot directly furnish PR140's complete first/middle/last-layer geometry plus all matched target/draft decision vectors and transaction state. A separately identified observer adaptation, complete host registration and independent qualification would still be needed if a revised input pool were approved. They were not implemented after the decisive coverage stop.

The stated maximum worker budget also needs reconciliation before any future registration. E1 core (108), conditional FAST E1 (36), core E2 (576) and conditional FAST E2 (144) already require **864 workers before calibration**, exceeding the stated 852 maximum. Calibration worker grouping is unspecified. With one fresh capture/count-pair worker per calibration input/arm it adds 24, giving a concrete 888-worker scenario. This report does not silently raise the cap or treat that grouping as a protocol requirement. The 1,776-request arithmetic does reconcile.

## Accounting and limits

`MODEL_SLOTS.csv` retains all **1,776 possible request slots** as `NOT_RUN_S0_MISSING_COVERAGE`, including 576 explicit core warmups and 144 conditional FAST warmups. Inputs remain unbound symbolic positions. `WORKER_SCENARIO.csv` enumerates the 888-worker paired-calibration scenario solely to expose the budget conflict; it is not an executable registration. No timings or output-equivalence flags were fabricated, and the normalized performance estimator was not called.

The original registration template remains incomplete. S0 froze a bounded static-census plan (six vocabulary processes, 1,800 seconds, 512 MiB storage reservation, 4 GiB memory reservation, 30-second cleanup reserve and 240-second per-child timeout). These reservations are not evidence of OS-enforced memory limits. Actual census-owned wall time was 40.470422 seconds; all six exit receipts are present. Model/GPU-worker charges are zero. Interactive shell/API/compiler orchestration was not globally censused, and remaining scientific quota was not certified. Historical cumulative ledgers were neither reset nor rewritten; their full reconciliation remains pending.

There was a control deviation: the intended pre-census Git commit failed because the new sparse checkout omitted the result directory and lacked a local author identity. The shell continued into the static census. The plan existed on disk first, but the census did **not** have a committed/remote prospective freeze. This evidence is therefore an explicitly unregistered read-only inventory, never a formally frozen native study. The failure is preserved in `CONTROL_DEVIATION.json`; no scientific slot was started or retried. The locally written census-source hash was verified at entry. Subsequent packaging does not retroactively cure the missing commit.

## Disposition

PR140's instruction to stop before candidate evaluation when a stratum cannot be filled applies. The RTX numerical and cost claims remain untested on new/longer inputs. An author-approved prospective amendment specifying a natural, licensed input source and reconciling process ceilings is necessary to proceed. It must also precede full exposure exclusion, actual input/implementation/order/resource freeze, calibration and E1/E2. This result does not authorize those changes, a different k/model/precision sweep, another device, or paper/arXiv submission. See `PAPER_ADDENDUM.md` for the resulting claim boundary.
