#!/usr/bin/env python3
"""Current PDF/log/font/bibliography/anonymity gates with explicit manual-QA status."""
import argparse,hashlib,json,re,zipfile
from pathlib import Path
from pypdf import PdfReader
HERE=Path(__file__).resolve().parents[1];E=HERE.parent/'evidence'
FORBIDDEN=['leecdiang','/Users/','/home/','D:\\','C:\\','file://','github.com/leecdiang']
def scan(s):
 assert not any(x.casefold() in s.casefold() for x in FORBIDDEN),'identifying content'
def qa(build):
 report={'status':'RERUN_PASS','pdfs':{},'manual_visual_review':'PENDING — automated QA does not constitute page-by-page visual inspection'}
 for n,out in [('main','manuscript'),('appendix','appendix'),('hardware-only','hardware-only')]:
  p=build/(n+'.pdf' if n!='hardware-only' else 'hardware-only/hardware-only.pdf');r=PdfReader(p);texts=[x.extract_text() or '' for x in r.pages];text='\n'.join(texts);metadata=dict(r.metadata);scan(text+'\n'+str(metadata));assert 'Anonymous' in metadata.get('/Author','') and 'v0.8.5' in metadata.get('/Subject','');assert '??' not in text and not re.search(r'RTX 5070 Ti(?!\s+Laptop)',text)
  assert 'AUTHORERR' not in text,'unresolved author affiliation';assert p.read_bytes()==(HERE/'output'/(out+'-v0.8.5.pdf')).read_bytes();assert not r.trailer['/Root'].get('/Names',{}).get('/EmbeddedFiles');annotations=[]
  for page in r.pages:
   for a in page.get('/Annots',[]):
    a=a.get_object();action=a.get('/A',{});scan(str(action));annotations.append(str(action.get('/URI','')))
  fonts={};seen=set()
  def resources(rr):
   rr=rr.get_object()
   for f in rr.get('/Font',{}).values():
    f=f.get_object();sub=str(f.get('/Subtype'));name=str(f.get('/BaseFont'));assert sub in ('/Type1','/TrueType','/Type0'),(name,sub)
    for physical in ([x.get_object() for x in f['/DescendantFonts']] if sub=='/Type0' else [f]):
     desc=physical.get('/FontDescriptor');assert desc and any(k in desc.get_object() for k in ('/FontFile','/FontFile2','/FontFile3')),(name,'not embedded')
    fonts[name]=sub
   for x in rr.get('/XObject',{}).values():
    key=(getattr(x,'idnum',None),getattr(x,'generation',None))
    if key in seen:continue
    seen.add(key);x=x.get_object()
    if x.get('/Subtype')=='/Form' and '/Resources' in x:resources(x['/Resources'])
  for page in r.pages:resources(page['/Resources'])
  assert any('NimbusRomNo9L' in n for n in fonts),'official Times font missing';log=p.with_suffix('.log').read_text();errors=re.findall(r'Overfull[^\n]*|LaTeX Error[^\n]*|Citation[^\n]*undefined|Reference[^\n]*undefined|undefined references|Font shape[^\n]*undefined|Font[^\n]*substitut|Some font shapes were not available|Missing character[^\n]*',log);assert not errors,(n,errors)
  aux=p.with_suffix('.aux').read_text();body=None
  if n!='appendix':body=int(re.search(r'\\newlabel\{maintextend\}\{\{[^}]*\}\{(\d+)\}',aux).group(1));assert body<=10,(n,'body exceeds ten pages',body)
  report['pdfs'][n]={'pages':len(r.pages),'body_pages':body,'references_pages':len(r.pages)-body if body else 0,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'metadata':metadata,'fonts':fonts,'anonymous_text_metadata_actions':'PASS','attachments':0,'overfull_boxes':0,'undefined_references_citations':0,'underfull_warnings':re.findall(r'Underfull[^\n]*',log),'labels':{k:{'number':v,'page':int(p)} for k,v,p in re.findall(r'\\newlabel\{((?:fig|tab|sec):[^}]+)\}\{\{([^}]+)\}\{(\d+)\}',aux)}}
  if n=='hardware-only':assert 'sec:runtime' not in aux and 'Internal section-removal and reference proof only' in text
 bib=(HERE/'references.bib').read_text();keys=re.findall(r'@\w+\{([^,]+),',bib);assert len(keys)==len(set(keys));authors=[]
 for m in re.finditer(r'author\s*=\s*\{',bib):
  i=m.end();start=i;depth=1
  while depth:depth+=(bib[i]=='{')-(bib[i]=='}');i+=1
  authors.append(bib[start:i-1])
 assert len(authors)==len(keys) and all(not re.search(r'\bothers\b|et al',a) for a in authors)
 bbl=(build/'main.bbl').read_text();cited=re.findall(r'\\bibitem(?:\[[\s\S]*?\])?\{([^}]+)\}',bbl);assert set(cited)==set(keys),(len(cited),len(keys))
 for block in re.split(r'\\bibitem',bbl)[1:]:
  authorbody=block.split('}\n',1)[1].split('\\newblock',1)[0];assert 'et~al' not in authorbody and 'et al' not in authorbody
 report['bibliography']={'entries':len(keys),'resolved_cited_entries':len(cited),'complete_author_lists':True}
 with zipfile.ZipFile(HERE/'output/overleaf-evidence-integration-v0.8.5.zip') as z:
  for n in z.namelist():
   scan(n)
   if n.endswith(('.tex','.bib','.sty','.bst','.txt','.json')):scan(z.read(n).decode(errors='replace'))
 report['source_zip_anonymity']='PASS'
 visual=E/'VISUAL_QA_V085.json'
 if visual.exists():
  v=json.loads(visual.read_text())
  if v.get('status')=='RERUN_PASS' and all(v['pdf_sha256'].get(n)==x['sha256'] for n,x in report['pdfs'].items()):
   report['manual_visual_review']='RERUN_PASS — separate recorded primary-agent visual review; not inferred from automated scans'
   report['manual_visual_receipt_sha256']=hashlib.sha256(visual.read_bytes()).hexdigest()
 (E/'PDF_AND_ANONYMITY_V085_QA.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({n:{k:v for k,v in r.items() if k in ('pages','body_pages','references_pages')} for n,r in report['pdfs'].items()}));return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--build',type=Path);a=p.parse_args();b=a.build or Path(json.loads((E/'CLEAN_ZIP_REBUILD_V085_QA.json').read_text())['fresh_directory']);qa(b)
