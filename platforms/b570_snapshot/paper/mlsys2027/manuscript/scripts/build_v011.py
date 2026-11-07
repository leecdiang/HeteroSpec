#!/usr/bin/env python3
"""Build the integrated paper twice from a deterministic portable source ZIP.
Document-only operation; Python 3, latexmk/TeX Live, and pypdf are required.
"""
import hashlib, json, re, shutil, subprocess, tempfile, zipfile
from pathlib import Path
from pypdf import PdfReader

HERE = Path(__file__).resolve().parents[1]
OUT = HERE / 'output'
PATTERN = r'\\(?:input|include|includegraphics)(?:\[[^\]]*\])?\{([^}]+)\}'

def digest(data): return hashlib.sha256(data).hexdigest()

def bundle():
    files = {}
    def collect(name):
        if name in files: return
        assert not Path(name).is_absolute() and '..' not in Path(name).parts, name
        data = (HERE/name).read_bytes()
        if name.endswith('.tex'):
            data = re.sub(r'(?<!\\)%[^\n]*', '', data.decode()).encode()
        files[name] = data
        if name.endswith('.tex'):
            text = data.decode()
            for child in re.findall(PATTERN, text):
                collect(child if Path(child).suffix else child+'.tex')
    for name in ('main.tex','appendix.tex','references.bib'): collect(name)
    for name in ('mlsys2025.sty','mlsys2025.bst','algorithm.sty','algorithmic.sty','fancyhdr.sty'):
        path = HERE/name
        if not path.exists(): path = HERE/'vendor/official/mlsys2025style'/name
        files[name] = path.read_bytes()
    for name in ('build_v011.py','figure_v011.py'): files['scripts/'+name] = (HERE/'scripts'/name).read_bytes()
    files['README.txt'] = b'''INTEGRATED EMPIRICAL MANUSCRIPT v0.11.0
Build: latexmk -pdf main.tex; latexmk -pdf appendix.tex
Full clean packaging/QA: python scripts/build_v011.py (requires pypdf).
Optional chart regeneration: python scripts/figure_v011.py (requires matplotlib).
The included chart is generated already; the document needs no model or network.
All document dependencies are included; TeX comments are stripped for anonymity.
SHA256SUMS.json binds this source package.
Separate anonymous-integrated-evidence-v0.11.0.zip: python -B verify_v011.py.
That package validates retained exports and historical arithmetic, not execution
of omitted models/binaries or absolute experiment chronology. The author review,
raw provenance and venue assessment are separate from anonymous material.
'''
    files['SHA256SUMS.json'] = (json.dumps({n:digest(d) for n,d in sorted(files.items())},indent=2)+'\n').encode()
    OUT.mkdir(exist_ok=True)
    path = OUT/'overleaf-integrated-empirical-v0.11.0.zip'
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for n,d in sorted(files.items()):
            i=zipfile.ZipInfo(n,(2026,10,5,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;z.writestr(i,d)
    return path

def main():
    package=bundle(); reports=[]; texts={}
    with tempfile.TemporaryDirectory(prefix='integrated-paper-') as tmp:
        for run in (1,2):
            root=Path(tmp)/str(run);root.mkdir()
            with zipfile.ZipFile(package) as z: z.extractall(root)
            manifest=json.loads((root/'SHA256SUMS.json').read_text())
            for n,h in manifest.items(): assert digest((root/n).read_bytes())==h,n
            for name in ('main','appendix'):
                result=subprocess.run(['latexmk','-pdf','-interaction=nonstopmode','-halt-on-error',name+'.tex'],cwd=root,capture_output=True,text=True)
                (OUT/f'{name}-build-{run}.log').write_text(result.stdout+result.stderr)
                if result.returncode: raise RuntimeError(f'{name} build {run} failed; see output log')
                log=(root/(name+'.log')).read_text(errors='replace')
                assert not re.search(r'Undefined control sequence|LaTeX Error|(?:Citation|Reference).*undefined|There were undefined references|Overfull \\[hv]box',log),name
                reader=PdfReader(root/(name+'.pdf'))
                page_text=[p.extract_text() for p in reader.pages]
                if run==1:
                    texts[name]=page_text
                    shutil.copyfile(root/(name+'.pdf'),OUT/f'{"manuscript" if name=="main" else name}-v0.11.0.pdf')
                else: assert page_text==texts[name],name
                body=int(re.search(r'\\newlabel\{maintextend\}\{\{[^}]*\}\{(\d+)\}',(root/'main.aux').read_text()).group(1))
                assert body<=10,body
                reports.append(dict(run=run,document=name,pages=len(page_text),body_pages=body if name=='main' else None,text_sha256=digest('\n'.join(page_text).encode()),overfull=0,undefined=0,underfull=len(re.findall('Underfull',log))))
    report=dict(status='PASS',scope='Two clean document builds; no model inference',package_sha256=digest(package.read_bytes()),page_text_identical=True,builds=reports)
    (OUT/'BUILD_QA_V011.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
