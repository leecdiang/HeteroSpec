"""Build author-review PDFs and a clean portable source package, CPU only."""
from pathlib import Path
import argparse, hashlib, json, os, re, shutil, subprocess, sys, zipfile

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output'


def run(args):
    env=os.environ.copy()
    env['SOURCE_DATE_EPOCH']='1791504000'  # 2026-10-09 00:00:00 UTC
    env['FORCE_SOURCE_DATE']='1'
    env['TZ']='UTC'
    return subprocess.run(args,cwd=ROOT,env=env,text=True,capture_output=True,check=True)


def check_text():
    text=(ROOT/'main.tex').read_text()
    abstract=re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}',text,re.S).group(1)
    words=len(re.findall(r"\b[\w]+(?:[-'][\w]+)*\b",abstract))
    assert words<=250,words
    keyword=re.search(r'\\begin\{keyword\}(.*?)\\end\{keyword\}',text,re.S).group(1)
    keywords=[k.strip() for k in keyword.split(r'\sep')]
    assert 1<=len(keywords)<=7
    highlights=(ROOT/'Highlights.txt').read_text().splitlines()
    assert 3<=len(highlights)<=5 and all(0<len(h)<=85 for h in highlights)
    alltex='\n'.join(p.read_text() for p in [ROOT/'main.tex',ROOT/'supplement.tex',ROOT/'declarations.tex']+
                     list((ROOT/'sections').glob('*.tex'))+list((ROOT/'supplement').glob('*.tex')))
    cites={k.strip() for c in re.findall(r'\\cite(?:p|t)?\{([^}]+)\}',alltex) for k in c.split(',')}
    bibkeys=set(re.findall(r'@\w+\{([^,]+),',(ROOT/'references.bib').read_text()))
    assert cites==bibkeys,dict(undefined=cites-bibkeys,unused=bibkeys-cites)
    return dict(abstract_words=words,keywords=len(keywords),highlight_characters=[len(h) for h in highlights],
                bibliography_entries=len(bibkeys),all_entries_cited=True)


def package():
    target=OUT/'overleaf-author-source-v0.14.1.zip'
    sources=[p for p in ROOT.rglob('*') if p.is_file() and
             not any(c in p.relative_to(ROOT).parts for c in ['build','output','__pycache__'])]
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(sources):
            info=zipfile.ZipInfo(str(p.relative_to(ROOT)),date_time=(2026,10,9,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
            z.writestr(info,p.read_bytes())
    return dict(filename=target.name,files=len(sources),bytes=target.stat().st_size,
                sha256=hashlib.sha256(target.read_bytes()).hexdigest())


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--no-package',action='store_true');ap.add_argument('--skip-assets',action='store_true')
    args=ap.parse_args();OUT.mkdir(exist_ok=True)
    if not args.skip_assets:
        run([sys.executable,'scripts/build_ledgers.py'])
        result=run([sys.executable,'scripts/reconstruct.py']);(OUT/'reconstruction-console.log').write_text(result.stdout+result.stderr)
        result=run([sys.executable,'scripts/audit_v0141.py']);(OUT/'scientific-console.log').write_text(result.stdout+result.stderr)
    qa=dict(version='v0.14.1',author_side_validation=True,new_inference=0,editorial_checks=check_text(),documents={})
    for stem,label in [('main','jsa-manuscript-v0.14.1.pdf'),('supplement','jsa-supplement-v0.14.1.pdf')]:
        try:
            result=run(['latexmk','-pdf','-interaction=nonstopmode','-halt-on-error','-file-line-error','-outdir=build',stem+'.tex'])
        except subprocess.CalledProcessError as e:
            (OUT/(stem+'-console.log')).write_text(e.stdout+e.stderr);raise
        (OUT/(stem+'-console.log')).write_text(result.stdout+result.stderr)
        log=(ROOT/'build'/f'{stem}.log').read_text(errors='replace')
        problems=re.findall(r'Overfull.*|.*undefined.*|.*multiply defined.*|.*Float too large.*|.*Missing character.*|.*destination with the same identifier.*|.*duplicate ignored.*',log,re.I)
        assert not problems,(stem,problems)
        pdf=OUT/label;shutil.copyfile(ROOT/'build'/f'{stem}.pdf',pdf)
        run(['pdftotext','-layout',str(pdf),str(OUT/(stem+'.txt'))])
        info=run(['pdfinfo',str(pdf)]).stdout
        fonts=run(['pdffonts',str(pdf)]).stdout;(OUT/(stem+'-fonts.txt')).write_text(fonts)
        assert 'Type 3' not in fonts
        # pdffonts columns after the font type contain emb/sub/uni flags.
        for row in fonts.splitlines()[2:]:
            assert re.search(r'\s+yes\s+(?:yes|no)\s+(?:yes|no)\s+',row),row
        extracted=(OUT/(stem+'.txt')).read_text()
        qa['documents'][stem]=dict(pages=int(re.search(r'Pages:\s+(\d+)',info).group(1)),
                                   overfull=0,undefined_references=0,multiply_defined=0,type3_fonts=0,
                                   all_fonts_embedded=True,sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(),
                                   text_sha256=hashlib.sha256(extracted.encode()).hexdigest())
    if not args.no_package:qa['source_package']=package()
    (OUT/'BUILD_QA.json').write_text(json.dumps(qa,indent=2)+'\n')
    (OUT/'SHA256SUMS.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                                               for p in OUT.iterdir() if p.suffix in ['.pdf','.zip']},indent=2)+'\n')
    print(json.dumps(qa,indent=2))


if __name__=='__main__':main()
