#!/usr/bin/env python3
"""Prepare a one-level, editable LaTeX source archive. No submission is made."""
import argparse
from pathlib import Path
import re
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--out',type=Path,required=True)
args=ap.parse_args()
out=args.out.resolve()
if out.exists(): raise SystemExit('Use a new output directory; existing sources are not overwritten.')
out.mkdir(parents=True)
copied={}

def add(source):
    source=source.resolve()
    name=source.name
    if name in copied and copied[name]!=source:
        raise ValueError('Flattening filename collision: '+name)
    if name in copied:return
    copied[name]=source
    if source.suffix=='.tex':
        text=source.read_text()
        def inc(m):
            dep=ROOT/m.group(1)
            if not dep.suffix:dep=dep.with_suffix('.tex')
            add(dep)
            return r'\input{'+dep.stem+'}'
        text=re.sub(r'\\input\{([^}]+)\}',inc,text)
        text=text.replace(r'\graphicspath{{figures/}}',r'\graphicspath{{./}}')
        (out/name).write_text(text)
    else: shutil.copy2(source,out/name)

for name in ['main.tex','supplement.tex','highlights.tex','highlights.txt',
             'references.bib','cas-dc.cls','cas-common.sty']:
    add(ROOT/name)
for file in (ROOT/'figures').glob('*.pdf'):add(file)
for name in ['main.bbl','supplement.bbl']:
    if (ROOT/'build'/name).exists():add(ROOT/'build'/name)
(out/'README.txt').write_text(
    'AUTHOR-REVIEW SOURCES: not a submitted or final author-approved manuscript.\n'
    'All TeX inputs, figures, class/style files and bibliography are at this level.\n'
    'Use a complete TeX Live installation. Build each document with pdflatex.\n'
    'For main/supplement: pdflatex, bibtex, pdflatex, pdflatex.\n'
    'The included .bbl files also support builds without rerunning BibTeX.\n'
    'Numeric citations use the standard TeX Live unsrtnat style.\n'
    'The official CAS files are unchanged; their complete original distribution\n'
    'and license notices are in the companion author-review package.\n'
    'Final author declarations and data deposit/access terms remain pending.\n')
archive=out.with_suffix('.zip')
if archive.exists():raise SystemExit('Archive already exists; use a new destination.')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for f in sorted(out.iterdir()):z.write(f,f.name)
print(f'Created {len(list(out.iterdir()))} one-level source files and {archive.name}.')
