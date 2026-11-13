#!/usr/bin/env python3
"""Check requested manuscript constraints and compiled document identities."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import fitz

ROOT=Path(__file__).resolve().parents[1]
checks=[]
def check(name,ok,detail=None):
    checks.append({'name':name,'pass':bool(ok),'detail':detail})
    if not ok:raise AssertionError(name+': '+str(detail))

main=(ROOT/'main.tex').read_text()
abstract=re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}',main,re.S).group(1).strip()
check('abstract synchronized',abstract==(ROOT/'abstract.tex').read_text().strip())
count=len(abstract.split())
check('abstract <= 250 whitespace words',count<=250,count)
keywords=re.search(r'\\begin\{keywords\}(.*?)\\end\{keywords\}',main,re.S).group(1).split(r'\sep')
check('1 to 7 keywords',1<=len(keywords)<=7,len(keywords))
highlights=(ROOT/'highlights.txt').read_text().splitlines()
check('3 to 5 highlights',3<=len(highlights)<=5,len(highlights))
check('highlights <= 85 characters each',all(0<len(x)<=85 for x in highlights),[len(x) for x in highlights])
for stem in ['main','supplement','highlights']:
    file=ROOT/(stem+'.pdf')
    doc=fitz.open(file)
    check(stem+' has pages',len(doc)>0,len(doc))
    if stem=='main':check('main <= 16 pages',len(doc)<=16,len(doc))
    log=(ROOT/'build'/(stem+'.log')).read_text(errors='replace')
    unresolved=[l for l in log.splitlines() if 'undefined' in l.lower() and ('reference' in l.lower() or 'citation' in l.lower())]
    check(stem+' resolved citations/references',not unresolved,unresolved)
    fontout=subprocess.check_output(['pdffonts',str(file)],text=True)
    lines=fontout.splitlines()[2:]
    unembedded=[x for x in lines if re.search(r'\sno\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+$',x)]
    check(stem+' fonts embedded',not unembedded,unembedded)
    check(stem+' no Type 3 fonts',not any('Type 3' in x for x in lines))
    if stem in ['main','supplement']:
        aux=(ROOT/'build'/(stem+'.aux')).read_text()
        cites=[]
        for group in re.findall(r'\\citation\{([^}]+)\}',aux):
            for key in group.split(','):
                if key not in cites:cites.append(key)
        bbl=(ROOT/'build'/(stem+'.bbl')).read_text()
        keys=re.findall(r'\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}',bbl)
        check(stem+' bibliography in first-citation order',cites==keys,{'cited':cites,'listed':keys})
    checks.append({'name':stem+' PDF identity','pass':True,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),
                   'pages':len(doc),'text_sha256':hashlib.sha256('\n'.join(page.get_text() for page in doc).encode()).hexdigest()})
scientific='\n'.join(p.read_text() for p in (ROOT/'sections').glob('*.tex'))
check('no prohibited evidence-package narrative in scientific text',not re.search(r'\bPR\s*#?\s*221\b|#221\b|data package|searching for|missing package',scientific,re.I))
result={'status':'PASS','checks':checks,'model_calls':0,'gpu_contexts':0}
(ROOT/'generated/manuscript_checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':'PASS','checks':len(checks),'abstract_words':count,'highlights_lengths':[len(x) for x in highlights]}))
