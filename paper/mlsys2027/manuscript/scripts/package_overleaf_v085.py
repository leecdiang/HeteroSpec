#!/usr/bin/env python3
"""Collect current TeX dependencies into a portable, anonymous source bundle."""
import argparse,hashlib,json,re,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]
PATTERN=r'\\(?:input|include|includegraphics)(?:\[[^\]]*\])?\{([^}]+)\}'
def collect_bundle():
 files={};sources={}
 def collect(source,destination):
  source=source.resolve();content=source.read_bytes();sources[str(source.relative_to(HERE.parent.parent.parent))]=hashlib.sha256(content).hexdigest()
  if destination in files:return
  if source.suffix=='.tex':
   text=content.decode();text=re.sub(r'(?<!\\)%[^\n]*','',text)
   for match in list(re.finditer(PATTERN,text)):
    path=match.group(1);dependency=HERE/path
    if not dependency.suffix:dependency=dependency.with_suffix('.tex')
    target='publication/'+str(Path(path).relative_to('../figures')) if path.startswith('../figures/') else path
    if not Path(target).suffix:target+='.tex'
    assert not Path(target).is_absolute() and '..' not in Path(target).parts
    text=text.replace('{'+path+'}','{'+target+'}');collect(dependency,target)
   content=text.encode()
  files[destination]=content
 for name in ('main.tex','appendix.tex'):collect(HERE/name,name)
 files['references.bib']=(HERE/'references.bib').read_bytes();sources['paper/mlsys2027/manuscript/references.bib']=hashlib.sha256(files['references.bib']).hexdigest()
 for p in sorted((HERE/'vendor/official/mlsys2025style').iterdir()):
  if p.suffix in ('.sty','.bst'):
   files[p.name]=p.read_bytes();sources[str(p.relative_to(HERE.parent.parent.parent))]=hashlib.sha256(files[p.name]).hexdigest()
 files['README.txt']=b'''EVIDENCE-INTEGRATION DRAFT -- v0.8.5
Build from the ZIP root with pdfLaTeX: latexmk -pdf main.tex
Separate appendix: latexmk -pdf appendix.tex
This self-contained source ZIP supports editing and PDF reconstruction.
The anonymous evidence index is a separate reviewer-facing artifact.
The internal hardware-only build is a section-removal/reference proof only.
No model, measurement hardware, network or external repository is needed.
Prediction equality, reference qualification, sampled immediate effects and
continuation effects retain distinct study identities. New serialized RTX
latency is qualified for its instrumented boundary and is slower than target.
Anonymous derived evidence cannot authenticate original remote freeze times
or omitted weights/runtime/compiler/driver bytes. No functional pass@k claim.
This is an integration draft awaiting a separate author-initiated review.
'''
 return files,sources
def verify_dependencies(files):
 for name,data in files.items():
  if not name.endswith('.tex'):continue
  for path in re.findall(PATTERN,data.decode()):
   if not Path(path).suffix:path+='.tex'
   if path not in files:raise ValueError('missing dependency '+name+': '+path)
def package(output):
 files,sources=collect_bundle();verify_dependencies(files)
 manifest={n:hashlib.sha256(d).hexdigest() for n,d in sorted(files.items())};files['SHA256SUMS.json']=(json.dumps(manifest,indent=2)+'\n').encode()
 output.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
  for n,d in sorted(files.items()):
   i=zipfile.ZipInfo(n,(2026,10,1,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;z.writestr(i,d)
 return {'files':len(files),'source_files':sources,'source_tree_digest':hashlib.sha256(json.dumps(sources,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'zip_sha256':hashlib.sha256(output.read_bytes()).hexdigest()}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=HERE/'output/overleaf-evidence-integration-v0.8.5.zip');a=p.parse_args();r=package(a.output);print(json.dumps({k:v for k,v in r.items() if k!='source_files'}))
