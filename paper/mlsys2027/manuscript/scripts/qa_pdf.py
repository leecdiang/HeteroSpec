#!/usr/bin/env python3
"""Check final anonymous PDFs, page boundary, bibliography and TeX diagnostics."""
from pathlib import Path
import re,json,hashlib
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]; E=ROOT.parent/'evidence'
report={'status':'PASS','pdfs':{},'manual_visual_review':'Recorded separately in MANUSCRIPT_STATUS.md; rerender after final edits.'}
for fn in ['main','appendix']:
 p=ROOT/'build'/f'{fn}.pdf';r=PdfReader(p);text='\n'.join(page.extract_text() or '' for page in r.pages);metadata=dict(r.metadata)
 combined=text+'\n'+str(metadata)
 for forbidden in ['leecdiang','/Users/','D:\\','C:\\','HeteroSpec','AUTHORERR','/home/','Acknowledgments','Acknowledgements']:
  assert forbidden.casefold() not in combined.casefold(),(fn,forbidden)
 assert 'Anonymous' in metadata.get('/Author',''),metadata
 assert 'v0.3' in metadata.get('/Subject',''),metadata
 output=ROOT/'output'/('manuscript-v0.3.pdf' if fn=='main' else 'appendix-v0.3.pdf')
 assert output.read_bytes()==p.read_bytes(),(fn,'delivered PDF differs from checked build')
 assert not re.search(r'RTX 5070 Ti(?!\s+Laptop)', text), 'Missing Laptop identity'
 assert '??' not in text
 # PDF actions/links must not point to identifying local or artifact paths.
 for page in r.pages:
  for a in page.get('/Annots',[]):
   action=a.get_object().get('/A',{});uri=str(action.get('/URI',''))
   assert not re.search(r'leecdiang|/Users/|HeteroSpec|file:',uri,re.I),uri
 fonts={}
 seen=set()
 def scan_resources(resources):
  resources=resources.get_object()
  for f in resources.get('/Font',{}).values():
   f=f.get_object();sub=str(f.get('/Subtype'));name=str(f.get('/BaseFont'))
   assert sub in ('/Type1','/TrueType','/Type0'),(name,sub)
   physical=[v.get_object() for v in f['/DescendantFonts']] if sub=='/Type0' else [f]
   for font in physical:
    desc=font.get('/FontDescriptor')
    assert desc is not None and any(k in desc.get_object() for k in ('/FontFile','/FontFile2','/FontFile3')),(name,'font not embedded')
   fonts[name]=sub
  for obj in resources.get('/XObject',{}).values():
   key=(getattr(obj,'idnum',None),getattr(obj,'generation',None))
   if key in seen:continue
   seen.add(key);obj=obj.get_object()
   if obj.get('/Subtype')=='/Form' and '/Resources' in obj:scan_resources(obj['/Resources'])
 for page in r.pages:scan_resources(page['/Resources'])
 log=(ROOT/'build'/f'{fn}.log').read_text()
 assert not re.search(r'Overfull|undefined references|Citation .* undefined|LaTeX Error|AUTHORERR',log),fn
 report['pdfs'][fn]={'pages':len(r.pages),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'metadata':metadata,'fonts':fonts,'anonymous_scan':'PASS','overfull_boxes':0,'undefined_references':0}
aux=(ROOT/'build/main.aux').read_text();mainpage=int(re.search(r'\\newlabel\{maintextend\}\{\{[^}]*\}\{(\d+)\}',aux).group(1));assert mainpage<=10
report['main_text_pages']=mainpage
report['references_pages']=report['pdfs']['main']['pages']-mainpage
report['section_start_pages']={k:int(v) for k,v in re.findall(r'\\newlabel\{(sec:[^}]+)\}\{\{[^}]*\}\{(\d+)\}',aux)}
figures={k:{'number':n,'page':int(p)} for k,n,p in re.findall(r'\\newlabel\{(fig:[^}]+)\}\{\{([^}]+)\}\{(\d+)\}',aux)}
assert set(figures)=={'fig:translation','fig:m4','fig:verification','fig:state'},figures
assert {k:v['number'] for k,v in figures.items()}=={'fig:m4':'1','fig:translation':'2','fig:verification':'3','fig:state':'4'}
assert all(label not in aux for label in ('fig:framework','fig:overview','fig:regimes','tab:mechanism'))
appendix_aux=(ROOT/'build/appendix.aux').read_text()
assert 'fig:regimes' not in appendix_aux
assert r'\newlabel{tab:verificationlookup}{{A3}' in appendix_aux
assert r'\newlabel{tab:regimes}{{A4}' in appendix_aux
report['main_figures']=figures
report['appendix_tables']={k:{'number':n,'page':int(p)} for k,n,p in re.findall(r'\\newlabel\{(tab:[^}]+)\}\{\{([^}]+)\}\{(\d+)\}',appendix_aux)}
# All 13 cited entries have complete authors, including 58 HumanEval authors.
bib=(ROOT/'references.bib').read_text();authors=re.findall(r'author=\{([^}]+)\}',bib);assert len(authors)==13;assert all('others' not in a and 'et al' not in a for a in authors)
assert len(authors[-2].split(' and '))==58
bbl=(ROOT/'build/main.bbl').read_text()
for block in re.split(r'\\bibitem',bbl)[1:]:
 authorbody=block.split('}\n',1)[1].split('\\newblock',1)[0]
 assert 'et~al' not in authorbody and 'et al' not in authorbody,authorbody
report['references']={'entries':13,'full_author_lists':True,'HumanEval_author_count':58}
# Inventory every requested overclaim search hit for manual disposition.
paths=[ROOT/'main.tex',ROOT/'appendix.tex']+list((ROOT/'sections').glob('*.tex'))+list((ROOT/'figures').glob('*.tex'))+list((ROOT/'tables').glob('*.tex'))
hits=[]
for p in paths:
 for n,line in enumerate(p.read_text().splitlines(),1):
  if re.search(r'\bfirst\b|\buniversally\b|\bproves\b|CUDA is broken|NPU is too slow|unified memory causes|all speculative decoding',line,re.I):hits.append({'path':str(p.relative_to(ROOT)),'line':n,'text':line})
report['overclaim_search_hits']=hits
hp=ROOT/'build/hardware-only/hardware-only.pdf'
if hp.exists():
 haux=hp.with_suffix('.aux').read_text();htext='\n'.join(p.extract_text() for p in PdfReader(hp).pages)
 assert 'Requirements traced to closed measurements' not in htext and 'implementation and measured results pending' not in htext
 assert 'sec:runtime' not in haux and '??' not in htext
 report['hardware_only']={'total_pages':len(PdfReader(hp).pages),'main_pages':int(re.search(r'\\newlabel\{maintextend\}\{\{[^}]*\}\{(\d+)\}',haux).group(1)),'runtime_section_removed':True,'no_undefined_references':True,'sha256':hashlib.sha256(hp.read_bytes()).hexdigest()}
(E/'PDF_QA.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':'PASS','main_pages':mainpage,'references_pages':report['references_pages'],'appendix_pages':report['pdfs']['appendix']['pages'],'hardware_only':report.get('hardware_only'),'overclaim_hits':hits},indent=2))
