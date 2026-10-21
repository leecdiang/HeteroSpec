#!/usr/bin/env python3
"""Build the two manuscript PDFs without model execution or network access."""
from __future__ import annotations
import argparse, os, re, shutil, subprocess
from pathlib import Path

def run(command: list[str], cwd: Path, logfile: Path, env: dict[str,str]) -> None:
    with logfile.open('w', encoding='utf-8') as f:
        result = subprocess.run(command, cwd=cwd, env=env, stdout=f, stderr=subprocess.STDOUT, timeout=120)
    if result.returncode:
        tail='\n'.join(logfile.read_text(errors='replace').splitlines()[-35:])
        raise RuntimeError(f'Build failed: {command}\n{tail}')

def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument('--document', choices=['main','supplement','both'],default='both')
    args=ap.parse_args()
    root=Path(__file__).resolve().parents[1]
    output=root/'output'; output.mkdir(exist_ok=True)
    latex=shutil.which('pdflatex')
    bib=next((x for name in ('bibtex','bibtex.original','bibtex8') if (x:=shutil.which(name))),None)
    if not latex or not bib:
        raise SystemExit('Install pdfLaTeX and BibTeX plus the TeX packages specified in README.md.')
    env=dict(os.environ)
    env['BIBINPUTS']=str(root)+os.pathsep+env.get('BIBINPUTS','')
    env['BSTINPUTS']=str(root)+os.pathsep+env.get('BSTINPUTS','')
    stems=['main','supplement'] if args.document=='both' else [args.document]
    for stem in stems:
        cmd=[latex,'-interaction=nonstopmode','-halt-on-error','-output-directory=output',f'{stem}.tex']
        run(cmd,root,output/f'{stem}.pass1.txt',env)
        run([bib,stem],output,output/f'{stem}.bibtex.txt',env)
        for i in (2,3): run(cmd,root,output/f'{stem}.pass{i}.txt',env)
        log=(output/f'{stem}.log').read_text(errors='replace')
        bad=[r'Overfull \\hbox',r'Overfull \\vbox',r'LaTeX Warning: Reference .* undefined',r'Citation .* undefined',r'There were undefined']
        if any(re.search(p,log,re.S if '.*' in p else 0) for p in bad):
            raise RuntimeError(f'Unresolved layout/reference warnings in {stem}.log; inspect before delivery.')
        pdf=output/f'{stem}.pdf'
        if not pdf.is_file() or pdf.stat().st_size<10000: raise RuntimeError(f'Missing/empty {pdf}')
        print(f'Built {pdf.name}: {pdf.stat().st_size:,} bytes')
if __name__=='__main__': main()
