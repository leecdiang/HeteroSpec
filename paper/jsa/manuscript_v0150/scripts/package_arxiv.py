#!/usr/bin/env python3
"""Create a clean single-entry arXiv source ZIP and compile main + supplement.
Scientific input files are copied unchanged; only document assembly is different.
"""
import hashlib,json,os,re,shutil,subprocess,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output'
def sha(b):return hashlib.sha256(b).hexdigest()
def run(args,cwd):
    r=subprocess.run(args,cwd=cwd,capture_output=True,text=True,env={**os.environ,'SOURCE_DATE_EPOCH':'1791849600'},timeout=180)
    if r.returncode:raise RuntimeError(r.stdout[-5000:]+r.stderr[-1000:])
    return r.stdout

def main():
    main=(ROOT/'main.tex').read_text();sup=(ROOT/'supplement.tex').read_text()
    body=sup.split(r'\end{frontmatter}',1)[1].split(r'\bibliographystyle',1)[0]
    abstract=re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}',sup,re.S).group(1).strip()
    transition=r'''
\flushcolsend
\clearpage
\raggedcolsend
\setcounter{section}{0}
\setcounter{subsection}{0}
\setcounter{table}{0}
\setcounter{figure}{0}
\setcounter{equation}{0}
\renewcommand{\thesection}{S\arabic{section}}
\renewcommand{\thetable}{S\arabic{table}}
\renewcommand{\thefigure}{S\arabic{figure}}
\renewcommand{\theequation}{S\arabic{equation}}
\renewcommand{\dbltopfraction}{.9}
\renewcommand{\textfraction}{.08}
\pdfbookmark[0]{Supplementary Material}{supplement-start}
\twocolumn[{\centering\Large\bfseries Supplementary Material\par\vspace{6pt}
\normalsize\normalfont ABSTRACTTEXT\par\vspace{12pt}}]
'''.replace('ABSTRACTTEXT',abstract)
    combined=main.split(r'\end{document}')[0]+transition+body+'\n\\end{document}\n'
    combined=combined.replace(r'\begin{document}',r'\hypersetup{pdfsubject={arXiv update prepared from JSA manuscript v0.15.3}}'+'\n'+r'\begin{document}')
    expected=re.findall(r'\\input\{([^}]+)\}',main)+re.findall(r'\\input\{([^}]+)\}',body)
    assert re.findall(r'\\input\{([^}]+)\}',combined)==expected
    payload={'arxiv.tex':combined.encode()}
    def include(text):
        for name in re.findall(r'\\input\{([^}]+)\}',text):
            key=name if name.endswith('.tex') else name+'.tex'
            if key not in payload:
                payload[key]=(ROOT/key).read_bytes();include(payload[key].decode())
    include(combined)
    for key in ['references.bib','psql-num.bst']:payload[key]=(ROOT/key).read_bytes()
    payload['00README.json']=(json.dumps(dict(process=dict(compiler='pdflatex'),sources=[dict(filename='arxiv.tex',usage='toplevel')]),indent=2)+'\n').encode()
    with tempfile.TemporaryDirectory(prefix='heterospec-arxiv-') as t:
        fresh=Path(t)
        for name,data in payload.items():p=fresh/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        cmd=['pdflatex','-interaction=nonstopmode','-halt-on-error','-file-line-error','arxiv.tex']
        run(cmd,fresh);run(['bibtex','arxiv'],fresh)
        for _ in range(3):run(cmd,fresh)
        payload['arxiv.bbl']=(fresh/'arxiv.bbl').read_bytes()
        package=OUT/'arxiv-source-v0.15.3.zip'
        with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for name,data in sorted(payload.items()):
                info=zipfile.ZipInfo(name,date_time=(2026,10,13,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16;z.writestr(info,data)
        # Fresh extraction validates the actual deliverable with included BBL.
        extracted=fresh/'extracted';extracted.mkdir()
        with zipfile.ZipFile(package) as z:z.extractall(extracted)
        for _ in range(3):run(cmd,extracted)
        log=(extracted/'arxiv.log').read_text(errors='replace')
        bad=re.findall(r'Overfull.*|.*undefined.*|.*multiply defined.*|.*Float too large.*|.*Missing character.*|.*destination with the same identifier.*|.*duplicate ignored.*',log,re.I)
        assert not bad,bad
        pdf=OUT/'arxiv-combined-v0.15.3.pdf';shutil.copyfile(extracted/'arxiv.pdf',pdf)
        (OUT/'arxiv-combined.log').write_text(log)
        text=run(['pdftotext','-layout',str(pdf),'-'],extracted)
        pages=text.split('\f');pages=[p for p in pages if p.strip()]
        for i,p in enumerate(pages,1):assert p.strip().endswith(str(i)),('page numbering',i)
        start=[i for i,p in enumerate(pages,1) if re.search(r'^\s*Supplementary Material\s*$',p,re.M)]
        assert len(start)==1
        fonts=run(['pdffonts',str(pdf)],extracted);assert 'Type 3' not in fonts
        assert all(re.search(r'\s+yes\s+(?:yes|no)\s+(?:yes|no)\s+',line) for line in fonts.splitlines()[2:])
        qa=dict(status='PASS_LOCAL_CLEAN_ZIP_COMPILATION',date='2026-10-13',entry='arxiv.tex',zip_files=len(payload),zip_sha256=sha(package.read_bytes()),pdf_sha256=sha(pdf.read_bytes()),pages=len(pages),supplement_starts=start[0],continuous_page_numbers=True,all_fonts_embedded=True,type3_fonts=0,unresolved_references=0,overfull_boxes=0,shared_bibliography_entries=len(re.findall(r'\\bibitem\{',payload['arxiv.bbl'].decode())),unchanged_scientific_inputs={n:sha(b) for n,b in payload.items() if n.startswith(('sections/','supplement/','figures/'))},submitted=False,server_compilation_checked=False)
        (OUT/'ARXIV_SOURCE_QA.json').write_text(json.dumps(qa,indent=2)+'\n')
        title=re.search(r'\\title\{([^}]+)\}',main).group(1)
        (OUT/'arxiv-title-v0.15.3.txt').write_text(title+'\n')
        abstract_main=(ROOT/'sections/00_abstract.tex').read_text() if (ROOT/'sections/00_abstract.tex').exists() else re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}',main,re.S).group(1)
        if r'\input{' in abstract_main:
            n=re.search(r'\\input\{([^}]+)\}',abstract_main).group(1);abstract_main=(ROOT/(n+'.tex')).read_text()
        (OUT/'arxiv-abstract-v0.15.3.txt').write_text(abstract_main.strip()+'\n')
        (OUT/'arxiv-comments-v0.15.3.txt').write_text(f'{len(pages)} pages, 7 figures; includes supplementary material. Updated phase-scoped layout evidence, B570 boundary analysis, references and presentation.\n')
        print(json.dumps({k:v for k,v in qa.items() if k!='unchanged_scientific_inputs'},indent=2))
if __name__=='__main__':main()
