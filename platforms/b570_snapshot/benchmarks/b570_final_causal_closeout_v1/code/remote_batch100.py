import sys,json,urllib.request,urllib.parse,hashlib,concurrent.futures
from pathlib import Path
R=Path(__file__).resolve().parents[1];job=json.loads(sys.stdin.read());dest=R/'receipts/authenticated_remote_parts';dest.mkdir(parents=True,exist_ok=True)
def chk(b,p):
 assert len(b)==p['bytes'] and hashlib.sha256(b).hexdigest()==p['sha256']
 assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==p['git_sha']
def one(p):
 f=dest/p['name']
 if f.exists():chk(f.read_bytes(),p);return dict(name=p['name'],status='ALREADY_DOWNLOADED_ACTUAL_BYTES_REHASHED')
 try:
  u=urllib.parse.urlparse(p['url']);assert u.scheme=='https' and u.hostname=='raw.githubusercontent.com'
  b=urllib.request.urlopen(p['url'],timeout=30).read();chk(b,p);f.write_bytes(b)
  return dict(name=p['name'],status='ACTUAL_AUTHENTICATED_HTTPS_BODY_VERIFIED',bytes=len(b),sha256=p['sha256'],git_sha=p['git_sha'])
 except Exception as e:return dict(name=p['name'],status='TRANSPORT_FAILURE',error_type=type(e).__name__,error=str(e))
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:rows=list(pool.map(one,job['parts']))
out=dict(batch=job['batch'],authenticated_commit=job['commit'],rows=rows,credentials_persisted=False)
(R/'receipts'/('REMOTE_DOWNLOAD_BATCH_'+str(job['batch'])+'.json')).write_bytes((json.dumps(out,indent=2)+'\n').encode())
print(json.dumps(dict(batch=job['batch'],complete=sum(r['status']!='TRANSPORT_FAILURE' for r in rows),failed=[r['name'] for r in rows if r['status']=='TRANSPORT_FAILURE'],files_total=len(list(dest.iterdir())))))
