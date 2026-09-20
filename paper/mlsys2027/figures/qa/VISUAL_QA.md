# Final-size visual QA

**Figure status: PUBLICATION-CANDIDATE.** Checked on 2026-09-20. All five standalone vector candidates pass within this scope; manuscript integration and actual OLD/NEW comparison remain pending.

## Width and typography

The official MLSys style defines 6.75-in text width and 0.25-in column separation. Figures 1/3 are 3.25 in; Figures 2/4/5 are 6.75 in. PDFs retain exact widths without tight-crop resizing. Text uses STIXGeneral and STIX math, compatible with the style's Times typography, at 8–13 pt. PDFs embed TrueType fonts. SVG text is converted to paths for portable rendering.

## Inspections performed

| Figure | Width × height (in) | Color | Grayscale at final width | Stronger-conclusion check | Result |
|---|---|---|---|---|---|
| 1 | 3.25 × 4.05 | Render inspected | Native-width proof inspected | Detached proxy; full C and R_target; not claimed as novel theory | PASS |
| 2 | 6.75 × 3.58 | Render inspected | Native-width proof inspected | Open/filled and status text prevent promoting cheap blocked paths; contexts explicit | PASS |
| 3 | 3.25 × 2.90 | Render inspected | Final 96-dpi grayscale image inspected | Separate studies, 1× reference, CIs and exactness retained; no paired-workload inference | PASS |
| 4 | 6.75 × 3.75 | Render inspected | Native-width proof inspected | Absolute totals; hatch/text redundancy; distinct mean/GM estimands; no replay-only claim | PASS |
| 5 | 6.75 × 4.10 | Render inspected | Native-width proof inspected | Categorical columns; blocked profitability omitted; no continuous score or leaderboard | PASS |

Each final PDF was rendered by Poppler at 96 and 180 dpi. Grayscale inspection used the native-width proof sheets and the final Figure 3 render after its last label/ref-line refinement. Large renders were also checked for marker, glyph and line defects. PNGs are previews only.

Observed issues and repairs:

- Figure 2 axis label was too close to its legend note: plot moved upward; distinct footer lines restored.
- Figure 3 axis label/footnote collision: canvas and lower margin increased; title/interval text masked against the 1× reference and reference height bounded.
- Initial Nimbus Roman OTF embedding produced Poppler font-type warnings: replaced with STIXGeneral TrueType and regenerated all assets. Final renders have no such warnings.

The small Figure 4 residual segments keep their true widths and are stated numerically; they are not enlarged into misleading visible proportions. Overlapping nearby Figure 2 context markers are accompanied by exact min/max labels and the full cell table. These are design choices, not missing data.

## Checks not claimed

- No inspection of the unavailable manuscript, its current captions or its original figures.
- No final submission-page fit or author review.
- No printer-dependent physical hardcopy test; the proof PDF preserves physical dimensions for a 100% print check.
- No browser visual inspection of the companion notebook HTML: browser executable unavailable. The notebook is schema-validated and its plain Python cells executed sequentially; embedded figure outputs were visually inspected through the final-figure workflow. Jupyter TCP/IPC kernel startup was unavailable in this environment.

Numerical logs are separate: `figure1_validation.json` through `figure5_validation.json`. A visual pass does not substitute for numerical validation.
