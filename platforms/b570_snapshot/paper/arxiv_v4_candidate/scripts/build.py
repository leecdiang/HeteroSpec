#!/usr/bin/env python3
"""Build and check the complete article and supplement; no network/native inference."""
from __future__ import annotations
import argparse,json,os,re,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def run(command:list[str],cwd:Path,log:Path,env:dict[str,str])->None:
    with log.open('w',encoding='utf-8') as stream:
        result=subprocess.run(command,cwd=cwd,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=240)
    if result.returncode:
        raise RuntimeError(f'Command failed ({result.returncode}): {command}\n'+log.read_text(errors='replace')[-4500:])

def main()->None:
    ap=argparse.ArgumentParser();ap.add_argument('--cached-bbl',action='store_true',help='Use the included bibliography without running BibTeX');args=ap.parse_args()
    latex=shutil.which('pdflatex')
    bib=next((p for name in ('bibtex','bibtex.original','bibtex8') if (p:=shutil.which(name))),None)
    if not latex or (not args.cached_bbl and not bib):raise SystemExit('Install pdfLaTeX and BibTeX (or use --cached-bbl with the included main.bbl).')
    logs=ROOT/'build_logs';logs.mkdir(exist_ok=True);env=dict(os.environ)
    env['BIBINPUTS']=str(ROOT)+os.pathsep+env.get('BIBINPUTS','');env['BSTINPUTS']=str(ROOT)+os.pathsep+env.get('BSTINPUTS','')
    run([sys.executable,'-B','anc/check.py'],ROOT,logs/'reported_checks.json',env)
    run([sys.executable,'-B','-m','unittest','test_release','test_closure','test_refinement','test_round3','test_major_revision','test_native_followup','-v'],ROOT/'anc',logs/'tests.txt',env)
    cmd=[latex,'-no-shell-escape','-interaction=nonstopmode','-halt-on-error','-file-line-error','main.tex']
    run(cmd,ROOT,logs/'pass1.txt',env)
    if not args.cached_bbl:run([bib,'main'],ROOT,logs/'bibtex.txt',env)
    for i in (2,3):run(cmd,ROOT,logs/f'pass{i}.txt',env)
    log=(ROOT/'main.log').read_text(errors='replace')
    patterns=[r'Overfull \\hbox',r'Overfull \\vbox',r'undefined',r'Missing character:',r'destination with the same identifier']
    failures=[s for s in log.splitlines() if any(re.search(p,s,re.I) for p in patterns)]
    if failures:raise RuntimeError('Unresolved build warnings:\n'+'\n'.join(failures))
    pdf=ROOT/'main.pdf'
    if not pdf.exists() or pdf.stat().st_size<10000:raise RuntimeError('No valid PDF produced')
    print(json.dumps({'status':'BUILD_AND_REPORTED_CHECKS_PASS','pdf':'main.pdf','bytes':pdf.stat().st_size,'visual_qa':'This build requires separate page/figure inspection; see the release validation archive for the inspected source/PDF hashes.','new_native_executions':0},indent=2))
if __name__=='__main__':main()
