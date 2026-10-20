"""Read-only delivery qualification from actual downloaded bytes and restored raw recomputation."""
import json,hashlib,zipfile,base64
from pathlib import Path
from evidence_contract import need,member,manifest_check,inventory
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(x):return (json.dumps(x,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def external(root,value):
 p=Path(value).resolve();need(p!=root and root not in p.parents,'delivery proof must be external')
 from campaign_budget import config
 _,owned=config(root,read_only=True);need(owned in p.parents,'delivery proof outside registered area')
 for q in [p,*p.parents]:
  need(not q.is_symlink() and not q.is_junction(),'delivery proof alias')
 need(p.is_file() and p.stat().st_nlink==1,'delivery proof file');return p
def check(root,c,manifest,tool_binding,recompute):
 root=Path(root).resolve();proof=c.get('restoration_proof');need(isinstance(proof,dict),'actual restoration proof required')
 def receipt(name):
  ref=proof[name];p=external(root,ref['path']);need(sha(p)==ref['sha256'],'delivery receipt hash '+name)
  return json.loads(p.read_bytes())
 archive=receipt('archive');download=receipt('download');restore=receipt('restore')
 manifest_sha=sha(member(root,manifest));m=json.loads(member(root,manifest).read_bytes())
 need(archive['manifest_sha256']==download['manifest_sha256']==restore['manifest_sha256']==manifest_sha,'delivery manifest binding')
 original=external(root,archive['path']);remote=external(root,download['path'])
 need(original!=remote,'download must use fresh path')
 need(original.stat().st_size==remote.stat().st_size==archive['bytes']==download['bytes'],'download byte count')
 need(sha(original)==sha(remote)==archive['sha256']==download['sha256']==restore['archive_sha256'],'actual downloaded archive hash')
 chunks=download['chunks'];need(chunks and all(x.get('remote_blob_sha') and x.get('sha256') and x.get('bytes',0)>0 for x in chunks),'remote chunk provenance')
 parts=[];provider_downloads=[]
 for row in chunks:
  p=external(root,row['path']);data=p.read_bytes();need(len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],'download chunk bytes')
  need(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==row['remote_blob_sha'],'download chunk Git identity');parts.append(data)
  from delivery_binding_v6 import download as bind_download
  provider_downloads.append(bind_download(root,row['tool_operation'],row,download['remote_commit']))
 need(base64.b64decode(b''.join(parts),validate=True)==remote.read_bytes(),'actual downloaded chunk reconstruction')
 need(download.get('remote_commit') and download.get('transport')=='github_authenticated_blob_chunks','actual remote provenance')
 wanted={x['path']:x for x in m['files']};wanted[manifest]=dict(bytes=member(root,manifest).stat().st_size,sha256=manifest_sha)
 with zipfile.ZipFile(remote) as z:
  names=z.namelist();need(len(names)==len(set(names)) and set(names)==set(wanted),'downloaded archive exact membership')
  for name,row in wanted.items():
   data=z.read(name);need(len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],'downloaded archive member')
 restored=Path(restore['root']).resolve();need(restored!=root and root not in restored.parents,'fresh restored root')
 manifest_check(restored,manifest);need(sha(member(restored,manifest))==manifest_sha,'restored manifest')
 driver=member(restored,'source/recompute_cpu8.py')
 need(restore['driver_sha256']==sha(driver)==sha(member(root,'source/recompute_cpu8.py')),'packaged unchanged driver')
 need(restore['exit_code']==0 and restore['isolated_import'] is True,'actual packaged auditor exit')
 argv=restore['argv'];report=external(root,restore['report_path'])
 frozen=json.loads(member(root,'CAPABILITY_FREEZE.json').read_bytes())
 need(Path(argv[0]).resolve()==Path(frozen['python']).resolve() and sha(argv[0])==frozen['python_sha256'],'packaged auditor interpreter')
 expected=[argv[0],'-I','-S','-B',str(driver),'--root',str(restored),'--run',c['formal_run'],'--manifest',manifest,'--tool-binding',tool_binding,'--output',str(report)]
 need(argv==expected,'isolated packaged auditor argv')
 # The original source root is exactly sealed before download/restore.
 # Restore request, provider terminal, native exits and full stdout must be
 # captured by the independent outside owner, never created under root/tools.
 from delivery_binding_v6 import restore_postseal_invocation
 restore_binding=restore_postseal_invocation(root,restore['tool_operation'],argv,report)
 report=external(root,restore['report_path']);prefix=member(root,'reports/CPU8_PREFIX.json')
 expected=canonical(recompute(restored))
 need(report.read_bytes()==prefix.read_bytes()==expected and sha(report)==restore['report_sha256'],'actual byte-identical independent reconstruction')
 need(restore['manifest_members']==len(m['files']),'restored complete count')
 return dict(provider_downloads=provider_downloads,restore_tool_binding=restore_binding,status='DOWNLOADED_RAW_RECOMPUTED',archive_sha256=sha(remote),manifest_sha256=manifest_sha,members=len(m['files']),reconstruction_sha256=sha(report),remote_commit=download['remote_commit'],scope='Actual downloaded bytes, exact restored tree and portable packaged auditor; no claim of full OS ledger')
