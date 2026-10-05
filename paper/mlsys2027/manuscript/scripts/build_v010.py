#!/usr/bin/env python3
"""Clean document build and independent source-ZIP rebuild; no model execution."""
import hashlib,json,re,shutil,subprocess,tempfile,zipfile,sys
from pathlib import Path
from pypdf import PdfReader
from package_overleaf_v010 import package
HERE=Path(__file__).resolve().parents[1];OUT=HERE/'output';REV=HERE.parent/'reviews/reconstruction_v010'
def build():
 OUT.mkdir(exist_ok=True)
 zpath=OUT/'overleaf-intervention-reconstruction-v0.10.0.zip';m=package(zpath)
 qa=HERE.parents[2]/'tmp/qa-v010';qa.mkdir(parents=True,exist_ok=True)
 runroot=Path(tempfile.mkdtemp(prefix='clean-',dir=qa));comparisons={};logs={}
 for variant in ('fresh','zip-rebuild'):
  d=runroot/variant;d.mkdir()
  with zipfile.ZipFile(zpath) as z:z.extractall(d)
  hashes=json.loads((d/'SHA256SUMS.json').read_text())
  assert set(hashes)|{'SHA256SUMS.json'}=={p.relative_to(d).as_posix() for p in d.rglob('*') if p.is_file()}
  for n,h in hashes.items():assert hashlib.sha256((d/n).read_bytes()).hexdigest()==h,n
  for name in ('main','appendix'):
   with (d/(name+'-build.console')).open('wb') as f:subprocess.run(['latexmk','-pdf','-interaction=nonstopmode','-halt-on-error',name+'.tex'],cwd=d,stdout=f,stderr=subprocess.STDOUT,check=True)
   for _ in range(2):
    with (d/(name+'-build.console')).open('ab') as f:subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error',name+'.tex'],cwd=d,stdout=f,stderr=subprocess.STDOUT,check=True)
   reader=PdfReader(d/(name+'.pdf'));assert b'%%EOF' in (d/(name+'.pdf')).read_bytes()[-1024:]
   texts=[p.extract_text() for p in reader.pages]
   if variant=='fresh':comparisons[name]={'pages':len(texts),'text_sha256':hashlib.sha256('\n'.join(texts).encode()).hexdigest()}
   else:assert comparisons[name]['text_sha256']==hashlib.sha256('\n'.join(texts).encode()).hexdigest(),name
   log=(d/(name+'.log')).read_text(errors='replace')
   assert not re.search(r'(Undefined control sequence|LaTeX Error|There were undefined references|Citation.*undefined|Reference.*undefined)',log),name
   logs[variant+'/'+name]={'undefined':False,'overfull':re.findall(r'Overfull \\hbox[^\n]*',log),'underfull':len(re.findall('Underfull',log))}
 for name,dest in [('main','manuscript-v0.10.0.pdf'),('appendix','appendix-v0.10.0.pdf')]:shutil.copy2(runroot/'fresh'/(name+'.pdf'),OUT/dest)
 aux=(runroot/'fresh/main.aux').read_text();body_page=int(re.search(r'\\newlabel\{maintextend\}\{\{[^}]*\}\{(\d+)\}',aux).group(1));assert body_page<=10,body_page
 report={'status':'CLEAN_BUILD_PASS','body_pages':body_page,'version':'v0.10.0','build_root':str(runroot),'comparisons':comparisons,'logs':logs,'package':m,'commands':['python scripts/build_v010.py','latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex','latexmk -pdf -interaction=nonstopmode -halt-on-error appendix.tex'],'scope':'Document compilation only; no model forward'}
 (REV/'BUILD_QA.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'root':str(runroot),'comparison':comparisons,'logs':logs}))
if __name__=='__main__':build()
