# Current author draft — v0.8.6 convergence

This draft starts from exact v085 content/delivery HEAD
`dccbbb53e1f91d3239e2075336100795dd6daa1e`, on
`paper/mlsys2027-convergence-v0.8.6`. It is stacked on the unmerged v085
branch, not on a main containing v086. No hardware/model execution is added.
The title and three contributions remain; the central story is the original
B570 draft-free prospective full-trajectory prediction. Distinct fork,
RTX P/R and qualified-cost studies supply different supporting evidence.

## Current build and QA

Prerequisites: Python 3.11+ with pypdf, numpy and pymupdf; pdfLaTeX, BibTeX
and latexmk. Poppler renders the final pages. Activate those dependencies
before invoking Makefile; no runtime or model installation is needed.
These current entries have actually been run from this directory:

```sh
make all
make check
make overleaf
```

The defaults use v086 entries only. All old scripts, macros, Figure3,
archives, vendor styles and earlier PDFs/ZIPs/QA receipts are preserved.
Each build packages actual TeX dependencies and checks canonical-to-ZIP
byte transformations. It independently extracts into two new directories,
builds main/appendix and the internal hardware-only proof in each, and
compares every page's raw extracted text without normalization. Fresh aux
and bibliography files are generated locally; nothing is copied from an
old build. Automated PDF/log/font/reference/anonymous checks run afterward.
Manual review has its own final PDF/render hash receipt.

Outputs are manuscript-v0.8.6.pdf, appendix-v0.8.6.pdf,
hardware-only-v0.8.6.pdf, overleaf-convergence-v0.8.6.zip and
anonymous-evidence-index-v0.8.6.zip. Main has 10 body + 2 reference pages;
appendix has 12; internal proof has 9 body + 2 reference pages. The proof
removes the runtime section but keeps full-manuscript summaries; it is not
a submission paper. Appendix growth pays for raw-score/continuation tables,
M4 opportunity/sensitivity, conditional accounting, H2 input/witness audit
and evidence navigation; the CFP has no appendix page cap.

The source ZIP needs only TeX: extract into an empty directory and run
`latexmk -pdf main.tex` and `latexmk -pdf appendix.tex`. The compact index
needs only Python 3.11+ stdlib: extract into an empty directory and run
`python3 -B verify.py`. It executes unchanged prior numeric/endpoint
assertions and recomputes new post-study statistics from exported inputs.
INDEX.json identifies the separate unchanged H2 tape/events capsule by
exact filename, length and SHA256. Internal reviews and author paths are
excluded from both ZIPs.

## Actually executed full-archive and derived entries

The following commands were run from the repository root:

```sh
python3 -B paper/mlsys2027/scripts/replay_archives_v086.py --work tmp/qa-v086/archives-final
python3 -B paper/mlsys2027/scripts/analyze_existing_records_v086.py --work tmp/qa-v086/archives-final
python3 -B paper/mlsys2027/scripts/audit_h2_inputs_v086.py --work tmp/qa-v086/archives-final
python3 -B paper/mlsys2027/scripts/package_anonymous_evidence_v086.py --work tmp/qa-v086/archives-final
```

Archive replay requires a nonexistent directory; for another replay choose
a new path and pass that same path to the other three entries. The scripts
execute file/CPU verifiers only. All nine available families are reconstructed
and verified, including all 49 B570 parts, full/anonymous RTX H2, RTX H1 and
latency, old B570 H1 and both direct-ID studies, and M4 primary/secondary.
Original B570 Windows basename failures on POSIX remain explicit RERUN_FAIL
records; the Path.name-only adapter keeps every scientific assertion active.
Original verifier entry SHA, arguments, exit status and raw stdout/stderr
hashes are recorded. Other old prose-bound reviews are PRIOR_RECEIPT_ONLY
history; their fixed-word checks are not current semantic claims.

New descriptors use all original applicable records. The M4 sensitivity
has its own secondary seed2026100101/10000 stratified draws. Original
primary/secondary CIs and streams stay unchanged. 358H zero-draft results
are fixed-progress/target-work/baseline arithmetic bounds, not prompt-GM
bounds or optimization experiments. Complete native-log file counts are
observed, not a timed logging-cost estimate. Empty hook p99 0.6 microseconds
does not bound all logging. RTX independent GM .6458157742698285 and sealed
original .6458157742698286 remain distinct at one ulp.

Exact old v084 sequence ZIP and 358H runtime raw traces remain UNAVAILABLE.
Original 72 B570 arrays are preserved and compared element by element.
Offline hashes/ordinal mappings do not authenticate original absolute time,
remote exposure completeness or omitted weights/runtime/compiler/driver.

## Author review

See ../HANDOVER_CURRENT.md, ../evidence/DELIVERY_V086.md and
../reviews/convergence_v086/. R86-01 through13 map to the v085 prompt's CR
list; the separately numbered v083 reviews are historical evidence.
The three named new review attachments were unavailable; no unseen report
was cited. No fresh formal/mock scoring, inference, measurement, merge,
tag, release, submission or messages occurred. The next step is author
review of these exact artifacts, then a separately requested independent
submission-level review.
