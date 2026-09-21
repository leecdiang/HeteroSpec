#!/usr/bin/env python3
"""Build exactly two TikZ layouts, vector exports and native-width proofs."""
from pathlib import Path
import json, subprocess, shutil, re
import fitz

HERE=Path(__file__).resolve().parents[1]
E=json.loads((HERE/'data/evidence.json').read_text())
PREAMBLE=r'''\documentclass[border=0pt]{standalone}
\usepackage[T1]{fontenc}
\usepackage{mathptmx}
\usepackage{tikz}
\usetikzlibrary{arrows.meta}
\pdfinfoomitdate=1
\pdftrailerid{}
\pdfsuppressptexinfo=15
\definecolor{ink}{HTML}{222222}
\definecolor{accent}{HTML}{4C6E9E}
\definecolor{mid}{HTML}{777777}
\definecolor{rule}{HTML}{D0D3D6}
\newcommand{\dreal}{D_{\mathrm{real}}}
\newcommand{\rtarget}{R_{\mathrm{target}}}
\newcommand{\microv}{V_k^{\mathrm{micro}}}
\newcommand{\vtwo}{V_2^{\mathrm{micro}}}
\begin{document}
'''

def node(x,y,text,width=None,size=8.5,leading=10.0,anchor='north west',align='left'):
    opts=f'anchor={anchor},align={align},font=\\fontsize{{{size}}}{{{leading}}}\\selectfont'
    if width: opts+=f',text width={width}bp'
    return rf'\node[{opts}] at ({x},{y}) {{{text}}};'+'\n'

def drawing(which):
    height=172.8 if which=='a' else 151.2
    t=[rf'\begin{{tikzpicture}}[x=1bp,y=-1bp,inner sep=0,outer sep=0,text=ink,line width=.45bp]'+'\n',
       rf'\path[use as bounding box] (0,0) rectangle (486,{height});'+'\n']
    for x,w,label in [(3,101,'Local opportunity'),(119,106,'Path qualification'),
                       (242,122,'Stateful realization'),(380,103,'Realized outcome')]:
        t.append(node(x,5,label,size=9.2,leading=11))
        t.append(rf'\draw[rule] ({x},21) -- ({x+w},21);'+'\n')
    t += [node(3,32,r'Acceptance signal\\[3bp]Isolated draft throughput\\[3bp]Target-forward batching\\$\microv$',101),
          node(3,88,r'Acceptance is not $C$.\\$\microv$ is not complete $\rtarget$.',101,size=8,leading=10)]
    # Gate and a solid, explicitly qualified continuation; dashed rejected branch ends here.
    t.append(r'\draw[ink] (119,31) rectangle (225,85);'+'\n')
    t += [node(172,38,r'Correctness qualification',96,size=8.8,leading=10,anchor='north',align='center'),
          node(172,59,r'Chosen token-ID contract',99,size=8,leading=10,anchor='north',align='center'),
          node(172,73,r'admissible path',96,size=8,leading=10,anchor='north',align='center')]
    t.append(r'\draw[ink,-{Stealth[length=3bp,width=2.4bp]}] (105,53) -- (117,53);'+'\n')
    t.append(r'\fill[accent] (225,53) circle[radius=1.9bp];'+'\n')
    t.append(r'\draw[ink,-{Stealth[length=3bp,width=2.4bp]}] (227,53) -- (240,53);'+'\n')
    t.append(r'\draw[mid,dash pattern=on 2bp off 1.5bp] (172,85) -- (172,99);'+'\n')
    t.append(r'\draw[mid,fill=white] (172,99) circle[radius=2bp];'+'\n')
    t.append(node(172,104,r'blocked / diagnostic only',108,size=8,leading=9.5,anchor='north',align='center'))
    # Accounting box: costs and output progress have separate rows, never a new equation.
    t.append(r'\draw[ink] (242,31) rectangle (364,99);'+'\n')
    t.append(node(303,36,r'Realized speculative loop',116,size=8.8,leading=10,anchor='north',align='center'))
    for y,math,label in [(52,r'\dreal','realized draft cost'),(63,r'\rtarget','complete target work'),
                          (74,'X','residual cost'),(88,'C','committed output')]:
        t.append(node(248,y,'$'+math+'$',size=8.5,leading=10))
        t.append(node(281,y,label,size=8.3,leading=10))
    t.append(r'\draw[rule] (247,85) -- (359,85);'+'\n')
    t.append(r'\draw[ink,-{Stealth[length=3bp,width=2.4bp]}] (366,53) -- (378,53);'+'\n')
    t += [node(380,32,r'Qualified integrated\\post-prefill decode' if which=='a' else r'Qualified\\post-prefill decode',103,size=8.8,leading=10.5),
          node(380,65,r'Observed regimes:\\[2bp]profitable\\exact but negative',103,size=8.5,leading=10)]
    if which=='a':
        lo,hi=E['rtx']['batched_ubatch2']['range']; s=E['b570']['serialized']; h=E['state']; m=E['m4']
        t.append(node(119,119,rf'RTX batched: $\vtwo$\\{lo:.3f}--{hi:.3f}; blocked.\\B570 serialized: {s["exact_pairs"]}/{s["total_pairs"]} exact;\\globally inadmissible.',108,size=8,leading=9.5))
        t.append(node(242,119,rf'358H NPU, 8192-token context:\\{h["NPU"]["isolated_8192_tokens_s"]:.2f} vs CPU {h["CPU"]["isolated_8192_tokens_s"]:.2f} tok/s;\\{h["NPU"]["draft_pct"]:.2f}\% replay + proposal;\\{h["NPU"]["speedup"]:.3f}$\times$ prompt-GM speedup.',130,size=8,leading=9.5))
        t.append(node(380,119,rf'M4: separate Metal studies\\24Q: {m["representative"]["speedup"]:.3f}$\times$; HE30: {m["humaneval"]["speedup"]:.3f}$\times$.\\Observed contrast;\\neither diagnosis assigned.',103,size=8,leading=9.5))
    else:
        t.append(node(119,119,r'RTX batched / B570\\diagnostics: qualification failure.',108,size=8,leading=9.5))
        t.append(node(242,119,r'358H NPU: isolated advantage\\does not survive the tested\\stateful integration.',130,size=8,leading=9.5))
        t.append(node(380,119,r'M4: separate Metal studies;\\opposite observed outcomes.\\Neither diagnosis assigned.',103,size=8,leading=9.5))
    # One bounded-scope qualifier, with no implication of an exhaustive performance theory.
    footer=height-10
    t.append(node(3,footer,r'Measured mechanisms are configuration-scoped and non-exhaustive.',size=8,leading=9))
    t.append('\\end{tikzpicture}\n')
    return ''.join(t)

