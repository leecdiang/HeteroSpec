#!/usr/bin/env python3
"""Screen restored UTF-8 text for specific credential patterns; not a privacy certification."""
from pathlib import Path
import re,json,zipfile,io,hashlib,time
p=Path(__file__).resolve().parents[1]
patterns={
'github_token':rb'\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{70,})\b',
'aws_key':rb'\bAKIA[0-9A-Z]{16}\b',
'private_key':rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
'openai_key':rb'\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{45,}\b',
'hf_token':rb'\bhf_[A-Za-z0-9]{30,}\b'}
patterns={k:re.compile(v) for k,v in patterns.items()};count={'files':0,'utf8_text_files':0,'text_bytes':0,'nested_archives':0};hits=[];seen=set();expected=[]
def scan(name,data,depth=0):
 h=hashlib.sha256(data).hexdigest()
 if h in seen:return
 seen.add(h);count['files']+=1
 if name.lower().endswith('.zip') and data[:4]==b'PK\x03\x04' and depth<6:
  try:
   with zipfile.ZipFile(io.BytesIO(data)) as z:
    count['nested_archives']+=1
    for i in z.infolist():
     if not i.is_dir():scan(name+'!'+i.filename,z.read(i),depth+1)
  except zipfile.BadZipFile:
   if 'CPU_DIAGNOSTIC/corrupt.zip' in name:expected.append(name)
   else:raise
  return
 if b'\x00' in data[:8192]:return
 try:data.decode('utf-8')
 except UnicodeDecodeError:return
 count['utf8_text_files']+=1;count['text_bytes']+=len(data)
 for kind,pat in patterns.items():
  for m in pat.finditer(data):hits.append({'path':name,'pattern':kind,'offset':m.start(),'match_sha256':hashlib.sha256(m.group()).hexdigest()})
for d in sorted((p/'output/raw_restore').iterdir()):
 if not (d/'restored').exists():continue
 for f in sorted((d/'restored').rglob('*')):
  if f.is_file():scan(d.name+'/'+str(f.relative_to(d/'restored')),f.read_bytes())
 print(d.name,count,flush=True)
result={'date':'2026-10-13','scope':'Six restored archives plus recursively readable nested ZIP members; identical content scanned once','patterns':list(patterns),'counts':count,'hits':hits,'expected_corrupt_fixture':expected,'limits':'Pattern scan only; not a complete privacy, legal-rights or credential absence certification. Binary files excluded from text matching.'}
(p/'review_access/RAW_TEXT_SECRET_SCAN.json').write_text(json.dumps(result,indent=2)+'\n');print('hits',len(hits),flush=True)
