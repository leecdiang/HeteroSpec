#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-1794387600}"
export FORCE_SOURCE_DATE=1
HS_PYTHON="${PYTHON:-python3}"
HS_TEX="${PDFLATEX:-pdflatex}"
HS_BIB="${BIBTEX:-bibtex}"
mkdir -p validation_logs
if [[ "${1:-}" != "--tex-only" ]]; then
  "$HS_PYTHON" scripts/derive.py > validation_logs/derive.log
  "$HS_PYTHON" scripts/derive_revision.py > validation_logs/derive_revision.log
  "$HS_PYTHON" scripts/derive_rewrite.py > validation_logs/derive_rewrite.log
  "$HS_PYTHON" scripts/build_tables.py > validation_logs/tables.log
  "$HS_PYTHON" scripts/build_figures.py > validation_logs/figures.log
  "$HS_PYTHON" scripts/check_figures.py > validation_logs/figure_checks.log
  "$HS_PYTHON" -m unittest discover -s scripts -p 'test_*.py' -v > validation_logs/evidence_tests.log 2>&1
fi
for entry in main supplement; do
  "$HS_TEX" -interaction=nonstopmode -halt-on-error "$entry.tex" > "validation_logs/$entry-pass1.log"
  "$HS_BIB" "$entry" > "validation_logs/$entry-bibtex.log"
  "$HS_TEX" -interaction=nonstopmode -halt-on-error "$entry.tex" > "validation_logs/$entry-pass2.log"
  "$HS_TEX" -interaction=nonstopmode -halt-on-error "$entry.tex" > "validation_logs/$entry-pass3.log"
  "$HS_PYTHON" - "$entry.log" <<'CHECK'
import re,sys
from pathlib import Path
p=Path(sys.argv[1]);text=p.read_text(errors='replace')
patterns=[r'Undefined control sequence',r'undefined references',r'undefined citations',
          r'multiply-defined labels',r'Overfull \\hbox',r'Missing character:',r'LaTeX Error']
found=[p for p in patterns if re.search(p,text)]
if found:raise SystemExit(f'Unresolved reference or layout error in {p}: {found}')
CHECK
done
printf 'Built main.pdf and supplement.pdf.\n'
