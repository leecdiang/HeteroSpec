# MLSys 2027 Submission Upload Checklist

Use this checklist at the actual submission; unchecked items require a final check even where the current QA receipt already passes. Official Research Track CFP: https://mlsys.org/Conferences/2027/CallForResearchPapers (checked 2026-09-29).

**Official deadline:** October 30, 2026, 20:00 UTC; **October 31, 2026, 04:00 Shanghai time**. The separately uploaded appendix is due at the same time. The research track is double blind. Current candidate: 10 body pages + 2 reference pages; separate appendix: 6 pages. All author-controlled identity/conflict checks below require human action.

## A. Frozen scientific baseline

Scientific author-freeze tag: `mlsys2027-v0.8-author-freeze` → `1d3b556c93b477680788dfd1eb0737dfe9eee28c`.

- [ ] Author-freeze tag exists.
- [ ] Tag resolves to the expected scientific baseline above.
- [ ] Closed evidence is unchanged.
- [ ] No new unreviewed experiments are included.

The submission-candidate tag has **not been created**. Create it only after PR #37 is author-approved and merged, and final QA passes on the merged commit. Query current repository main at session start; do not assume the scientific baseline equals current main.

## B. Main paper

Final title: **Execution-Path Qualification and Realized Costs in Speculative Decoding on Consumer Systems**.

- [ ] Final title is identical across source, PDF and OpenReview.
- [ ] Main body is at most 10 pages.
- [ ] References are excluded from the body count.
- [ ] No appendix is embedded in the main PDF.
- [ ] All figures are readable at submission scale, including Figure 3.
- [ ] No unresolved references/citations.
- [ ] Zero overfull boxes.
- [ ] All fonts are embedded, with zero substitutions.
- [ ] Author block is anonymous.
- [ ] PDF metadata is anonymous.
- [ ] No repository, username or local-path leakage.

## C. Appendix

- [ ] Appendix is uploaded as a separate PDF.
- [ ] Appendix is anonymous.
- [ ] References/citations resolve.
- [ ] No private paths or identities.
- [ ] Claims match the main paper.
- [ ] Appendix does not silently introduce new headline claims.

## D. Bibliography

- [ ] All cited works are present.
- [ ] All reference authors are explicitly listed.
- [ ] Lossless but Not Free is checked.
- [ ] Compiler-Assisted Speculative Sampling is checked.
- [ ] Lever is checked.
- [ ] ACL 2026 HeteroSpec is checked.
- [ ] No accidental duplicate citation keys.
- [ ] Proceedings version is preferred when available; preprints and acceptance notes remain honest.

## E. OpenReview account / conflicts

**作者人工操作 / Human author actions.** Do not infer conflicts from repository content. All authors need active complete OpenReview profiles; the CFP asks that profiles be created at least two weeks before submission. Confirm private author records while keeping the review PDF's author block and metadata anonymous.

- [ ] Every author has a complete active OpenReview profile.
- [ ] Institutional affiliation is current.
- [ ] Email is verified.
- [ ] Conflict domains are reviewed.
- [ ] Coauthor relationships are reviewed.
- [ ] Advisor / advisee conflicts are reviewed.
- [ ] Recent collaborator conflicts are reviewed.
- [ ] Submission author list matches the private manuscript author metadata; anonymous PDF metadata remains anonymous.
- [ ] Author order is confirmed.

## F. Source bundle

- [ ] Final source ZIP is generated.
- [ ] ZIP is extracted into a clean directory.
- [ ] `latexmk -pdf main.tex` succeeds.
- [ ] `latexmk -pdf appendix.tex` succeeds.
- [ ] Rebuilt page counts match.
- [ ] Extracted PDF text matches the frozen deliverables.
- [ ] Manifest hashes match.
- [ ] No local absolute paths.
- [ ] No unnecessary raw experimental artifacts inside the source ZIP.

This is a **manuscript-source package**, not the full reproducibility artifact package. The internal hardware-only proof is not an upload substitute for the main manuscript.

## G. Final content audit

- [ ] Title reflects execution-path qualification rather than generic consumer characterization.
- [ ] Abstract foregrounds 72/72 held-out prediction.
- [ ] Introduction has three focused contributions.
- [ ] M4 Guard is not presented as an incremental improvement.
- [ ] Historical comparator boundaries are preserved.
- [ ] B570 mechanism does not claim an RTX explanation.
- [ ] Sufficient-path wording is retained.
- [ ] No performance inference from the v0.8 mechanism study.
- [ ] No cross-platform energy ranking.

## H. Final submission candidate freeze

**After PR #37 merge and final build/QA**, complete these items; do not create this tag during the current finalization task.

- [ ] Record the final submission commit SHA.
- [ ] Create annotated tag: `mlsys2027-v0.8.1-submission-candidate-1`.
- [ ] Verify the peeled commit SHA.
- [ ] Record the main PDF SHA-256.
- [ ] Record the appendix SHA-256.
- [ ] Record the source ZIP SHA-256.

Freeze record to fill after final QA:

| Item | Final value |
|---|---|
| Submission commit SHA | Pending author-approved merge |
| Candidate tag peeled SHA | Pending tag creation |
| Main PDF SHA-256 | Pending final merged-commit build |
| Appendix SHA-256 | Pending final merged-commit build |
| Source ZIP SHA-256 | Pending final merged-commit build |

## I. Upload

- [ ] Upload the main PDF.
- [ ] Upload the separate appendix.
- [ ] Enter the exact final title.
- [ ] Paste the abstract from the frozen manuscript.
- [ ] Confirm author list/order.
- [ ] Confirm conflicts.
- [ ] Preview the rendered submission.
- [ ] Download uploaded PDFs and compare hashes; if OpenReview rewrites metadata, also compare extracted text.
- [ ] Obtain final author approval before the deadline.

Deadline: **October 30, 2026, 20:00 UTC / October 31, 2026, 04:00 Shanghai time**. Recheck the official CFP and OpenReview instructions immediately before upload.
