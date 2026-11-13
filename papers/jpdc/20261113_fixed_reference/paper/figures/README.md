# Scientific figure sources and regeneration

The figures implement one visual argument: a physical range can change an
attention result; the reference still admits independent arithmetic groups and
local cuts; the measured value depends on the control, the boundary geometry,
and the amount of live work. All figures are generated from editable code.

## Build

From the `paper` directory:

```sh
python scripts/build_figures.py
```

The script is CPU-only. It verifies 47 source-file SHA-256 identities, recomputes
the displayed point estimates and root observations, and checks them against the
published results. It preserves the original confidence intervals; it does not
create a new GPU experiment or a new population interval. It writes PDF, SVG and
PNG for all eleven figures, an exact numeric ledger, and two editable LaTeX
tables. The SVGs preserve editable text. PDFs contain vector paths and embedded
fonts; PNGs are previews, not the manuscript's figure inputs.

The tested toolchain uses Python 3, NumPy 2.3.5, pandas 2.2.3, Matplotlib 3.10.8,
Inkscape 1.4 and the P052 font family. P052 is compatible with the manuscript's
Palatino typography. SVG-to-PDF export through Inkscape avoids a CFF font
embedding mismatch in direct Matplotlib PDF output. Without P052 or Inkscape,
the script uses DejaVu Serif and direct Matplotlib vector PDF export.

## Main figures

| File stem | Inches | Scientific question and observations | Statistical and timing boundary |
|---|---:|---|---|
| `fig01_overview` | 7 × 3.45 | Actual 765–768 position example, separate physical and arithmetic groups, local attention cuts, downstream vectors and state. Eight-column grouping is a schematic. | A conceptual method figure, not a performance chart or graphical abstract. The numerical example is from the pinned native diagnostic. |
| `fig02_extent` | 7 × 2.15 | Bidirectional 768/1024 extent exchange: scalar/wide capture × replay extent, four outcomes. | Exact native AV-output comparisons for one captured case with one query in both AV operators. Not full-model state or service timing. |
| `fig03_strong_baseline` | 7 × 3.38 | Twelve root means and all 48 paired rounds; C/B versus B/G and C/G. B is the backend shared-quantization **scalar loop**, not loop4. | Equal-root geometric ratio; 95% C/B interval, 97.5% secondary intervals; reset-inclusive resident service. No draft. |
| `fig04_factorial` | 7 × 3.35 | Eight direct component contrasts and two interactions; 160 displayed root ratios. Both uncertain LOCAL-with-packing effects remain hollow. | Direct estimates: ratio of totals. Interaction: equal-root geometric ratio of ratios. Original 99% root intervals. Qwen sizes share 16 roots. |
| `fig05_application` | 7 × 2.80 | (a) Same-D4 method combination and (b) full application versus fastest fixed M; 88 root observations. | Ratios of total resident service with original 99% intervals. Separate scales and comparators. Full application includes drafting. |
| `fig06_geometry` | 7 × 2.95 | All twelve controlled B570 cells with all 36 paired observations; separate A5000 natural-opportunity count. | Ratio of summed append times; min–max of three pairs is a descriptive range, not a CI. No pooling of B570 timings and A5000 counts. |

## Supplementary figures

| File stem | Inches | Why retain it |
|---|---:|---|
| `supp01_width_tradeoff` | 7 × 3.80 | Equal-work q8/q4-pair advantages coexist with slower live k7/k3 service. Four origin aggregates per operation cell are separate from sixteen live roots. Original 98.75% live intervals, exact work counts. |
| `supp02_width_cost` | 7 × 2.85 | All ten signed LOCAL-packed host-phase differences, including negative draft-sync, and their exact sum to complete service. Residual is not assigned to an invented mechanism. |
| `supp03_historical_geometry` | 7 × 2.45 | All fourteen measured historical geometry cells, fourteen inside controls, and one explicitly unmeasured cell. The q32 reversals remain visible. |
| `supp04_prior32b_lifecycle` | 7 × 3.45 | All six earlier 32B service arms and 24 root means, alongside Llama's resident-versus-worker ranking reversal for every fixed M comparator. No new uncertainty interval is invented. |
| `supp05_rtx_contracts` | 7 × 2.65 | C and C1 lose within the old contract; U wins in a different contract. All 60 paired operator observations remain separate by experiment and boundary. The complete default modern backend is not plotted because it was not timed. |

