#!/usr/bin/env python3
"""Generate caption/include kit and native-size figure-story proof, without prose edits."""
from pathlib import Path
import re, subprocess,tempfile,shutil
import fitz

HERE=Path(__file__).resolve().parents[1]
def main():
    source=(HERE/'FIGURE_CAPTION_SUGGESTIONS.md').read_text()
    paragraphs=[p for p in source.split('\n\n') if p.startswith(('**Figure','**Appendix Figure'))]
    assert len(paragraphs)==5
    labels=['overview','verification','m4','state','regimes']
    kit=['% Figure-only placement kit. Paths relative to manuscript/.',
         '% Do not input wholesale: see FIGURE_INTEGRATION.md. Existing prose is untouched.']
    proof=[r'\documentclass[10pt]{article}',r'\usepackage[letterpaper,margin=0.875in]{geometry}',
           r'\usepackage{times,graphicx,amsmath,amssymb,caption}',
           r'\captionsetup{font=small,labelfont=bf}',r'\pagestyle{empty}',r'\begin{document}']
    for i,(p,label) in enumerate(zip(paragraphs,labels),1):
        title,body=p[2:].split('**',1);body=body.strip()
        title=title.split(' — ',1)[1].rstrip('.')
        caption=r'\textbf{'+title+'}. '+body
        caption=caption.replace('×',r'$\times$').replace('–','--').replace('—','---')
        caption=re.sub(r'(?<!\\)%',r'\\%',caption)
        env='figure' if i==3 else 'figure*';width=r'\columnwidth' if i==3 else r'\textwidth'
        kit += ['',f'% {"Appendix A1 only" if i==5 else "Main Figure "+str(i)}',
            '\\begin{'+env+'}[t]',r'\centering',
            f'\\includegraphics[width={width}]{{../figures/pdf/figure{i}.pdf}}',
            '\\caption{'+caption+'}',f'\\label{{fig:{label}}}', '\\end{'+env+'}']
        if i>1:proof.append(r'\clearpage')
        if i==5:proof += [r'\renewcommand{\thefigure}{A\arabic{figure}}',r'\setcounter{figure}{0}']
        proof += [r'\noindent\small Figure-only narrative proof; native MLSys width. Print at 100\%.\par\bigskip',
            r'\begin{center}', '\\begin{minipage}{'+('3.25in' if i==3 else '6.75in')+'}',
            '\\includegraphics[width=\\linewidth]{'+str(HERE/f'pdf/figure{i}.pdf')+'}',
            '\\captionof{figure}{'+caption+'}',r'\end{minipage}',r'\end{center}']
    proof.append(r'\end{document}')
    (HERE/'integration/selected_figures.tex').write_text('\n'.join(kit)+'\n')
    with tempfile.TemporaryDirectory(prefix='heterospec-story-') as td:
        p=Path(td);(p/'story.tex').write_text('\n'.join(proof)+'\n')
        subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error','story.tex'],cwd=p,check=True,capture_output=True)
        log=(p/'story.log').read_text()
        assert 'Overfull' not in log,log
        shutil.copyfile(p/'story.pdf',HERE/'qa/figure_story_proof.pdf')
    doc=fitz.open(HERE/'qa/figure_story_proof.pdf');assert len(doc)==5
    for i,page in enumerate(doc,1):
        page.get_pixmap(matrix=fitz.Matrix(96/72,96/72),colorspace=fitz.csGRAY).save(HERE/f'qa/story_page{i}_gray.png')
    print('Figure-only inclusion kit and 5-page captioned story proof; no overfull TeX boxes.')
if __name__=='__main__':main()
