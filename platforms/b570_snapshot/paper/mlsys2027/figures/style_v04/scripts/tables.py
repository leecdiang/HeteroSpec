#!/usr/bin/env python3
"""Compile booktabs alternatives from the same frozen records; no manuscript edits."""
from pathlib import Path
import csv,json,subprocess,tempfile,shutil,hashlib,os
HERE=Path(__file__).resolve().parents[1];SOURCE=HERE.parent/'data'
def read(n):return list(csv.DictReader((SOURCE/n).read_text().splitlines()))
def compile_asset(name,body,width):
    (HERE/f'tables/{name}.tex').write_text(body+'\n')
    doc=r'''\documentclass[border=0pt]{standalone}
\usepackage{mathptmx,booktabs,tabularx,array}
\pdfinfoomitdate=1\pdftrailerid{}\pdfsuppressptexinfo=15
\begin{document}
\begin{minipage}{WIDTHin}\fontsize{9}{11}\selectfont
\vspace*{1pt}
BODY
\vspace*{1pt}
\end{minipage}
\end{document}'''.replace('WIDTH',str(width)).replace('BODY',body)
    with tempfile.TemporaryDirectory(prefix='heterospec-style-') as td:
        p=Path(td);(p/'table.tex').write_text(doc)
        r=subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error','table.tex'],cwd=p,capture_output=True,text=True)
        if r.returncode:raise RuntimeError(r.stdout)
        log=(p/'table.log').read_text();assert 'Overfull' not in log,log
        shutil.copyfile(p/'table.pdf',HERE/f'pdf/{name}.pdf')
    subprocess.run(['pdftocairo','-svg',str(HERE/f'pdf/{name}.pdf'),str(HERE/f'svg/{name}.svg')],check=True)
    (HERE/f'qa/{name}_render.json').write_text(json.dumps(dict(asset=name,engine='LaTeX booktabs/mathptmx',width_in=width,
        overfull_boxes=0,output_sha256={ext:hashlib.sha256((HERE/f'{ext}/{name}.{ext}').read_bytes()).hexdigest() for ext in ['pdf','svg']}),indent=2)+'\n')
def main():
    d=read('figure1_overview.csv');names=['M4 HumanEval30, $k=2$','M4 representative 24Q','RTX 5070 Ti Laptop, batched','358H NPU draft']
    rows=[]
    for i,r in enumerate(d):
        local=(rf'$V_2^{{\mathrm{{micro}}}}={float(r["local_low"]):.3f}$--${float(r["local_high"]):.3f}$' if i<3 else rf'NPU/CPU: {float(r["local_high"]):.2f} vs {float(r["local_low"]):.2f} tokens/s')
        outcome='Blocked; no admissible speedup' if r['status']=='blocked' else ('Profitable: ' if float(r['speedup'])>1 else 'Negative: ')+rf'{float(r["speedup"]):.3f}$\times$; {r["exact"]} exact'
        rows.append(' & '.join([names[i],local,outcome])+r' \\')
    body='\n'.join([r'\setlength{\tabcolsep}{5pt}',r'\renewcommand{\arraystretch}{1.2}',
        r'\begin{tabularx}{\linewidth}{@{}p{1.84in}p{2.30in}X@{}}',r'\toprule',r'Case & Local indicator & Realized outcome \\',r'\midrule',*rows,r'\bottomrule',r'\end{tabularx}'])
    compile_asset('figure1B_table',body,6.75)
    regimes=read('figure5_regimes.csv');real={r['device']:r for r in read('figure4_realized.csv')};rows=[]
    for r in regimes:
        q=('Qualified; '+r['exact']+' exact') if r['admissibility']=='qualified' else ('Blocked; gate failed' if r['case']=='RTX batched' else 'Inadmissible; '+r['exact']+' exact')
        if r['case']=='RTX serialized controls':q=r'Qualified;\newline 90/90 each exact'
        outcome={'profitable':'Profitable','negative':'Negative','not_admissible':'Not admissible'}[r['profitability']]
        evidence={'PRIMARY':'P','SECONDARY':'S','MECHANISM_SUPPORTED':'M','DIAGNOSTIC':'D'}[r['evidence_class']]
        mechanism=r['mechanism']
        if r['case'].startswith('358H'):
            evidence='P/M';dev=r['case'].split()[-1];v=real[dev]
            mechanism+=rf'\newline {float(v["target_pct"] if dev=="CPU" else v["draft_pct"]):.2f}\% '+('target side' if dev=='CPU' else 'replay + proposal')
        rows.append(' & '.join([r['case'],q,outcome,evidence,mechanism])+r' \\')
    body='\n'.join([r'\setlength{\tabcolsep}{4pt}',r'\renewcommand{\arraystretch}{1.15}',
        r'\begin{tabularx}{\linewidth}{@{}p{1.38in}p{1.29in}p{.79in}p{.35in}X@{}}',r'\toprule',
        r'Case & Qualification & Outcome & Class & Case annotation \\',r'\midrule',*rows,r'\bottomrule',r'\end{tabularx}'])
    compile_asset('appendix_table',body,6.75)
    # This is an optional prose replacement, not edited manuscript text.
    a,b,rx,n=d
    prose=(f"The shared M4 Metal path has a separately measured $V_2^{{\\mathrm{{micro}}}}$ range of {float(a['local_low']):.3f}--{float(a['local_high']):.3f}, yet the separate HumanEval30 ($k=2$) and representative-24Q studies yield {float(a['speedup']):.3f}$\\times$ ({a['exact']} exact) and {float(b['speedup']):.3f}$\\times$ ({b['exact']} exact). "
       f"RTX batched verification costs {float(rx['local_low']):.3f}--{float(rx['local_high']):.3f} baseline steps but fails qualification, so it has no admissible speedup. "
       f"At 8,192 tokens, isolated NPU/CPU drafting reaches {float(n['local_high']):.2f}/{float(n['local_low']):.2f} tokens/s, while the qualified 358H NPU path yields {float(n['speedup']):.3f}$\\times$ ({n['exact']} exact). "
       "Speedups cover post-prefill decode; the detailed figures retain campaign-specific intervals and measurement boundaries. These heterogeneous observations do not isolate workload-only causality.")
    compile_asset('figure1B_prose',prose,3.25)
    print('Booktabs overview, appendix inventory, and optional prose alternative compiled to PDF/SVG.')
if __name__=='__main__':main()
