# Evidence integration audit — v0.8.5

Document/build delivery complete; **evidence-access coverage is partial** at
explicitly unavailable original v084 ZIP and 358H runtime raw traces. This is
not an assertion that every original executable passes unmodified on POSIX.
Current versioned reports distinguish RERUN_PASS, RERUN_FAIL,
PRIOR_RECEIPT_ONLY, UNAVAILABLE and NOT_APPLICABLE by actual scope.

## Source and preservation

Started from exact merged main `98e8470f2559f78335de8d3473997d21b4bb55b8`
in an independent worktree; PRs 40–43 are ancestors. Origin/main still equals
that baseline at final fetch. Author's original clean v083 checkout stays
untouched. The official title and three contributions remain; all 3,015
protected existing benchmark/script/archive/report/analysis/evidence/style/
figure/output files and three old numeric macro files match baseline Git
blobs. Figure 3 source, geometry, PDF/SVG, data and checks remain unchanged;
v084 Figure 2 and original B570 commitment tables are preserved. The author
freeze tag still peels to `1d3b556c93b477680788dfd1eb0737dfe9eee28c`.
The Appendix A4 placement change removes forced pagination only, retaining
all data/provenance. There are no unresolved unexpected protected differences.

Old guidance to wait for author integration approval is historical; the
current explicit user instruction authorizes integration and Draft PR.
Existing older no-integration closeouts remain byte-intact. No new inference,
hardware measurement, parameter search or formal/mock review was conducted.

## Argument and denominator checks

The study ledger/projection binds canonical SHA256, full task IDs, runtime/
reference, endpoint, conditions, execution versus comparison counts, primary/
secondary estimator, freeze order, allowed/excluded claims and manuscript
locations. Old historical H, fresh reference qualification Q, frozen
prediction P and sampled intervention endpoints are separated in §2/§3.
The three studies are connected in abstract/contributions, methods, §5,
synthesis, related work, limitations/conclusion, Table 2 and Appendix K–O.

- Original B570 UB1 H1 remains 36/36 discovery, 72/72 reserved prediction/live
  on 24 repeat-stable prompts, four divergent from UB128 reference (60/72).
- New B570 forks have 72/72 score changes, zero raw-top1 and immediate ID
  changes, 195 correlated paired decisions, and 18 later differing runs on
  six prompts. The sampled block starts at ≥64 IDs; source KV/clone/R0
  controls are audited. Code and capture arrays confirm alternate target
  remains UB128 on later blocks and draft proposals follow alternate
  history; no immediate sampled reference-restoration claim is made.
- Earlier RTX H1 matches 24/36 discovery, leaves no selected hypothesis,
  has H2 unavailable in that frozen arm and zero reserved runs. Separate
  V2 H2 uses application/API/process isolation with draft-only P and
  target-only R/R_ONLY; shared numerical code, draft-dependent construction
  and lack of adversarial OS isolation are disclosed. Discovery matches
  36/36; formal runs total 288. Each prediction comparison matches 72/72,
  reference comparison 60/72. Four stable divergences are /17 4:1406→271,
  /33 8:14937→4210, /14 4:1406→271, /22 0:1499→750.
  Each H2/R_ONLY/live endpoint has 63 EOG runs on 21 prompts plus nine cap
  runs on three; reference has 66 EOG on 22 plus six cap on two.
- Fresh latency has 180 runs/90 pairs, direct-ID 90/90, canonical target/
  serialized ratio 0.6458157742698286, CI [0.629802205379344,
  0.6598843928244866], 0/30 faster prompts. Independent fsum replay is
  0.6458157742698285 (one ulp; explicit absolute tolerance 1e-14).
  Native clock endpoint, synchronized prefill boundary, per-request
  sampler/state, debug logging/response, excluded loading/prefill/teardown
  and empty-hook versus total logging limits are stated. Historical 0.650
  and Figure 3 are not replaced; no qualified same-study batched timing.
- M4 retained primary 1.3114 Guard / 1.3469 Always and adverse paired
  secondary Guard/Always 1.0270760219826773 with CI wholly above one;
  distinct Guard/oracle regret remains 1.0278. 358H combined replay/proposal
  58.35% is inseparable, CPU complete target 87.34%, runtime qualified
  intervention absent, no formal performance/energy or stronger source
  identity claim. No functional HumanEval pass@k result is inferred.

