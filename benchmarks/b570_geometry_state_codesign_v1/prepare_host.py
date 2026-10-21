"""P0-only CAS restore. Does not import a model runtime or start a native worker."""
import hashlib,json,pathlib,shutil,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
OLD=pathlib.Path(r'C:/Users/DIANG/Documents/ChatGPT/HeteroSpec/work')
EXPECTED='816b802f915373c861e754bba448048705ce790ee8a230e114fef8197079a530'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 archive=OLD/'b570-phasebinding-boundary-v1/COMPLETE_CAS.zip'
 assert sha(archive)==EXPECTED
 dest=ROOT/'_host/pr97'
 assert not dest.exists(),'Never overwrite restored evidence'
 with zipfile.ZipFile(archive) as z:
  mb=z.read('MANIFEST.json');m=json.loads(mb);rows=m['files']
  assert len(rows)==m['logical_files']==8358
  assert len({r['path'].casefold() for r in rows})==len(rows)
  hashes={r['sha256'] for r in rows}
  assert len(hashes)==m['unique_objects']==7883
  assert set(z.namelist())=={'MANIFEST.json'}|{'objects/'+h for h in hashes}
  for h in sorted(hashes):assert hashlib.sha256(z.read('objects/'+h)).hexdigest()==h
  for r in rows:
   p=pathlib.PurePosixPath(r['path'])
   assert not p.is_absolute() and '..' not in p.parts and ':' not in str(p) and chr(92) not in str(p)
   out=dest/p;assert out.resolve().is_relative_to(dest.resolve())
   data=z.read('objects/'+r['sha256']);assert len(data)==r['bytes']
   out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(data)
  for r in rows:assert sha(dest/r['path'])==r['sha256']
 (ROOT/'p0/PR97_RESTORE.json').write_text(json.dumps(dict(status='PASS_FRESH_FULL_BYTE_RESTORE',archive_sha256=EXPECTED,manifest_sha256=hashlib.sha256(mb).hexdigest(),logical_files=len(rows),unique_objects=len(hashes),source_head='5a66653bd0ce413d4eb9aef3a4501b93c138071b',native_starts=0),indent=2)+'\n')
 (ROOT/'p0/PR97_MANIFEST.json').write_bytes(mb)
 print('RESTORED',len(rows),'files; no native starts')
if __name__=='__main__':main()
