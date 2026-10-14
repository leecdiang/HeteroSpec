#!/usr/bin/env python3
"""Verify draft preview/downloads using secret-link cookies only, never account credentials.
Keep review_links.json and downloaded previews in ignored private output.
Incomplete transfers can be resumed by rerunning; no Zenodo mutation occurs.
"""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin
import json,subprocess,hashlib
p=Path(__file__).resolve().parents[1];d=p/'output/zenodo_private';links=json.loads((d/'review_links.json').read_text())
class Page(HTMLParser):
 def __init__(self):super().__init__();self.record=None;self.downloads={}
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'data-record' in a:self.record=json.loads(a['data-record'])
  u=a.get('href','')
  if tag=='a' and '/files/' in u and 'download=1' in u:self.downloads[u.split('/files/')[1].split('?')[0]]=urljoin('https://zenodo.org',u)
for kind,url in links.items():
 page=d/(kind+'-preview.html');jar=d/(kind+'-cookiejar.txt')
 q=subprocess.run(['curl','-q','-sSL','--max-time','50','-c',str(jar),'-o',str(page),'-w','%{http_code}',url],capture_output=True,text=True)
 if q.returncode or q.stdout!='200':print(kind,'preview not ready',q.stdout,flush=True);continue
 parsed=Page();parsed.feed(page.read_text());r=parsed.record or {}
 summary={k:r.get(k) for k in ['id','is_published','is_draft','status']};summary['available_downloads']=list(parsed.downloads)
 (d/(kind+'-preview-status.json')).write_text(json.dumps(summary,indent=2)+'\n')
 print(kind,summary,flush=True)
 for name,url in parsed.downloads.items():
  assert Path(name).name==name and '..' not in name and url.startswith('https://zenodo.org/'), 'Unexpected download path'
  target=d/name
  local=p/'output'/name
  if not local.exists():local=p/'output/JSA_v0153_raw_archives'/name
  if not local.exists():local=p/'output/zenodo_transfer_parts'/name
  if target.exists() and target.stat().st_size==local.stat().st_size:
   with target.open('rb') as f: got=hashlib.file_digest(f,'sha256').hexdigest()
   with local.open('rb') as f: want=hashlib.file_digest(f,'sha256').hexdigest()
   if got==want:
    print('ANONYMOUS_DOWNLOAD_SHA256_CACHED_PASS',name,got,flush=True);continue
  q=subprocess.run(['curl','-q','-sSL','--fail','--max-time','600','--continue-at','-','-b',str(jar),'-o',str(target),url],capture_output=True,text=True)
  if q.returncode:print(name,'download exit',q.returncode,flush=True);continue
  h=hashlib.sha256(target.read_bytes()).hexdigest();local=p/'output'/name
  if not local.exists():local=p/'output/JSA_v0153_raw_archives'/name
  if not local.exists():local=p/'output/zenodo_transfer_parts'/name
  with local.open('rb') as f:expected=hashlib.file_digest(f,'sha256').hexdigest()
  assert target.stat().st_size==local.stat().st_size and h==expected,name
  print('ANONYMOUS_DOWNLOAD_SHA256_PASS',name,h,flush=True)