CORE=(r'\textbf{From local opportunity to integrated post-prefill decode outcomes.} '
      r'Local acceptance, isolated drafting, and target-forward batching do not by themselves establish integrated gains. '
      r'Arrows mark evaluation boundaries, not a guarantee of gain. '
      r'The frozen greedy token-ID contract excludes the tested RTX 5070 Ti Laptop batched path; B570 serialization improves agreement without qualifying the full workload. '
      r'Blocked timings remain diagnostic. For the qualified 358H NPU path, full-prefix replay and proposal share one synchronous OpenVINO call, '
      r'and the isolated draft advantage does not survive this measured state interface. '
      r'$D_{\mathrm{real}}$, $R_{\mathrm{target}}$, and $X$ normalize measured draft, complete target, and residual costs by matched target-only token cost; '
      r'$C$ counts all committed output, including correction/bonus tokens. '
      r'M4\textquotesingle s separate frozen studies on the same tested Metal stack yield opposite exact regimes. '
      r'Workload and session conditions differ, and neither diagnosis is assigned to the contrast. '
      r'The measured mechanisms are configuration-scoped and non-exhaustive; timing excludes loading and initial prompt prefill.')

def caption(which):
    if which=='b': return CORE
    m=E['m4']; s=E['state']['NPU']
    extra=(r' The RTX interval spans measured contexts, not a CI; $V_2^{\mathrm{micro}}$ is not complete $R_{\mathrm{target}}$. '
           r'The 358H throughput values are isolated medians; their 95\% repetition-bootstrap CIs are '
           rf'[{E["state"]["NPU"]["isolated_ci95"][0]:.2f}, {E["state"]["NPU"]["isolated_ci95"][1]:.2f}] (NPU) and '
           rf'[{E["state"]["CPU"]["isolated_ci95"][0]:.2f}, {E["state"]["CPU"]["isolated_ci95"][1]:.2f}] (CPU). '
           r'The cost fraction is a ratio of arithmetic totals of speculative post-prefill time; speedup is a prompt geometric mean. '
           rf'The 358H NPU path is {s["exact_pairs"]}/{s["pairs"]} exact, with speedup 95\% CI [{s["ci95"][0]:.3f}, {s["ci95"][1]:.3f}]. '
           rf'M4 24Q and HumanEval30 fixed-$k=2$ are {m["representative"]["exact_pairs"]}/{m["representative"]["pairs"]} and {m["humaneval"]["exact_pairs"]}/{m["humaneval"]["pairs"]} exact; '
           rf'their prompt-GM speedup 95\% CIs are [{m["representative"]["ci95"][0]:.3f}, {m["representative"]["ci95"][1]:.3f}] and [{m["humaneval"]["ci95"][0]:.3f}, {m["humaneval"]["ci95"][1]:.3f}].')
    return CORE+extra