`generated/figure_application_controls.tex` contains all fifteen fixed
application contrasts (five per model) as a `booktabs` tabular. Its numerator is
always `L_P_D4`. `generated/figure_natural_table.tex` contains all four natural
multi-turn pairs and the pooled descriptive total. Neither table includes its
own floating environment or caption, so an author can place it in either draft.

## Immutable provenance

Every figure entry in `generated/figure_manifest.json` includes the full source
commit, direct GitHub URL, local file, source SHA-256, generation script, output
hashes, actual page size, and observation counts. The complete source-file
inventory is `generated/figure_source_downloads.json`.

Primary pinned sources include:

- [Paper-source data snapshot at e8a4981ef7db8f05cff7144fd4edc6e5a4109343](https://github.com/leecdiang/HeteroSpec/tree/e8a4981ef7db8f05cff7144fd4edc6e5a4109343/papers/reference_compatible/20261111_tpds_mainline_rewrite).
- [Public timing rows at 10fc03ed59e260a290a8ca8d6670d30d50f08118](https://github.com/leecdiang/HeteroSpec/tree/10fc03ed59e260a290a8ca8d6670d30d50f08118/benchmarks/jpdc_closeout_20261113/statistics).
- [S3 per-root values at ab695a766d055f7d3c6b1fed0720c579c749bcdb](https://github.com/leecdiang/HeteroSpec/blob/ab695a766d055f7d3c6b1fed0720c579c749bcdb/benchmarks/server_expansion_v1/strong_baseline_followup_20261110/RESULTS_S3_20261112/PER_ROOT.csv).
- [Native AV intervention at 701079f265c0ff8fd05d43fbc2d8d5054a711e1b](https://github.com/leecdiang/HeteroSpec/blob/701079f265c0ff8fd05d43fbc2d8d5054a711e1b/platforms/rtx_reference_snapshot/benchmarks/rtx_llama_repair_v1/host_execution/RESULTS.md).
- [RTX C timing rows at ba019f30522352c87cac2cc527082ecc6c73ed97](https://github.com/leecdiang/HeteroSpec/blob/ba019f30522352c87cac2cc527082ecc6c73ed97/benchmarks/rtx223_e08_q8_20261113/numeric-v1/TIMING_SAMPLES.csv).
- [RTX C1 timing rows at 304dcbff6d17461237774464c67ce8cb0ed60189](https://github.com/leecdiang/HeteroSpec/blob/304dcbff6d17461237774464c67ce8cb0ed60189/benchmarks/rtx223_e09_c1_20261113/ALL_SAMPLES.csv).
- [RTX U timing rows and analysis at c8e5ea070ac393d7513903e0ec261dfce4554a49](https://github.com/leecdiang/HeteroSpec/tree/c8e5ea070ac393d7513903e0ec261dfce4554a49/benchmarks/rtx223_e11_u_contract_20261113).

The U CSV's convenience `per_operator_ms` values have a small float-rounding
difference from its published analysis. The plot uses the same CSV's original
`event_ms / batch_repetitions`, which reproduces the published geometric ratios
to floating-point precision. No source value is changed.

## Visual conventions and checks

Blue and ochre share a consistent meaning within each explicitly labeled panel;
color is redundant with hatching, marker shape, marker fill, position or text.
Primary colored text exceeds a 5:1 contrast ratio against white. Main-figure text
is at least 8.2 pt at the supplied 7-inch size; supplementary text is at least
8.6 pt. These minima retain at least 8 pt after placement at the manuscript's
6.84-inch width and the supplement's 6.54-inch width. The reference ratio is a dashed line at one. Faint dots
are observed roots or paired blocks, never synthetic distributions.

The builder checks text against the physical page and refuses to hide an
observation beyond a displayed axis range. The final rendered PDFs were also
inspected in color and grayscale. `generated/figure_layout_check.json`,
`generated/figure_numeric_checks.json`, and `generated/figure_pdf_check.json`
record those checks. The initial layout pass found footer/axis-label collisions;
the delivered version increases bottom margins and removes those collisions.

Review checklists were informed by the `scientific-visualization` and
`statistical-analysis` skills from
[Scientific Agent Skills at 2d2065fb4520fa3f3f2bcf61cff26ec8b7eba4b5](https://github.com/K-Dense-AI/scientific-agent-skills/tree/2d2065fb4520fa3f3f2bcf61cff26ec8b7eba4b5).
They supplied workflow guidance, not data or measurements. The diagram and plot
code were prepared with ChatGPT/Codex assistance. The author-facing submission
declaration must accurately disclose and verify this use.
