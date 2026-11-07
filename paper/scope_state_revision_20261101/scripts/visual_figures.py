"""Vector encodings for the visual review. Consumes unchanged reconstructed data.
No estimates, filters or scientific selections are added here.
"""
from __future__ import annotations


def _axis(x, width, title, ylabel, xmin, xmax, ticks, xlabel, height=3.25):
    return [r'\begin{axis}[at={('+f'{x}cm,0cm'+r')},anchor=south west,scale only axis,',
            f'width={width}cm,height={height}cm,xmin={xmin},xmax={xmax},',
            ylabel+',xtick={'+ticks+r'},',
            r'axis lines*=left,axis line style={aux,line width=.5pt},tick style={aux},',
            r'tick label style={font=\footnotesize},grid=major,grid style={gray!13},',
            r'title={'+title+r'},title style={font=\small,yshift=4pt},',
            r'xlabel={'+xlabel+r'},xlabel style={font=\footnotesize,align=center},clip=false]']


def _row(values, pooled, y, color):
    # Offsets separate three actual dates from the pooled estimate; y has no metric meaning.
    out=[r'\addplot['+color+r',line width=.9pt,forget plot] coordinates {'+
         f'({min(values):.12f},{y-.19:.2f})({max(values):.12f},{y-.19:.2f})'+r'};']
    for v,dy,mark in zip(values,(-.07,.07,.21),('o','triangle','square')):
        out.append(r'\addplot[only marks,mark='+mark+r',mark size=2.2pt,line width=.65pt,'+color+r',forget plot] coordinates {'+f'({v:.12f},{y+dy:.2f})'+r'};')
    out.append(r'\addplot[only marks,mark=diamond*,mark size=2.7pt,'+color+r',forget plot] coordinates {'+f'({pooled:.12f},{y-.19:.2f})'+r'};')
    out.append(r'\node[font=\scriptsize,text='+color+r',anchor=north] at (axis cs:'+f'{pooled:.12f},{y-.31:.2f}'+r'){'+f'{pooled:.3f}'+r'};')
    return out


def scope_figure(a):
    fig=[r'% Generated from immutable session logs; ranges are observed date ranges.',
         r'\begin{tikzpicture}']
    for fam,x,title in [('Qwen',.6,r'\textbf{A}\quad Qwen3'),('SmolLM2',6.0,r'\textbf{B}\quad SmolLM2')]:
        fig+=_axis(x,4.15,title,r'ymin=.35,ymax=3.48,ytick={1,2,3},yticklabels={QB,PQ,GS}',.64,1.30,'.7,.9,1,1.2',r'$D_L=T_{M_L}/T_{C_L}$\\$>1$: drafting faster')
        fig.append(r'\addplot[aux,dashed,forget plot] coordinates {(1,.35)(1,3.48)};')
        f=a['rtx'][fam]
        for k,y,c in [('D_GS',3,'aux'),('D_PQ',2,'target'),('D_QB',1,'qualified')]:
            fig+=_row([d['ratios'][k] for d in f['dates']],f['ratios'][k],y,c)
        fig.append(r'\end{axis}')
    fig+=_axis(12.2,4.1,r'\textbf{C}\quad Scope interaction',r'ymin=.35,ymax=2.48,ytick={1,2},yticklabels={SmolLM2,Qwen3}',.98,1.56,'1,1.2,1.4',r'$\Gamma=D_{\QB}/D_{\GS}$\\$>1$: higher draft value')
    fig.append(r'\addplot[aux,dashed,forget plot] coordinates {(1,.35)(1,2.48)};')
    for fam,y in [('Qwen',2),('SmolLM2',1)]:
        f=a['rtx'][fam];k='I_QB_vs_GS'
        fig+=_row([d['ratios'][k] for d in f['dates']],f['ratios'][k],y,'target')
    fig.append(r'\end{axis}')
    fig += [r'\node[anchor=north,font=\footnotesize] at (8.25,-1.15) {'+
            r'\tikz[baseline=-.5ex]\draw[aux,line width=.65pt] (0,0) circle (2pt);\ 30 Oct\quad '+
            r'\tikz[baseline=-.5ex]\draw[aux,line width=.65pt] (0,.08)--(.08,-.06)--(-.08,-.06)--cycle;\ 31 Oct\quad '+
            r'\tikz[baseline=-.5ex]\draw[aux,line width=.65pt] (-.06,-.06) rectangle (.06,.06);\ 1 Nov\quad '+
            r'\tikz[baseline=-.5ex]\fill[aux] (0,.08)--(.06,0)--(0,-.08)--(-.06,0)--cycle;\ Pooled\quad '+
            r'\tikz[baseline=-.5ex]\draw[aux,line width=.9pt] (0,0)--(.35,0);\ Date range (not CI)};',
            r'\end{tikzpicture}','']
    return '\n'.join(fig)