def compile_tex(path,out):
    out.mkdir(parents=True,exist_ok=True)
    p=subprocess.run(['pdflatex','-halt-on-error','-interaction=nonstopmode',f'-output-directory={out}',str(path)],cwd=HERE,capture_output=True,text=True)
    if p.returncode: raise RuntimeError(p.stdout[-7000:])
    assert 'Overfull' not in p.stdout, p.stdout
    return out/(path.stem+'.pdf')

def main():
    qa=HERE/'qa';qa.mkdir(exist_ok=True)
    work=qa/'build';work.mkdir(exist_ok=True)
    costs={}
    for which in ('a','b'):
        dst=HERE/('candidate_'+which); dst.mkdir(exist_ok=True)
        src=dst/'mechanism.tex'
        src.write_text('% Rebuilt by scripts/render.py; edit generator to preserve regeneration.\n'+PREAMBLE+drawing(which)+'\\end{document}\n')
        pdf=compile_tex(src,work/which);shutil.copyfile(pdf,dst/'mechanism.pdf')
        subprocess.run(['pdftocairo','-svg',str(dst/'mechanism.pdf'),str(dst/'mechanism.svg')],check=True)
        # Independent SVG renderer, in addition to Poppler PDF previews.
        sv=fitz.open(dst/'mechanism.svg')
        sv[0].get_pixmap(dpi=96).save(qa/f'{which}_svg_96.png')
        (dst/'caption.tex').write_text(caption(which)+'\n')
        for dpi in (96,180):
            for gray in (False,True):
                prefix=qa/f'{which}_{dpi}_{"gray" if gray else "color"}'
                cmd=['pdftocairo','-png','-singlefile','-r',str(dpi)]
                if gray: cmd+=['-gray']
                subprocess.run(cmd+[str(dst/'mechanism.pdf'),str(prefix)],check=True)
        # True 6.75-in figure+caption block; no fit-to-page scaling.
        proof=(PREAMBLE.replace(r'\usepackage{tikz}',r'\usepackage{graphicx}\usepackage{caption}\usepackage{tikz}')+
            r'\begin{minipage}{6.75in}\centering'+'\n'+
            rf'\includegraphics[width=6.75in]{{candidate_{which}/mechanism.pdf}}'+'\n'+
            r'\captionsetup{font=small,labelformat=empty,skip=5pt}\captionof{figure}{'+caption(which)+r'}\end{minipage}\end{document}'+'\n')
        psrc=work/f'proof_{which}.tex';psrc.write_text(proof)
        pp=compile_tex(psrc,work/('proof_'+which));shutil.copyfile(pp,qa/f'proof_{which}.pdf')
        page=fitz.open(dst/'mechanism.pdf')[0];block=fitz.open(qa/f'proof_{which}.pdf')[0]
        costs[which]=dict(width_in=page.rect.width/72,artwork_height_in=page.rect.height/72,
          captioned_height_in=block.rect.height/72,artwork_area_in2=page.rect.width*page.rect.height/72**2,
          captioned_area_in2=block.rect.width*block.rect.height/72**2)
        subprocess.run(['pdftocairo','-png','-singlefile','-gray','-r','96',str(qa/f'proof_{which}.pdf'),str(qa/f'proof_{which}_gray')],check=True)
    (qa/'page_cost.json').write_text(json.dumps(costs,indent=2)+'\n')
    print(json.dumps(costs,indent=2))

if __name__=='__main__': main()
