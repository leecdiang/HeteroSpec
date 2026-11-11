#!/usr/bin/env python3
"""Render native-size color/grayscale, caption transfer, comparisons and page costs."""
from pathlib import Path
import json,subprocess,tempfile,shutil,csv
import fitz
from PIL import Image
HERE=Path(__file__).resolve().parents[1];FIG=HERE.parent;MAN=FIG.parent/'manuscript'
NAMES=['figure1A','figure1B_table','figure1B_prose','verification','m4','state','appendix_table']
def caption(filename):
    s=(MAN/'figures'/filename).read_text();start=s.index('\\caption{')+len('\\caption{');level=1;i=start
    while level:
        if s[i]=='{' and s[i-1]!='\\':level+=1
        if s[i]=='}' and s[i-1]!='\\':level-=1
        i+=1
    return s[start:i-1]
def compile_block(name,asset,width,cap):
    # A native-width minipage gives an explicit artwork-plus-caption height.
    tex=r'''\documentclass[border=0pt]{standalone}
\usepackage{mathptmx,graphicx,caption,amsmath,amssymb}
\captionsetup{font=small,labelformat=empty,skip=6pt}
\pdfinfoomitdate=1\pdftrailerid{}\pdfsuppressptexinfo=15
\begin{document}\begin{minipage}{WIDTHin}
\includegraphics[width=\linewidth]{ASSET}
CAPTION
\end{minipage}\end{document}'''.replace('WIDTH',str(width)).replace('ASSET',str(asset)).replace('CAPTION',r'\captionof{figure}{'+cap+'}' if cap else '')
    tex=tex.replace(r'Figures~\ref{fig:m4}, \ref{fig:verification}, and~\ref{fig:state}', 'the M4, verification, and 358H figures')
    for lab,word in [('fig:state','the 358H figure'),('fig:m4','the M4 figure'),('fig:verification','the verification figure')]:
        tex=tex.replace(r'Figure~\ref{'+lab+'}',word).replace(r'\ref{'+lab+'}',word)
    with tempfile.TemporaryDirectory(prefix='style-caption-') as td:
        p=Path(td);(p/'block.tex').write_text(tex)
        r=subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error','block.tex'],cwd=p,capture_output=True,text=True)
        if r.returncode:raise RuntimeError(r.stdout)
        assert 'Overfull' not in (p/'block.log').read_text(),name
        doc=fitz.open(p/'block.pdf');out=fitz.open();out.insert_pdf(doc)
    return out
