#!/usr/bin/env python3
"""Check final anonymous PDFs, page boundary, bibliography and TeX diagnostics."""
from pathlib import Path
import re,json,hashlib
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]; E=ROOT.parent/'evidence'
import os
BUILD=Path(os.environ['HETEROSPEC_V081_BUILD'])
report={'status':'PASS','pdfs':{},'manual_visual_review':'Recorded separately in MANUSCRIPT_STATUS.md; rerender after final edits.'}
for fn in ['main','appendix','hardware-only']:
 p=BUILD/('hardware-only/hardware-only.pdf' if fn=='hardware-only' else f'{fn}.pdf');r=PdfReader(p);text='\n'.join(page.extract_text() or '' for page in r.pages);metadata=dict(r.metadata)
 combined=text+'\n'+str(metadata)
 for forbidden in ['leecdiang','/Users/','D:\\','C:\\','AUTHORERR','/home/','Acknowledgments','Acknowledgements']:
  assert forbidden.casefold() not in combined.casefold(),(fn,forbidden)
 assert 'Anonymous' in metadata.get('/Author',''),metadata
 assert 'v0.8.1' in metadata.get('/Subject',''),metadata
 output=ROOT/'output'/('manuscript-v0.8.1.pdf' if fn=='main' else 'hardware-only-v0.8.1.pdf' if fn=='hardware-only' else 'appendix-v0.8.1.pdf')
 assert output.read_bytes()==p.read_bytes(),(fn,'delivered PDF differs from checked build')
 assert not re.search(r'RTX 5070 Ti(?!\s+Laptop)', text), 'Missing Laptop identity'
 assert '??' not in text
 if fn!='appendix':
  assert 'HeteroSpec' not in re.sub(r'ACL\s+HeteroSpec', '', re.split(r'\bREFERENCES\b',text,flags=re.I)[0]), 'unexpected public system name'
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
 assert any('NimbusRomNo9L' in name for name in fonts), (fn,'official Times fonts absent')
 log=p.with_suffix('.log').read_text()
 assert not re.search(r'Overfull|undefined references|Citation .* undefined|LaTeX Error|AUTHORERR|Font shape .* undefined|Font .*substitut|Some font shapes were not available',log),fn
 report['pdfs'][fn]={'pages':len(r.pages),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'metadata':metadata,'fonts':fonts,'anonymous_scan':'PASS','overfull_boxes':0,'undefined_references':0}
aux=(BUILD/'main.aux').read_text();mainpage=int(re.search(r'\\newlabel\{maintextend\}\{\{[^}]*\}\{(\d+)\}',aux).group(1));assert mainpage<=10
report['main_text_pages']=mainpage
report['references_pages']=report['pdfs']['main']['pages']-mainpage
report['section_start_pages']={k:int(v) for k,v in re.findall(r'\\newlabel\{(sec:[^}]+)\}\{\{[^}]*\}\{(\d+)\}',aux)}
figures={k:{'number':n,'page':int(p)} for k,n,p in re.findall(r'\\newlabel\{(fig:[^}]+)\}\{\{([^}]+)\}\{(\d+)\}',aux)}
assert set(figures)=={'fig:translation','fig:m4','fig:verification','fig:state'},figures
assert {k:v['number'] for k,v in figures.items()}=={'fig:m4':'1','fig:translation':'2','fig:verification':'3','fig:state':'4'}
assert all(label not in aux for label in ('fig:framework','fig:overview','fig:regimes','tab:mechanism'))
appendix_aux=(BUILD/'appendix.aux').read_text()
assert 'fig:regimes' not in appendix_aux
assert r'\newlabel{tab:verificationlookup}{{A3}' in appendix_aux
assert r'\newlabel{tab:regimes}{{A4}' in appendix_aux
assert figures['fig:verification']['page']<=report['section_start_pages']['sec:runtime'], 'Figure 3 drifted into runtime discussion'
report['main_figures']=figures
report['appendix_tables']={k:{'number':n,'page':int(p)} for k,n,p in re.findall(r'\\newlabel\{(tab:[^}]+)\}\{\{([^}]+)\}\{(\d+)\}',appendix_aux)}
# All 19 cited entries have complete authors, including 58 HumanEval authors.
bib=(ROOT/'references.bib').read_text();authors=[]
for match in re.finditer(r'author\s*=\s*\{',bib):
 start=match.end(); depth=1; end=start
 while depth:
  depth+=(bib[end]=='{')-(bib[end]=='}'); end+=1
 authors.append(bib[start:end-1])
keys=re.findall(r'@\w+\{([^,]+),',bib)
assert len(keys)==len(set(keys))==19
assert [len(a.split(' and ')) for a in authors[-4:]]==[1,5,5,5]
assert len(authors)==19;assert all('others' not in a and 'et al' not in a for a in authors)
assert len(authors[11].split(' and '))==58
bbl=(BUILD/'main.bbl').read_text()
for block in re.split(r'\\bibitem',bbl)[1:]:
 authorbody=block.split('}\n',1)[1].split('\\newblock',1)[0]
 assert 'et~al' not in authorbody and 'et al' not in authorbody,authorbody
report['references']={'entries':19,'full_author_lists':True,'HumanEval_author_count':58}
# Inventory every requested overclaim search hit for manual disposition.
paths=[ROOT/'main.tex',ROOT/'appendix.tex']+list((ROOT/'sections').glob('*.tex'))+list((ROOT/'figures').glob('*.tex'))+list((ROOT/'tables').glob('*.tex'))
hits=[]
for p in paths:
 for n,line in enumerate(p.read_text().splitlines(),1):
  if re.search(r'\bfirst\b|\buniversally\b|\bproves\b|CUDA is broken|NPU is too slow|unified memory causes|all speculative decoding',line,re.I):hits.append({'path':str(p.relative_to(ROOT)),'line':n,'text':line})
report['overclaim_search_hits']=hits
hp=BUILD/'hardware-only/hardware-only.pdf'
if hp.exists():
 haux=hp.with_suffix('.aux').read_text();htext='\n'.join(p.extract_text() for p in PdfReader(hp).pages)
 assert 'Requirements traced to closed measurements' not in htext and 'implementation and measured results pending' not in htext
 assert 'sec:runtime' not in haux and '??' not in htext
 report['hardware_only']={'total_pages':len(PdfReader(hp).pages),'main_pages':int(re.search(r'\\newlabel\{maintextend\}\{\{[^}]*\}\{(\d+)\}',haux).group(1)),'runtime_section_removed':True,'no_undefined_references':True,'sha256':hashlib.sha256(hp.read_bytes()).hexdigest()}
(E/'NARRATIVE_PDF_V081_QA.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'status':'PASS','main_pages':mainpage,'references_pages':report['references_pages'],'appendix_pages':report['pdfs']['appendix']['pages'],'hardware_only_pages':report['hardware_only']['total_pages'],'bibliography_entries':19}))
