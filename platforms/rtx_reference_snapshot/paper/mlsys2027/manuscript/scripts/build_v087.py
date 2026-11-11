#!/usr/bin/env python3
"""Build current PDFs and final source ZIP in two independent fresh directories."""
import argparse,hashlib,json,os,re,shutil,subprocess,sys,tempfile,zipfile
from pathlib import Path
from pypdf import PdfReader
from package_overleaf_v087 import package
HERE=Path(__file__).resolve().parents[1];E=HERE.parent/'evidence';OUT=HERE/'output'
def run(args,root,console,env=None):
 with console.open('ab') as f:subprocess.run(args,cwd=root,stdout=f,stderr=subprocess.STDOUT,env=env,check=True)
def extract(archive,dest):
 dest.mkdir()
 with zipfile.ZipFile(archive) as z:z.extractall(dest)
 m=json.loads((dest/'SHA256SUMS.json').read_text())
 assert {p.relative_to(dest).as_posix() for p in dest.rglob('*') if p.is_file()}==set(m)|{'SHA256SUMS.json'}
 for n,h in m.items():assert hashlib.sha256((dest/n).read_bytes()).hexdigest()==h,n
 return m
def build(qa_root=None):
 OUT.mkdir(exist_ok=True);manifest=package(OUT/'overleaf-rtx-integration-v0.8.7.zip')
 local_qa=HERE.parents[2]/'tmp/qa-v087';local_qa.mkdir(parents=True,exist_ok=True)
 root=qa_root or Path(tempfile.mkdtemp(prefix='build-',dir=local_qa));root.mkdir(parents=True,exist_ok=True)
 fresh=root/'fresh';clean=root/'final-zip-independent';a=extract(OUT/'overleaf-rtx-integration-v0.8.7.zip',fresh);b=extract(OUT/'overleaf-rtx-integration-v0.8.7.zip',clean);assert a==b
 for d in (fresh,clean):
  for name in ('main','appendix'):
   run(['latexmk','-pdf',name+'.tex'],d,d/(name+'-build.console'))
   for _ in range(2):run(['pdflatex','-interaction=nonstopmode','-halt-on-error',name+'.tex'],d,d/(name+'-build.console'))
 for d in (fresh,clean):
  (d/'hardware-only').mkdir();args=['pdflatex','-interaction=nonstopmode','-halt-on-error','-output-directory=hardware-only','-jobname=hardware-only',r'\def\HardwareOnly{1}\input{main.tex}'];console=d/'hardware-build.console';run(args,d,console);env=os.environ.copy();env['BIBINPUTS']=str(d)+':';run(['bibtex','hardware-only/hardware-only'],d,console,env)
  for _ in range(3):run(args,d,console)
 for n,dest in [('main.pdf','manuscript-v0.8.7.pdf'),('appendix.pdf','appendix-v0.8.7.pdf'),('hardware-only/hardware-only.pdf','hardware-only-v0.8.7.pdf')]:shutil.copyfile(fresh/n,OUT/dest)
 comparison={}
 for name in ('main','appendix','hardware-only/hardware-only'):
  aa=PdfReader(fresh/(name+'.pdf'));bb=PdfReader(clean/(name+'.pdf'));at=[p.extract_text() for p in aa.pages];bt=[p.extract_text() for p in bb.pages];assert len(aa.pages)==len(bb.pages) and at==bt,name
  comparison[name]={'pages':len(aa.pages),'raw_extracted_page_text_exact_equal':True,'normalization_applied':False,'all_page_text_equal':True,'text_sha256':hashlib.sha256('\n'.join(at).encode()).hexdigest()}
 versions={}
 for cmd in (['latexmk','-v'],['pdflatex','--version'],['bibtex','--version']):versions[cmd[0]]=subprocess.check_output(cmd,text=True).splitlines()[:2]
 report={'status':'RERUN_PASS','fresh_directory':str(fresh),'clean_zip_directory':str(clean),'manifest_files':len(a),'all_hashes_verified':True,'comparison':comparison,**manifest,'baseline_remote_head':'87b811e21a164468232cfea3c2404a1ebc869477','source_state':'Current dependency hashes above are authoritative; content commit recorded at delivery','environment':{'python':sys.version,'tools':versions},'commands':['latexmk -pdf main.tex','latexmk -pdf appendix.tex','two explicit final pdfLaTeX resolution passes per document','pdflatex/bibtex hardware-only (3 resolution passes)'],'scope':'New directories, no prior PDF or aux reused; document compilation only'}
 (E/'CLEAN_ZIP_REBUILD_V087_QA.json').write_text(json.dumps(report,indent=2)+'\n')
 run([sys.executable,str(HERE/'scripts/qa_pdf_v087.py'),'--build',str(fresh)],HERE,root/'qa.console')
 print(json.dumps({'status':'RERUN_PASS','comparison':comparison,'local_qa':str(root)}));return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--qa-root',type=Path);a=p.parse_args();build(a.qa_root.resolve() if a.qa_root else None)
