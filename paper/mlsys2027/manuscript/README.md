# Current manuscript — v0.8.6 on main

Main contains the unchanged v0.8.6 delivery through PR #46, manuscript integration anchor `361cb43a67f7fd9bfae95de4cdf7e816c46bbe90`. The exact delivery/content tree remains `494a5ca4fe62534b032b37d01652c3f88e0d16e1` and authoritative TeX source remains `da8d5739eb108de7f35d3a3cfbd954d42462f2e0`. Documentation commits may follow the anchor; resolve the actual remote HEAD before work.

Read [the canonical handover](../HANDOVER_CURRENT.md) for current scope and next-step authorization. Versioned manifests/reviews retain their original stacked-PR delivery context. This repository reconciliation adds no hardware/model execution and changes no TeX, numbers, Figure 3, official style, delivered PDF or ZIP.

The central story remains the original B570 draft-free prospective full-trajectory prediction. Distinct fork, RTX P/R and qualified-cost studies supply different supporting evidence. The execution/build descriptions below report the original v0.8.6 delivery; this maintenance separately checks artifact identity, a fresh source-ZIP main/appendix build and compact evidence verification.

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

## Current author workflow and historical delivery records

Use [HANDOVER_CURRENT.md](../HANDOVER_CURRENT.md) for live repository state and RTX A+B preparation. See evidence/DELIVERY_V086.md and reviews/convergence_v086/ for the original revision response and delivery QA. Their Draft/unmerged and no-review language describes that delivery-time snapshot, not the later merge of #44/#45/#46 or a live authorization gate.

This maintenance does not perform a new submission-level review or claim that acceptance follows from build success. Independent review and any integration of future RTX results remain separate tasks. RTX protocol preparation is authorized; reserved execution waits for review of the exact protocol/source SHA.
