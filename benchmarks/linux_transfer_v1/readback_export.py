"""Verify the public derived bundle and optionally every indexed private capture."""
from pathlib import Path, PurePosixPath
import argparse, gzip, hashlib, json
from common import need, read, sha

def verify(directory,raw_work=None,materialize=None):
 directory=Path(directory).resolve();scope=read(directory/'EXPORT_SCOPE.json')
 need(sha(directory/'TEXT_INDEX.json')==scope['text_index_sha256'],'Text index changed')
 need(sha(directory/'BINARY_CAPTURE_INDEX.json')==scope['binary_index_sha256'],'Binary index changed')
 bundle=directory/'scientific-records.json.gz'
 need(sha(bundle)==scope['bundle_sha256'],'Compressed public bundle changed')
 index=read(directory/'TEXT_INDEX.json');binary=read(directory/'BINARY_CAPTURE_INDEX.json')
 need(index['bundle_sha256']==scope['bundle_sha256'],'Bundle index binding differs')
 with gzip.open(bundle,'rb') as f:data=f.read()
 need(len(data)==index['uncompressed_bytes'],'Truncated/extended public bundle')
 j=json.loads(data);need(j['schema']=='linux-transfer.public-text-bundle.v1','Unknown public bundle schema')
 entries={x['path']:x for x in index['files']}
 need(len(entries)==len(index['files'])==scope['text_files']==len(j['records']),'Duplicate/missing indexed text file')
 seen=set();dest=None
 if materialize:
  dest=Path(materialize).resolve();need(not dest.exists(),'Extract only into a fresh directory');dest.mkdir(parents=True)
 def relative(name):
  p=PurePosixPath(name);need(not p.is_absolute() and p.parts and all(x not in ('..','') for x in p.parts),'Unsafe indexed path');return p
 for r in j['records']:
  name=r['path'];rel=relative(name);need(name in entries and name not in seen,'Unexpected/duplicate public record');seen.add(name)
  b=r['text'].encode();row=entries[name]
  need(len(b)==row['exported_bytes'] and hashlib.sha256(b).hexdigest()==row['exported_sha256'],'Public text bytes differ: '+name)
  if dest:
   p=dest/str(rel);p.parent.mkdir(parents=True,exist_ok=True)
   with p.open('xb') as f:f.write(b)
 need(len(binary['files'])==binary['count']==scope['binary_captures'],'Binary count differs')
 need(sum(x['bytes'] for x in binary['files'])==binary['bytes'],'Binary byte total differs')
 names=set();raw_count=0
 for row in binary['files']:
  name=row['path'];rel=relative(name);need(name not in names,'Duplicate indexed binary');names.add(name)
  if raw_work:
   root=Path(raw_work).resolve();p=root/str(rel)
   need(p.resolve().is_relative_to(root) and p.is_file(),'Indexed raw capture unavailable')
   need(p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],'Raw binary readback differs: '+name);raw_count+=1
 return {'public_bundle_passed':True,'public_text_files':len(entries),'indexed_binary_captures':len(names),
         'private_raw_captures_read_back':raw_count,'public_raw_binary_archive':False,
         'scope':'Derived public text byte readback; private capture readback only if --raw-work supplied; not third-party reproduction'}

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--export',dest='directory',required=True);p.add_argument('--raw-work');p.add_argument('--materialize')
 a=p.parse_args();print(json.dumps(verify(a.directory,a.raw_work,a.materialize),indent=2))
