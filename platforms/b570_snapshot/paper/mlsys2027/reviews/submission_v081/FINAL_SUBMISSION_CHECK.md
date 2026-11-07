# Focused internal review: final submission check — v0.8.1

Inspected actual final main PDF, separate appendix and hardware-only internal proof, their rendered pages, bibliography, build logs and clean ZIP reconstruction. Internal review only; no conference probability estimates.

| Gate | Result |
|---|---|
| Main pagination | PASS: 10 body + 2 references = 12 pages; body boundary read from final TeX auxiliary labels |
| Appendix | PASS: separate 6-page PDF; scientific content unchanged, version labels updated |
| Hardware proof | PASS: 9 body + 2 references = 11 pages; runtime section excluded, no unresolved references; internal proof only |
| Source package | PASS: 39 ZIP members, 38 manifest-covered payloads; clean extraction independently compiles main.tex and appendix.tex with plain latexmk -pdf; page counts and all extracted text match fresh build |
| Typography | PASS: every PDF font embedded; zero font substitution warnings, unresolved citations/references or overfull boxes |
| Bibliography | PASS: 19 unique entries; all author fields complete, rendered lists untruncated, including 58 HumanEval authors and all four new paper author lists |
| Anonymity | PASS: Anonymous Authors PDF metadata; no real author identities/affiliations, personal paths or repository/user URLs; cited literature author names and the third-party ACL HeteroSpec title are legitimate references |
| Figures | PASS: every figure byte preserved; Figure 3 stays Figure 3 before runtime discussion and has no new factual inconsistency or readability blocker |
| Title | Unchanged as instructed; current broad framing still has overlap risk. Recommend title alternative 1 from TITLE_REVIEW_V081.md; author choice pending |
| Abstract | Retains scoped direct-ID, B570 72/72, realized 358H, exact M4 results and negative Guard secondary contrast; compact tested-stack scope |
| Contributions | Three concrete contributions; Guard retained as evidence, removed as headline novelty |
| Scientific scope | PASS: protected result/evidence/figure/style paths and canonical Limitations preserved; no inference/timing/energy/sweeps |
| Official policy | Checked live CFP on 2026-09-29: 10-page body, all reference authors, separate appendix at same deadline, double blind |

Visual review covered every page in main, appendix and internal proof, with enlarged inspection of opening/claims, literature/limitations/conclusion, new reference entries and appendix mechanism chronology. No clipping or overlap found. The appendix retains its original sparse float pages; no layout or figure redesign was introduced. PDFs differ in metadata/build timestamps across separate builds; the required content/page/hash-manifest comparisons pass. Full experimental archives were not re-executed: scientific preservation is verified against the exact baseline, not represented as a new experimental replication.

Ready for author-review submission-candidate status. Remaining author actions: choose title, review exact manuscript/appendix and complete active OpenReview profiles/conflicts and final eligibility declaration. Official deadline is 2026-10-30 20:00 UTC (2026-10-31 04:00 Asia/Shanghai); appendix deadline is the same. No submission or merge performed.

Machine receipts: NARRATIVE_PDF_V081_QA.json, CLEAN_ZIP_QA_V081.json, PRESERVATION_QA_V081.json in the evidence directory. Prior scientific QA receipts remain untouched; this review does not claim fresh archive replay.