## Actually executed verification

Fresh archive reconstruction under `tmp/qa-v085/archives-final` verifies all
49 B570 part lengths/digests, full archive and 888 manifest files. The
unmodified sealed complete entry records RERUN_FAIL solely because POSIX
Path.name treats recorded backslashes differently. The new adapter replaces
only that module's Path.name Windows-basename interpretation; all original
assertions stay active and the scientific checks pass. The original failure
is retained as a separate nested RERUN_FAIL, not erased by the adapted PASS.

All three RTX H2 parts, full 4,165-file capsule, 3,701-file anonymous capsule,
Git blob/tree membership, reported freeze-before-live order, retained exposure/
selection and tapes were actually checked. Derived ordinals and file hashes
are not trusted process clocks or a remote filesystem re-scan. Earlier
RTX prediction and latency archives each rerun their own scientific and
provenance verifiers. M4 complete archive and 638-check secondary raw replay,
original B570 H1 manifest/Git/5,696 extracted-archive checks (the historical manuscript receipt remains 5,681) and both original 270-run direct-ID
archives were rerun. Nine accessible archive families are RERUN_PASS; 358H
runtime raw traces are UNAVAILABLE. External omitted asset bytes are outside
scope rather than silently authenticated.

Current `make check` passes 159 checks and four rejecting counterexamples:
H2 mislabeled QUALIFIED; changed prediction ID; reversed latency ratio;
missing actual source ZIP dependency. The historical 228-check numerical,
136-check runtime and 71-check Figure 3 validators were rerun with only new
output receipt names redirected in memory; their assertions and historical
receipt bytes are preserved. No earlier receipt is substituted for these
reruns. Old closeout assessments not rerun are PRIOR_RECEIPT_ONLY historical
context. New hardware inference/performance is NOT_APPLICABLE to this task.

## Build, policy, anonymity and visual checks

A source-identified v084 baseline was independently compiled (10+2 main,
8 appendix). Final v085 uses actual current dependencies in fresh directories,
then another independent extraction of the final 41-file source ZIP; both
plain latexmk builds match every page's text and count. Final main is 10+2,
appendix 10 and internal proof 8+2. No stale PDF/aux was reused or renamed.
PDF font embedding/official Times, logs, labels, citations, complete author
lists, duplicate keys, metadata/actions/URIs/attachments and source ZIP
anonymity passed. Current bibliography has 19 entries by actual cited set,
not a hardcoded fixed-count requirement. Underfull warnings are retained
and visually assessed; zero overfull or undefined citation/reference errors.

Official CFP was fetched on 2026-10-01 from
https://mlsys.org/Conferences/2027/CallForResearchPapers;
its exact HTML SHA256 and official style URL are in OFFICIAL_CFP_STYLE_V085_QA.
The actual linked case-sensitive MLSYS2025 ZIP was downloaded; all five
vendored .sty/.bst files are byte-identical. Main body ≤10 pages, two columns,
full author lists, separate appendix and research-track double blind hold.
Final 32 pages were individually viewed; delivery PNGs match reviewed images
byte-for-byte. See VISUAL_QA_V085.md/json for page-by-page notes and repairs.

Anonymous compact exports omit identity, absolute paths/times, repository
URLs and Git author metadata; original 72 B570 arrays are compared element
by element. Exact old v084 ZIP is UNAVAILABLE and was not overwritten.
The existing H2 anonymous capsule stays separate with exact hash/filename;
retained hashes may link to original public evidence and do not ensure
unlinkability. Sanitized chronology does not certify original absolute time.

## Delivery and remaining scope

Content/build commit is made first; final artifact manifest and delivery
closeout are committed separately, avoiding a self-referential HEAD hash.
The PR stays Draft. Remaining access gaps are documented above; model/backend
transfer, unique causality, functional correctness, logging-free deployment
performance and persistence benefit remain untested science, not authoring
blockers. Next is independent author-initiated submission-level review of
these exact artifacts/PR. No acceptance prediction, merge, tag or submission.
