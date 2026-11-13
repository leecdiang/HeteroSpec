#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-1794355200}"
export FORCE_SOURCE_DATE=1
PYTHON="${PYTHON:-python3}"
TEX="${PDFLATEX:-pdflatex}"
BIB="${BIBTEX:-bibtex}"
# A broken local wrapper is not a successful build. Use an installed original only
# when the ordinary command cannot be executed; no download or system edit.
if ! command -v "$BIB" >/dev/null 2>&1; then
  if command -v bibtex.original >/dev/null 2>&1; then BIB=bibtex.original;
  else echo 'No executable BibTeX found. Install/repair an approved TeX environment.' >&2; exit 2; fi
fi
command -v "$TEX" >/dev/null
mkdir -p validation_logs
"$PYTHON" scripts/derive.py > validation_logs/derive.log
"$PYTHON" scripts/derive_revision.py > validation_logs/derive_revision.log
"$PYTHON" scripts/build_tables.py > validation_logs/tables.log
"$PYTHON" scripts/build_figures.py > validation_logs/figures.log
"$PYTHON" -m unittest discover -s scripts -p 'test_*.py' -v > validation_logs/tests-normal.log 2>&1
"$PYTHON" -O -m unittest discover -s scripts -p 'test_*.py' -v > validation_logs/tests-optimized.log 2>&1
for entry in main journal; do
 "$TEX" -interaction=nonstopmode -halt-on-error "$entry.tex" > "validation_logs/$entry-1.log"
 "$BIB" "$entry" > "validation_logs/$entry-bibtex.log"
 "$TEX" -interaction=nonstopmode -halt-on-error "$entry.tex" > "validation_logs/$entry-2.log"
 "$TEX" -interaction=nonstopmode -halt-on-error "$entry.tex" > "validation_logs/$entry-3.log"
 if grep -Eq 'Undefined control sequence|There were undefined references|There were undefined citations|Overfull \\hbox|Missing character:' "$entry.log"; then
   echo "Unresolved layout/reference error in $entry.log" >&2; exit 3
 fi
done
printf 'Offline data checks and main/journal builds finished. Inspect rendered pages before release.\n'