def main():
    mapping={'figure1A':'00_overview.tex','figure1B_table':'00_overview.tex','verification':'03_verification.tex','m4':'02_m4.tex','state':'04_358h.tex','appendix_table':'05_regimes.tex'}
    caps={n:caption(p) for n,p in mapping.items()}
    caps['verification']+=r' M4 contexts are 512/2,048/8,192 tokens, RTX depths 0/256, and B570 contexts 512/2,048; nearby cells may overlap. Circles denote batched/fast paths and squares serialized paths. Ranges are not CIs; $V_2^{\mathrm{micro}}\ne R_{\mathrm{target}}$.'
    real=list(csv.DictReader((FIG/'data/figure4_realized.csv').read_text().splitlines()));c,n=real
    caps['state']+=(rf" CPU replay plus proposal is {float(c['draft_pct']):.2f}\%; NPU complete target work is {float(n['target_pct']):.2f}\%. Residuals are {float(c['residual_s'])*1000:.2f} ms ({float(c['residual_pct']):.2f}\%) and {float(n['residual_s'])*1000:.2f} ms ({float(n['residual_pct']):.2f}\%). Prompt-GM speedup 95\% CIs are [{float(c['ci_low']):.3f}, {float(c['ci_high']):.3f}] and [{float(n['ci_low']):.3f}, {float(n['ci_high']):.3f}], respectively. The vertical dashed line is the shared arithmetic-mean baseline. Isolated throughput excludes the full-prefix state cost; its device marks are horizontally offset for readability.")
    caps['appendix_table']+=r' P: primary; S: secondary; M: mechanism; D: diagnostic. RTX serialized groups CPU-to-RTX and RTX-to-RTX controls, 90/90 exact pairs each. Fractions denote generated-token equality, not functional correctness.'
    caps['figure1B_prose']=''
    (HERE/'qa/caption_transfer.json').write_text(json.dumps({n:dict(source_wrapper='paper/mlsys2027/manuscript/figures/'+mapping[n] if n in mapping else None,caption=caps[n]) for n in NAMES},indent=2)+'\n')
    md=['# Caption handoff — no manuscript edits','',
        'Existing checkpoint captions are retained below, with context moved out of artwork appended. Figure numbers/float placement remain an integration decision. LaTeX references point to the existing manuscript labels.','']
    for n in NAMES:
        if caps[n]:md += ['## '+n,'','```latex',caps[n],'```','']
    (HERE/'CAPTION_HANDOFF.md').write_text('\n'.join(md)+'\n')
    proof=fitz.open();sizes={}
    for name in NAMES:
        path=HERE/f'pdf/{name}.pdf';doc=fitz.open(path);w,h=doc[0].rect.width,doc[0].rect.height
        for dpi in [96,180]:
            im=doc[0].get_pixmap(matrix=fitz.Matrix(dpi/72,dpi/72));dest=HERE/f'qa/{name}_{dpi}dpi.png';im.save(dest)
            Image.open(dest).convert('L').save(HERE/f'qa/{name}_{dpi}dpi_gray.png')
        block=compile_block(name,path,w/72,caps[name]);bh=block[0].rect.height
        page=proof.new_page(width=612,height=792);page.insert_text((63,35),name+' | native width; print at 100%',fontsize=10)
        x=(612-w)/2;page.show_pdf_page(fitz.Rect(x,60,x+w,60+bh),block,0)
        assert 60+bh<755
        sizes[name]=dict(width_in=w/72,artwork_height_in=h/72,with_caption_height_in=bh/72,area_with_caption_in2=w*bh/72**2)
    old=compile_block('current_overview',FIG/'pdf/figure1.pdf',6.75,caption('00_overview.tex'))
    sizes['current_overview']=dict(width_in=6.75,artwork_height_in=3.63,with_caption_height_in=old[0].rect.height/72,area_with_caption_in2=6.75*old[0].rect.height/72)
    sizes['remove_reuse_existing_intro']=dict(additional_float_height_in=0,additional_text_height_in=0,
        note='Current introduction already states all four cases; details remain in M4/verification/358H evidence. Optional prose sample is a replacement, not an extra paragraph.')
    (HERE/'qa/page_cost.json').write_text(json.dumps(sizes,indent=2)+'\n')
    proof.save(HERE/'qa/STYLE_PROOF.pdf',garbage=4,deflate=True,no_new_id=True)
    comp=fitz.open()
    for i,name in [(1,'figure1A'),(2,'verification'),(3,'m4'),(4,'state'),(5,'appendix_table')]:
        page=comp.new_page(width=612,height=792);page.insert_text((63,30),f'Current asset {i} / v0.4 {name} | equal native width',fontsize=11)
        y=61
        for label,path in [('CURRENT',FIG/f'pdf/figure{i}.pdf'),('v0.4',HERE/f'pdf/{name}.pdf')]:
            d=fitz.open(path);w,h=d[0].rect.width,d[0].rect.height;x=(612-w)/2
            page.insert_text((x,y),label,fontsize=9);page.show_pdf_page(fitz.Rect(x,y+12,x+w,y+12+h),d,0);y+=h+43
        assert y<785
    comp.save(HERE/'qa/STYLE_COMPARISON.pdf',garbage=4,deflate=True,no_new_id=True)
    for doc,prefix in [(proof,'proof'),(comp,'comparison')]:
        for i,page in enumerate(doc,1):
            page.get_pixmap(matrix=fitz.Matrix(96/72,96/72),colorspace=fitz.csGRAY).save(HERE/f'qa/{prefix}_{i}_gray.png')
    print('Seven native-width captioned proofs; five CURRENT/STYLE comparisons; measured caption-inclusive page costs.')
if __name__=='__main__':main()