def producer_figure(a):
    ids=['G/582','G/4140','G/1184','G/2279','M/P1865','M/G846','M/P1804','M/G465']
    mat={(r['input_index'],r['producer'],r['consumer']):r for r in a['b570']['matrix']}
    fig=[r'% Full 48-cell matrix in original input order; two fixed-R cases annotated.',
         r'\begin{tikzpicture}[x=1cm,y=1cm,font=\footnotesize]',
         r'\node[anchor=west,font=\small] at (0,1.28) {\textbf{A}\quad Complete strict-reference matrix};',
         r'\node at (3.05,.80) {P1 state};',r'\node at (5.75,.80) {P4T state};',
         r'\draw[aux,line width=.45pt] (2.03,.57)--(4.06,.57);',
         r'\draw[aux,line width=.45pt] (4.73,.57)--(6.76,.57);',
         r'\node[anchor=east] at (1.65,.27) {Input};']
    xs=[2.35,3.05,3.75,5.05,5.75,6.45]
    for x,c in zip(xs,('C1','PQ','QB')*2):fig.append(r'\node at ('+f'{x},.27'+'){'+c+'};')
    for i,name in enumerate(ids):
        y=-.26-i*.48
        if i in (4,6):
            fig.append(r'\fill[light] (.18,'+f'{y-.225:.3f}'+r') rectangle (6.84,'+f'{y+.225:.3f}'+');')
        fig.append(r'\node[anchor=east'+(',font=\\footnotesize\\bfseries' if i in (4,6) else '')+r'] at (1.65,'+f'{y:.3f}'+'){'+name+'};')
        for x,(p,c) in zip(xs,((p,c) for p in ('P1','P4T') for c in ('C1','PQ','QB'))):
            eq=mat[str(i),p,c]['strict_reference_equal']=='True';col='qualified' if eq else 'draft';sym='$=$' if eq else r'$\ne$'
            fig.append(r'\node[draw='+col+r',fill='+col+r'!7,line width=.5pt,minimum width=5.9mm,minimum height=3.9mm,inner sep=0pt,text='+col+r'] at ('+f'{x},{y:.3f}'+'){'+sym+'};')
    fig += [r'\node[anchor=west,font=\scriptsize] at (.15,-4.08) {$=$ matches the input\textquotesingle s strict $R$; $\ne$ differs.};',
            r'\node[anchor=west,font=\scriptsize] at (.15,-4.43) {48 completed cells; 39 match $R$. PQ/QB agree in all 16 input--producer pairs.};',
            r'\draw[aux!40,line width=.45pt] (7.25,1.25)--(7.25,-4.45);',
            r'\node[anchor=west,font=\small] at (7.65,1.28) {\textbf{B}\quad Producer changes eligibility at fixed $R$};',
            r'\node[anchor=west,align=left] at (7.65,.68) {Prealgebra/1865 and /1804 (shaded rows):\\each input keeps the same $R$ under both producers.};',
            r'\node[anchor=west] at (7.75,-.15) {Receiver};',
            r'\node at (11.40,-.15) {P1 state};',r'\node at (14.75,-.15) {P4T state};',
            r'\draw[aux,line width=.45pt] (7.75,-.43)--(16.20,-.43);',
            r'\node[anchor=west] at (7.75,-.88) {C1};',
            r'\node[draw=qualified,fill=qualified!7,text=qualified,minimum width=19mm,minimum height=7mm] at (11.40,-.88) {$=R$};',
            r'\node[draw=qualified,fill=qualified!7,text=qualified,minimum width=19mm,minimum height=7mm] at (14.75,-.88) {$=R$};',
            r'\node[anchor=west] at (7.75,-1.75) {PQ and QB};',
            r'\node[draw=draft,fill=draft!7,text=draft,minimum width=19mm,minimum height=7mm] at (11.40,-1.75) {$\ne R$};',
            r'\node[draw=qualified,fill=qualified!7,text=qualified,minimum width=19mm,minimum height=7mm] at (14.75,-1.75) {$=R$};',
            r'\draw[flow] (12.47,-1.75)--(13.67,-1.75);',
            r'\node[anchor=west,align=left] at (7.75,-2.75) {Changed input to the clean receiver:\\sequence KV \emph{and} initial logits.};',
            r'\node[anchor=west,align=left,font=\scriptsize] at (7.75,-3.56) {P1 first departures: outputs 5 and 25 (one-based).\\G/1184 is distinct: the serial endpoint changes too.};',
            r'\end{tikzpicture}','']
    return '\n'.join(fig)
