# Author-approved figure presentation

Approved changes: Fig. 1 direct numerical labels and independent-study note;
Fig. 3 vertical offsets exposing all 11 context cells and explicit non-CI ranges;
Fig. 4 statistical-panel labels, dominant-cost percentages and separation of
arithmetic mean latency from prompt-geometric-mean speedup.

Fig. 2 remains the original `figures/mechanism_v05/mechanism.pdf`. Table 3 keeps
its compact three-row booktabs layout. Neither rejected visual revision is
included. Current submission-review comparator qualifications remain in the
captions and prose; historical text-path agreement is not direct-ID proof.

Inputs are the existing frozen CSVs in `paper/mlsys2027/figures/data/`.
No estimates, uncertainty intervals, units, sample counts or experimental
conclusions were recomputed. Historical figure trees and validation remain
intact; the new independent validator checks the selected presentation too.

Run `make figures` from the manuscript directory to regenerate and validate.
Dependencies: Python, numpy, pandas, matplotlib (reviewed with 3.10.6), pypdf.
PDF and SVG exports preserve the original physical sizes and embedded fonts.
Receipts record source hashes and actual plotted coordinates.

The rendering workflow uses the scientific-visualization guidance from
K-Dense Scientific Agent Skills (commit
49c6e97775eaa18ba791bebe23162a70ae601c18). Software-method attribution:
Kassis, Agarwal, He, Patel, and Brueckner (2026), *Scientific Agent Skills:
A Library of Procedural Knowledge for Research Agents*,
https://doi.org/10.48550/arXiv.2609.00065.

Integration base: 50050f6 (submission review v0.5), retaining its scientific
wording updates. Local review builds use Tectonic 0.17.0 with the original OT1
font encoding. The repository's standard build remains pdfLaTeX / latexmk.
