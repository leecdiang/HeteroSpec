import pathlib,json,hashlib,zipfile
R=pathlib.Path(__file__).resolve().parent.parent;D=R/'receipts/remote_download_v1';d=json.loads((D/'COMPLETE_CAS.json').read_text());a=D/'COMPLETE_CAS.zip'
with a.open('wb') as f:
 for x in d['parts']:
  b=(D/x['name']).read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256'];f.write(b)
with a.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==d['archive_sha256']
assert a.stat().st_size==d['archive_bytes']
with zipfile.ZipFile(a) as z:b=z.read('MANIFEST.json')
assert hashlib.sha256(b).hexdigest()==d['manifest_sha256']
assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==d['manifest_git_blob_sha1']
(D/'ARCHIVE_MANIFEST.json').write_bytes(b)
print(json.dumps(dict(status='PASS_ACTUAL_REMOTE_ASSEMBLY',archive_sha256=d['archive_sha256'],manifest_sha256=d['manifest_sha256'],manifest_git_blob_sha1=d['manifest_git_blob_sha1'],parts=len(d['parts']))))
