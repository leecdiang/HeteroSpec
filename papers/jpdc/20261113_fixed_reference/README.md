# JPDC author-review manuscript — revision 2

## Parallelizing Quantized LLM Inference Under a Fixed Numerical Reference

This revision develops the fixed-reference construction around one consistent query example, explicit planner/backend/consumer obligations, and opportunity–cost explanations of the existing experiments. It preserves the existing repository and historical evidence. It is **not a submitted or author-approved final manuscript**.

### Start here

- [Manuscript PDF](paper/main.pdf): compiled double-column manuscript.
- [Supplement PDF](paper/supplement.pdf): implementation coverage, complete controls, counterexamples and fixed source index.
- [Editable highlights](paper/highlights.txt) and [preview PDF](paper/highlights.pdf).
- [Chinese author notes PDF](author_notes/AUTHOR_NOTES.zh.pdf) and [editable notes](author_notes/AUTHOR_NOTES.zh.md), starting with a one-page decision summary.
- [Declarations to confirm](author_notes/DECLARATIONS_TO_CONFIRM.md): final author information and declaration decisions.
- [Build instructions](BUILD.md): CPU reconstruction, LaTeX build, flat submission-source preparation and limitations.
- [Figure source manifest](paper/generated/figure_manifest.json): each figure's source URL, commit, SHA-256, estimator and output identity.
- [Revision-2 response](reviews/v2/REVISION_RESPONSE.md): independent reviews and the concrete fixes applied.
- [Flat editable LaTeX source archive](submission/jpdc_submission_sources.zip): all source dependencies at one level, compiled separately for verification.

### Scientific scope

The strongest execution increment is the A5000 Qwen3-32B target-only C/B comparison: a **1.51%** time reduction, with a **95% stratified paired-root interval of 1.23–1.79%**. B is a shared-quantization **backend scalar-loop** control, not the Q8 backend-loop4 control. Complete speculative-application gains, local-cut increments and different-contract modern operator measurements are reported separately.

The manuscript retains natural-request negative results, inside-boundary and historical geometry counterexamples, the live-width slowdown, initialization reversals, and the faster modern extracted operator. A complete modern default backend has **not** been qualified or timed in this evidence set.

### Version relationships

- Review baseline (#243): `1382b2295aa9525a99ddb8f24026390ea11e95c4`; its head was unchanged when revision began.
- Base `main`: `ad16a13d2510363bb6f7c7b99241fe9ef1b54bb0`.
- Prior paper source (#222): `e8a4981ef7db8f05cff7144fd4edc6e5a4109343`.
- Evidence closeout (#241): `10fc03ed59e260a290a8ca8d6670d30d50f08118`.
- Authoring guide and official CAS template (#242): `b0c2391426f60185a4a70b7fd286b39220ca4cc0`.

Neither #222 nor #242 is merged by this work. Scientific results are linked to their own fixed commits. The project repository URL remains a source identifier; its old name is not the paper title.

### Review status

The package contains editable LaTeX, vector PDF/SVG figures, public numeric inputs, reconstruction and plotting scripts, compiled documents and review records. Preparation used CPU analysis and document builds, with **zero new model calls and zero GPU experiments**. Original data bytes and scientific baselines were not changed.

Before submission, the author must confirm the scientific content, complete affiliation/address, CRediT roles, funding, competing interests, acknowledgments, AI tool history, licenses and final data-access/deposit terms. Some original native records are restricted, and some temporary intermediates were pruned; no blanket availability promise is made. The 47 baseline data files remain byte-identical; five additional public fixed-version records support the new explanations. Historical V1 reviews and validation files are retained for context, while `reviews/v2/` and `validation/v2/` identify the revision-2 checks. The current full live JPDC guide returned HTTP 403, so journal-specific constraints follow the supplied official-guide excerpts, supplemented by independently accessible Elsevier policies.

The preferred publication route is subscription/non-OA. No merger, release, arXiv update, journal upload, formal submission or paid publishing choice is performed.
