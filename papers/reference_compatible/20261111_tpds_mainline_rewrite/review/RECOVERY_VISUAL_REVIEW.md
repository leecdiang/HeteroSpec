# Independent recovery visual review

## Result

**PASS for author-review delivery.** No blocking visual or layout defect was found in the recovered 10-page main manuscript, 5-page supplement or nine embedded figures. No manuscript, figure source, numeric input or original PDF was edited during this review.

## Scope and method

The reviewer read the recovered scientific-visualization skill (version 1.4), its publication-figure principles, and the PDF skill. Both complete PDFs were rendered independently with PyMuPDF at 100.8 dpi. The reviewer first inspected three page overviews and then inspected every one of the 15 individual page images. This review did not rely only on extracted text or the earlier validation report.

The four figures most dependent on multiple graphical encodings (execution construction, component effects, full resident service and width/work tradeoff) also received an independent grayscale rendering and visual inspection. Grayscale inspection and redundant encodings support accessibility; they are not a certification for every color-vision condition or printing process.

## Actual visual findings

- **Main pages 1–3:** The title and abstract are complete and aligned. The long title occupies two clean lines. Figure 1 on page 2 fits the full width; query positions, physical extents, hatching, crop/zero-pad direction and the two different divergence indices are readable and separated. Equations and subsection headings are intact on page 3.
- **Main pages 4–5:** Figure 2 separates physical-extent groups from arithmetic groups and the resident-state owner. Its arrows, box text, array shapes and legend text are not clipped or crossed by unrelated objects. The execution table and paired-estimate equation are legible. The method text continues normally across the figure-bearing pages.
- **Main pages 6–7:** The evaluation table uses the available width without overflowing either margin. Figures 3 and 4 retain visible points, intervals, axis units, equality lines and descriptive labels. The figure captions remain with their figures; no caption or marker lies outside its panel. The natural-boundary count is explicit even though its proportional bar segment is necessarily small.
- **Main pages 8–9:** Figure 5 is readable at manuscript width and explicitly identifies the fixed target-only controls, root distributions, intervals, fastest-control boldface and percentage reductions. Figure 6 separates equal-work execution from complete requests and work counts. The same-output token count, baseline circles, directional changes and counts are visible. Both figures precede the conclusion and references.
- **Main page 10:** The conclusion remains together, followed by acknowledgments and complete references. Both reference columns are intact, without overlap, clipped links or missing glyphs. The final page has normal unused space below the references; no additional compression is needed for delivery.
- **Supplement pages 1–5:** All eleven tables and three figures are present. Dense numeric tables on pages 2–5 remain readable. Signed host-cost bars have an explicit zero and numeric deltas. The historical geometry figure labels the unmeasured cell rather than treating it as zero. The supplementary bibliography is complete and does not collide with the last table or figure.
- **Visual continuity:** Blue, ochre and green, serif plot labels, subdued raw observations and the shared ratio/interval format are consistent. Hatching, panel position, direct labels, marker shapes, open versus filled marks and numeric direction provide information beyond color. In grayscale, the logical groups, fixed controls and positive/negative directions remain recoverable.

## Independent file checks

The main document has 40 font resources; the supplement has 17. All extracted font resources are embedded. Both documents have zero embedded raster images. Each of the nine standalone figure PDFs is a one-page vector file with embedded fonts and zero embedded raster images. These checks concern the inspected PDF files and do not certify journal policy compliance or experimental correctness.

| Inspected document | Pages | SHA-256 |
|---|---:|---|
| `source/main.pdf` | 10 | `b90a2bec4236763f5be21d0973abf0a27aa6c4805f55a7dd0c0579f954c501ce` |
| `source/supplement.pdf` | 5 | `4cb7353acb1b890e0ad1f6d29cc81520de84d8af285c45b0593aab9c24e25583` |

The independent inspection images and machine-readable per-PDF checks are retained in the recovery workspace under `qa/recovery_visual/`. They are internal QA derivatives, not replacement publication assets.

## Remaining issues

No layout change is required to complete this recovery. Small gray observations are intentionally subordinate to the estimates, but all remain visible in the inspected manuscript and grayscale figures. This report covers presentation; scientific interpretation, arithmetic provenance and the remote PR save are handled by the separate content review and release checks.

## Targeted recheck after abbreviation expansion

After the independent content review, the lead writer expanded KV, Q/K/V, QK, AV and RoPE at their first occurrences in three source files. The exact edits are recorded in `RECOVERY_CLARITY_EDITS.diff`.

The revised main manuscript remains **10 pages**. Pages **1 and 2** changed visually and were inspected again at 100.8 dpi. The expanded abstract and introduction remain clean; the Figure 1 caption fits, and the longer mechanism paragraph causes no clipping, overlapping text, stranded heading or page overflow. Pages **3 and 4** were also inspected, including Figure 2; their layout is unchanged.

An exact pixel comparison at the same rendering settings confirms that main pages **3–10 are identical** to the previously reviewed version. The entire **5-page supplement remains byte-identical**, and every supplementary page is also pixel-identical. The initial full review therefore carries forward for the unaffected pages and all nine figures. No further layout correction is required.

The document hash table above now identifies the revised final main PDF and unchanged supplement. The earlier main-PDF checkpoint was `7f27db2b76d743102a80e0f8810bdc423da047dcc9ce3eae46da050067ff2ec5`. Comparison details are in `qa/recovery_visual/clarity_edit_check.json`.
