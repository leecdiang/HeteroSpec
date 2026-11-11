# Figure-only integration handoff

Base checkpoint: `1a11361f8526ec361e20dd6878d6e67352fb7bbd`.

The selected sequence has four main figures and optional appendix A1. No manuscript file is edited by this branch. `selected_figures.tex` contains ready-to-use includes and caption text with the checked 6.75/3.25-in widths; paths are relative to `paper/mlsys2027/manuscript/`. It is a placement kit, not a file to input wholesale into the unchanged manuscript.

| Asset | Intended placement | Label | Current wrapper |
|---|---|---|---|
| `../figures/pdf/figure1.pdf` | Opening observation, double column | `fig:overview` (new) | Do not substitute silently for `fig:framework` |
| `../figures/pdf/figure2.pdf` | Correctness diagnosis, double column | `fig:verification` | `figures/03_verification.tex` |
| `../figures/pdf/figure3.pdf` | M4 contrast, single column | `fig:m4` | `figures/02_m4.tex` |
| `../figures/pdf/figure4.pdf` | 358H integration diagnosis, double column | `fig:state` | `figures/04_358h.tex` |
| `../figures/pdf/figure5.pdf` | Appendix only, double column | `fig:regimes` | `figures/05_regimes.tex` currently in main |

Two references need manuscript-owner reconciliation during the authorized narrative rewrite:

- `sections/02_framework.tex` describes Figure `fig:framework` as an accounting schematic. The new overview is a different concept. Retain the section's accounting equations and choose whether the original schematic is still needed as a subsection/appendix aid; it is not selected as an additional main figure.
- `sections/05_hardware_results.tex`, subsection “Stable hardware-study conclusion,” currently inputs and discusses the main regime map. Move that inventory to the appendix and adjust its reference and synthesis prose with the narrative rewrite. This figure branch leaves those sentences intact.

The old manuscript title, abstract and framework-first framing remain unchanged in this branch. The user-supplied new story controls the candidate captions, even though older handoff/status documents retain their earlier framing. No experiment, scientific result or runtime implementation changes are required.

`qa/insertion_proof.pdf` is a native-size artwork proof, not a rebuilt manuscript. `comparison/OLD_NEW_COMPARISON.pdf` contains equal-width comparisons; `comparison/OLD_NATIVE_WIDTH.pdf` preserves original sizes. Pagination, float placement, final reference numbering and full manuscript compilation belong to the prose integration pass.
