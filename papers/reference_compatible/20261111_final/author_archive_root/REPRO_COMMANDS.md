# Executed reconstruction commands and scope

## Author source rebuild (offline)

From the author package root:

```sh
cd paper
bash build.sh
```

`build.sh` actually ran the four Python derive/table/figure scripts, 59 unit tests
under ordinary Python and `python -O`, and the following for both `main` and
`journal`:

```sh
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Result: main14 pages (10main+4supplement), journal10 pages. Fresh-directory
statistics and figures regenerated, then both PDFs matched the release page text
and 100dpi page pixels. Original data files19/19 and display equations6/6 are
unchanged. Details and limits are in FINAL_SOURCE_MANIFEST.json.

## Standalone arXiv ZIP

The separate arXiv ZIP was extracted into an empty directory. The four TeX/BibTeX
commands above succeeded. There is one document root, main.tex. No Python,
GPU, shell escape or internet is required to compile this ZIP. All14 extracted
page texts and 100dpi rendered pages matched the delivered reading PDF.

## Environment repair that preceded successful builds

The container initially lacked a usable pdflatex format and its ordinary bibtex
wrapper was not executable. A user-scoped `fmtutil-user --byfmt pdflatex` generated
the format; a private PATH entry selected the installed `bibtex.original` binary.
No repository, system driver, GPU or experiment was changed. These are local TeX
environment repairs, not hidden manuscript dependencies. A normal TeX Live
installation can use ordinary pdflatex/BibTeX. The final successful logs, not the
initial failed attempt, are included.

Observed tooling: Python3.13.5, NumPy2.3.5, Matplotlib3.10.8, PyMuPDF1.26.7,
pdfTeX1.40.26 (TeX Live2025/dev), BibTeX0.99d. Embedded fonts are inspected;
font files are not distributed.

## Boundaries

This rebuild checks supplied data, figure code and document output. It does not
run inference, recover private KV captures or certify arbitrary-input numerical
equivalence. PR218 S2 recomputation uses the36 published paired ratios, not a new
replay of all72 original time receipts. Inherited intervals remain labelled.
