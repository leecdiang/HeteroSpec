"""Actual HTTPS body readback of the committed benchmark and fresh remote capsule restore."""
import concurrent.futures,hashlib,json,pathlib,subprocess,urllib.request,zipfile,io,os,base64
ROOT=pathlib.Path(__file__).resolve().parent
REPO=ROOT.parents[1];GIT=r'C:/hs/pr108-tools/git/cmd/git.exe'
def main():
 commit=subprocess.check_output([GIT,'rev-parse','HEAD'],cwd=REPO,text=True).strip()
 listing=subprocess.check_output([GIT,'ls-tree','-r','-z','HEAD','--','benchmarks/b570_geometry_state_codesign_v1'],cwd=REPO).decode().split(chr(0));entries=[]
 for row in listing:
  if not row:continue
  meta,name=row.split(chr(9),1);mode,kind,blob=meta.split();assert kind=='blob';entries.append((name,blob))
 credentials=subprocess.run([GIT,'credential','fill'],input='protocol=https\nhost=github.com\n\n',capture_output=True,text=True,env=dict(os.environ,GIT_TERMINAL_PROMPT='0'),check=True).stdout
 fields=dict(line.split('=',1) for line in credentials.splitlines() if '=' in line);token=fields.get('password');assert token,'Git credential helper did not return authentication'
 dest=ROOT/'_host/remote_authenticated_readback';assert not dest.exists();dest.mkdir(parents=True)
 def one(entry):
  name,blob=entry;url='https://api.github.com/repos/leecdiang/HeteroSpec/git/blobs/'+blob
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'HeteroSpec-P0-readback','Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'}),timeout=45) as r:
   assert r.status==200;body=json.load(r);assert body['sha']==blob and body['encoding']=='base64';data=base64.b64decode(body['content'])
  local=(REPO/name).read_bytes();assert data==local,('REMOTE_BYTE_MISMATCH',name)
  actual=hashlib.sha1(('blob '+str(len(data))+chr(0)).encode()+data).hexdigest();assert actual==blob
  p=dest/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
  return dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),git_blob=blob,transport='actual authenticated GitHub API blob body',url=url)
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:rows=list(ex.map(one,entries))
 remote=dest/'benchmarks/b570_geometry_state_codesign_v1';archive=remote/'p0/NATIVE_P0_CAPSULE.zip';fresh=ROOT/'_host/remote_capsule_restore';assert not fresh.exists()
 with zipfile.ZipFile(archive) as z:
  manifest=json.loads(z.read('MANIFEST.json'))
  assert set(z.namelist())=={'MANIFEST.json'}|{x['path'] for x in manifest}
  for x in manifest:
   data=z.read(x['path']);assert len(data)==x['bytes'] and hashlib.sha256(data).hexdigest()==x['sha256'];p=fresh/x['path'];assert p.resolve().is_relative_to(fresh.resolve());p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 for x in manifest:assert hashlib.sha256((fresh/x['path']).read_bytes()).hexdigest()==x['sha256']
 f0hash=hashlib.sha256((remote/'p0/F0_EXECUTION.json').read_bytes()).hexdigest()
 result=dict(status='PASS_REMOTE_BYTE_READBACK',commit=commit,F0_sha256=f0hash,files_verified=len(rows),files=rows,capsule_fresh_remote_restore_members=len(manifest),models_and_original_PR97_CAS='External pinned dependencies; unchanged local full restore and model rehash receipts retained',new_model_starts=0,author_authorization=False)
 (ROOT/'p0/REMOTE_READBACK.json').write_text(json.dumps(result,sort_keys=True,separators=(',',':'))+'\n')
 print(json.dumps({k:v for k,v in result.items() if k!='files'}))
if __name__=='__main__':main()
