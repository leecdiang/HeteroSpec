#!/usr/bin/env python3
"""Lossless content-addressed JSON archive; no executable/model artifacts."""
import argparse,pathlib,json,hashlib,base64,gzip,io
p=argparse.ArgumentParser();p.add_argument('--matrix',type=pathlib.Path);p.add_argument('--archive',type=pathlib.Path,required=True);p.add_argument('--restore',type=pathlib.Path);a=p.parse_args()
def need(x,m):
 if not x:raise ValueError(m)
if a.restore:
 need(not a.restore.exists(),'fresh restore path required');x=json.loads(a.archive.read_text())
 if x.get('codec')=='gzip+base64':
  compressed=base64.b64decode(x['data'],validate=True)
  with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as f:raw=f.read(64*1024*1024+1)
  need(len(raw)<=64*1024*1024 and len(raw)==x['bytes'] and hashlib.sha256(raw).hexdigest()==x['sha256'],'compressed archive size/digest');x=json.loads(raw)
 need(x['schema']=='native-cpu-replay-matrix-archive-v1','schema');a.restore.mkdir(parents=True)
 for name,h in x['files'].items():
  rel=pathlib.PurePosixPath(name);need(not rel.is_absolute() and '..' not in rel.parts and '\\' not in name,'archive path escape');b=base64.b64decode(x['payloads'][h],validate=True);need(hashlib.sha256(b).hexdigest()==h,'payload digest');dest=a.restore/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
 print(json.dumps({'restored_files':len(x['files'])}))
else:
 need(a.matrix and a.matrix.is_dir(),'matrix required');x={'schema':'native-cpu-replay-matrix-archive-v1','files':{},'payloads':{}}
 for f in sorted(a.matrix.rglob('*')):
  if f.is_file():
   b=f.read_bytes();h=hashlib.sha256(b).hexdigest();x['files'][str(f.relative_to(a.matrix))]=h;x['payloads'][h]=base64.b64encode(b).decode('ascii')
 with a.archive.open('x') as out:json.dump(x,out,separators=(',',':'));out.write('\n')
 print(json.dumps({'files':len(x['files']),'unique_payloads':len(x['payloads']),'archive_bytes':a.archive.stat().st_size}))
