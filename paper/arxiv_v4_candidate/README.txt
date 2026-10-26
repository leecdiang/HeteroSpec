Phase-Scoped Query Layouts for Reference-Preserving Speculative Decoding
Author: Chengzhan Li
Source revision: 2026-10-26 (native results integrated; not submitted)

This revision starts from the v4 source used in the accompanying review.
It reorganizes the article around repair scope, draft profitability and QB's
incremental implementation cost, then tests state/backend transfer and complete
service cost. Original measurements and registered primary intervals are retained.
This editorial update incorporates completed platform executions; it launches no new native model request.

Build the complete article and supplement:
    python3.11 -B scripts/build.py
The standard TeX installation needs pdfLaTeX, BibTeX, elsarticle, TikZ/PGFPlots,
flushend, and the packages listed in preamble.tex. The bibliography style and
matching main.bbl are included. Use --cached-bbl to skip BibTeX when necessary.

Check reported data and the secondary analysis (Python 3.11+, standard library):
    python3.11 -B anc/check.py
    cd anc
    python3.11 -B -m unittest test_release test_closure test_refinement test_round3 test_major_revision test_native_followup -v

Regenerate derived tables/figures from the source root:
    python3.11 -B scripts/generate_followup_figures.py
    python3.11 -B scripts/generate_repair_interaction.py
    python3.11 -B scripts/generate_e2_sensitivity.py
    python3.11 -B scripts/generate_e2_absolute_cost.py
    python3.11 -B scripts/generate_native_followup.py

The registered six-session percentile bootstrap remains the primary E2 analysis.
The t5 and omit-one-session results are secondary sensitivity analyses. Llama's
speculative direction remains positive, but its t5 interval crosses the practical
ratio threshold 1.02. Source data and primary results have not been replaced.

CPU runtime interface checks and archived source/patch provenance are under
anc/runtime_reproduction/. Follow its README for the exact scope and external
dependencies. The companion branches now supply native build/replay results; this paper
package itself is not a complete GPU runtime/raw-tensor capsule.

TeX tables and figures live outside anc/, so article compilation can use only
the TeX sources and included bibliography. The ancillary directory contains
reported measurements, reconstruction scripts and scientific history. It includes
failures and incomplete comparisons that constrain the article's conclusions.

The historical k3 resident HTTP-request experiments and later k1 fresh-context
service panels retain their distinct references, policies and timers. RTX's
41.8% service-time reduction is the frozen speculative policy's value;
dual-PQ/R already equals 0.588633. The two historical k1 panels do not establish a practical QB/PQ increment.
The new matched bridge establishes k3 layout benefits under resident and fresh
contexts. The separate new-input study retains the Llama reference counterexample.
B570 prefill timing is complete and negative under its practical screen.
Exact compact records and reconstruction are in anc/followup_20261026/.

No arXiv update, journal submission or merge is performed by this source package.
