# v0.7 prospective direct-ID qualification integration

Current author-review sources and outputs use v0.7. The new RTX/B570
qualification studies are separate from historical timing: RTX 75/90 to
90/90; B570 60/90 to 78/90, with a frozen 90/90 gate. Figure 3 separates
historical physical opportunity and fresh qualification. The historical
comparator record, old outputs and approved figures remain preserved.

Build with `make all hardware-only overleaf`, then `make check`. With an
existing Tectonic executable, run
`python scripts/build_v07.py --tectonic PATH_TO_TECTONIC` from the manuscript
directory. Run `python scripts/render_v07.py` and inspect every page.
All checks are offline; no model inference or parameter search is required.
Portable archive checks replay retained evidence, not omitted weights.

Delivery: `manuscript-v0.7.pdf`, `appendix-v0.7.pdf`,
`hardware-only-v0.7.pdf`, and `overleaf-direct-id-integration-v0.7.zip` under
`manuscript/output/` (or `output/` in the manuscript directory).
See the v0.7 scope/audit, versioned QA receipts, `MANUSCRIPT_STATUS.md`, and
`reviews/submission_v07/` for final pagination and independent review.
This is a draft for author review; the PR must remain Draft and unmerged.
Earlier status sections below are historical.

---

# v0.6 paired M4 Guard versus Always-Spec secondary analysis

Current review: `reviews/M4_GUARD_ALWAYS_SECONDARY_RESPONSE_V06.md`. Current
PDFs: `manuscript/output/manuscript-v0.6.pdf` and `manuscript/output/appendix-v0.6.pdf`.
This reviewer-requested post-study contrast uses only frozen raw observations:
Guard/Always-Spec = 1.0270760219826773, 95% prompt-bootstrap interval
[1.0129560055428655, 1.0435592653980876]. The interval lies above parity;
Guard had higher latency on this comparison. Prompt medians favor Guard on
24 prompts and Always-Spec on 36, with no ties. No new measurement or policy
change occurred. All v0.5 review qualifications remain in force.

# Current manuscript: submission review v0.5

The experimentally complete manuscript and runtime integration have received independent scientific, statistical, novelty, adversarial, writing, visual and artifact reviews. See `SUBMISSION_REVIEW_V05.md`, `manuscript/README.md`, and `reviews/submission_v05/`. Current review outputs use the v0.5 suffix. Earlier roadmap/status text below is historical, not a request for further experiments.

---

# MLSys 2027 paper workspace

Target venue: **MLSys 2027 Research Track**.

This directory is the controlled writing workspace for the HeteroSpec paper. It is intentionally separated from platform reports and raw experiment archives.

## Authoritative control file

`PAPER_FRAMEWORK_HANDOFF.md` is the scientific framework handoff / evidence ledger / claim taxonomy / decision log and is the single source of truth for paper claims.

If any outline, compact status note, generated summary, or historical report wording conflicts with the handoff, first determine whether the conflict is historical provenance or a living-document error. Preserve historical experiment records; repair living paper-control documents instead of weakening repository evidence.

## Current status

- Four hardware campaigns: **scientifically CLOSED**.
- 358H Phase 3: complete and merged.
- Scientific audit Rounds 1–12: complete and merged through PR #13.
- Terminal revalidation: maintained on `paper/final-audit-20260919` until reviewed.
- Scientific thesis and contribution ordering: frozen for drafting, subject only to explicit evidence-driven revision.
- Exact title wording: not frozen.
- Runtime/software co-design: future work; not a current measured contribution.

## Current writing policy

- Write from tracked repository evidence; never backfill missing measurements from prose, memory, or chat history.
- Preserve the strict greedy token-ID equality contract used by the experiments.
- Keep PRIMARY, SECONDARY, DIAGNOSTIC, POST_HOC_DESCRIPTIVE, and MECHANISM_SUPPORTED evidence visibly distinct.
- Use complete realized target-round cost (`R_target`) for end-to-end accounting; use `V_k^micro` only as a target-forward batching/mechanism proxy.
- Keep committed progress `C` distinct from accepted draft tokens/round.
- Do not compare energy values across incompatible sensor boundaries as if they measured one common calibrated system domain.
- Do not attribute cross-platform effects to one hardware feature without an isolated control.
- Use **RTX 5070 Ti Laptop** everywhere; do not shorten the tested device to desktop-like “RTX 5070 Ti”.
- Do not call the B570 serialized fallback globally exact while its full-workload result is 60/90 exact pairs.
- Do not treat isolated draft-device tok/s as realized speculative draft cost when the runtime reconstructs state.
- HumanEval generated code was not functionally executed; exactness is generated token-ID equality, not pass@k.

## Files

- `PAPER_FRAMEWORK_HANDOFF.md` — authoritative scientific ledger, claims, evidence, decisions, reviewer risks, figure/table plan, and audit history.
- `FORMAT_REQUIREMENTS.md` — MLSys 2027 submission constraints.
- `EVIDENCE_AUDIT_2026-09-18.md` — compact evidence/status audit, revalidated 2026-09-19.
- `OUTLINE.md` — post-audit paper structure; scientific ordering is stable, exact title/prose are not.
- `WRITING_STATUS.md` — section-level drafting readiness.
- `template/README.md` — instructions for importing the official style unchanged.

## Frozen scientific direction

> On the tested consumer systems, speculative decoding pays only when the execution path that survives the chosen correctness contract and the realized stateful runtime costs fit within the progress committed by a speculative round. The paper characterizes correctness-admissible execution paths and realized costs across consumer runtimes; it does not claim that heterogeneous speculative decoding, acceptance/cost accounting, numerical nondeterminism, or state reuse are themselves new ideas.

This is a bounded systems result across the tested runtimes, workloads, quantizations, models, and devices—not a universal statement about Metal, CUDA, Vulkan, NPUs, or speculative decoding.

## Next paper-production steps

1. Draft manuscript sections from `PAPER_FRAMEWORK_HANDOFF.md` and `OUTLINE.md`; do not reconstruct scientific claims from older reports alone.
2. Build main-paper figures under the handoff's comparability constraints: realized-cost schematic, M4 workload contrast, verification-path admissibility, and 358H isolated-vs-realized/state decomposition.
3. Keep energy as boundary-separated secondary/appendix evidence; never make a cross-platform absolute J/token leaderboard.
4. Run a final source/citation/anonymization/reviewer audit on the exact submission candidate.
5. If a runtime/software co-design study is pursued, create a separate branch and preregistration; do not extend the closed hardware campaigns post hoc.

Do not start a new hardware experiment, post-hoc parameter sweep, preregistration rewrite, or public release merely to make the paper story cleaner.
