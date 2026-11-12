# Minimal N1a execution proposal — not admitted

## Frozen semantics and ordering

Keep PR226 REFERENCE_CONTRACT.md, N1A_PROPOSAL_NOT_ADMITTED.json and the
261-check graph unchanged. The new caller is a separately named C4096 descendant,
not a relabeling of the original C1024 binary. R links the independently built
original reference numerical archives; the candidate links the fixed loop4
archives and complete original resident_context.hpp. No modern numerical backend
is substituted. The original R frontend issues a whole initial prompt API batch
with physical ubatch=1; later resident append is one token per API call. Cold's
prefix checkpoint explicitly splits that API sequence at the retained head.
Whether this alignment preserves strict arithmetic is NOT_RUN; a valid conflict
or first byte difference must stop before the candidate, not change the contract.

Prospective order is resident R → independent repeat R → cold canonical oracle
→ strong whole-rechunk+loop4. Each role uses two workers: four fixed natural
two-turn episodes and five named two-request raw-token controls. One context per
worker stays resident inside an episode; episode boundaries explicitly reset.
Cold clears each request and independently computes the actual R canonical IDs
and retained prefix. It never restores R state. Natural repeat and strong paths
generate their own greedy outputs and histories; expected R IDs are assertions,
not a forced proposal tape. Natural inputs and artificial controls stay separate.

R itself passing a repeat does not prove cold equivalence. Eligibility checks
precede raw comparison: same exact model/template/producer/IDs, state time,
position, requested-output mask, pending, ownership and stop semantics. Cold
POST_RECONCILE has a freshly computed frontier; resident invalidates its old
frontier. Compare active KV there, not those deliberately different outputs.
At POST_APPEND and TERMINAL compare all declared complete F32 rows and every
active F16 K/V scalar with strict raw-byte equality and finiteness. No tolerance,
argmax shortcut, new reference or continued timing follows a strict difference.

## Controls and immutable captures

The five fixed controls cover pending append, empty-think LCP trim, fully cached
final-token replay/ownership, unsupported trim and caller-injected failure before
native trim mutation. An unexpected native trim failure always poisons; unchanged
head cannot prove retained KV unchanged. Every real retained prefix is compared
to the previous actual terminal K/V with correct old/new position strides.
The output ownership pair binds source row, before event, actual mutation and
after event. Reset checks actual empty active state and ownership, not inactive
allocator zeroing. Universal EOG/capacity and LOCAL/packed remain N1b work.

The real writer extracts source-specific transposed V and physical-position maps,
emits only active little-endian K/V, and owns complete vocabulary output copies.
It does not keep a second opaque serialized cache. Each state phase is bounded
at 700,000,000 bytes, metadata at 1 MiB, stream chunks at 1 MiB. Immutable
transport files commit last; short/uncertain writes leave failure evidence and
poison. Every natural non-cold request keeps one complete producer receipt,
at most 1 MiB, including actual emitted IDs, stop/cap, wire response, parser
input, history, prompt and next canonical IDs. Oversize is a counted rejection,
never truncation or a rewritten prompt.

Exact planned capture inventory: 252 state checkpoints; 72 owned-output events;
27 reconcile, 36 mutation and 36 ownership-binding receipts; 24 real producer
receipts (R/repeat/strong only). The 32-producer storage allowance is conservative.
All capture phases, tensor transports, identities, row masks and native work
receipts must be complete. The CPU assembler inventories and rejects missing or
unplanned items, then delegates the frozen 261 checks. A complete file set or a
transport hash is not a truthful-native-source certificate.

## Requests, rows and deployment accounting

prepare_jobs.js expands the exact frozen proposal and saved tokenizer IDs without
loading any model or retokenizing the corpus. Its output is a template, not an
executable admitted manifest. Each of four roles has 18 requests: eight natural
requests and ten scripted control requests, totaling 72. Use the exact integer
per-role and per-operation manifest in NATIVE_JOB_TEMPLATE.json. The complete
manifest sums to 69,354 rows. Natural continuation/cold requests reserve their
actual declared integer bounds; all generated rows, independent cold prefix
work and controls are included.

Four requests and 16,384 rows are a proposed terminal failure reserve, giving
76 and 85,738 hard maxima. They are not automatic retry permission and do not
appear as runnable replacement jobs. Stop on first failed qualification,
partial decode, uncertain write, missing stage certificate or budget rejection.
No old STATE reopening, refund, directory change or historical quota transfer.

Ten deployments = two future no-forward resource preflights plus eight workers.
Each reserves one backend initialization, model load, context and placement;
all four axes have maximum ten, separately from model requests/rows. The current
live preflight implementation/admission is incomplete and NOT_RUN. Loader/ELF
placement must be durably reserved before exec; worker verifies that reservation
without charging placement twice. Setup errors consume reservations even before
a request starts. Reset closes the last charged request after reset capture.

Native entrypoints are wired to one protected UNIX-socket broker and one
canonical global successor ledger. CPU mock accounting has tested crash/no-ACK
handling and stream inspection up to a 512 MiB journal ceiling. Its ACK is not
GPU or stage permission. A separately audited controller must enforce one
outstanding worker, strict stage certificates, deadline/quiet-window/space/RSS
guards and safe shutdown. This controller is not delivered as an admitted runner.
No Boolean JSON flag or environment variable can unlock ProductionGate.

## Resource admission and stop rules

review/resource_budget.js derives 553,094,505,923 bytes from raw tensors,
bounded metadata, a 512 MiB journal, worst-case archive, independent restore,
8 GiB build/text allowance and 100 GiB protected free space. The proposal counts
failure artifacts, transport/uncertainty markers and archive entries; an added
opaque KV copy would require recalculation. Stop before a write/reservation
that exceeds its envelope; never delete old data.

Require at least 48 GiB available host RAM (24 GiB worker ceiling plus 24 GiB
reserve), actual measured single-GPU peak plus 2 GiB safety, refreshed disk and
an expressly allocated UUID with CUDA_VISIBLE_DEVICES equal to that one UUID.
Snapshot availability is not permission or a safe-window certificate. No native
RSS/VRAM peak has been measured, so these are proposed gates, not a pass.

Proposed five-hour outer watchdog includes worker timeouts, CPU raw comparisons,
archive/restore/readback and closing margin. Native speed and RPC/fsync rates
are unmeasured. At any missing bound, insufficient resources or unexplained
contract conflict stop safely with spent counters, first difference and partial
captures preserved. Do not create extra calibration requests.

## Go / No-Go

CPU source recovery, compile/link and synthetic safety preparation: completed
with the attached receipts. Actual loaded identity, preflight, all 261 raw native
checks, repeatability, resident/cold equivalence, real producer continuation and
runtime resource enforcement: NOT_RUN or BLOCKED as listed in STATUS.json.
The next review must approve a finite resource manifest and finish the stage
controller/admission implementation before any native executable is launched.
N1a success would only support a further N1b proposal. It would establish no
four-arm, LOCAL, natural-service or performance result; N2 remains separate.
