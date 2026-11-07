#!/usr/bin/env python3
"""Fresh CPU/file-only archive reconstruction. Never imports a runner or executes models."""
import argparse, hashlib, json, subprocess, sys, tarfile, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
E=ROOT/'paper/mlsys2027/evidence'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def run(args, dest):
 p=subprocess.run([sys.executable,'-B',*map(str,args)],capture_output=True)
 Path(str(dest)+'.stdout.log').write_bytes(p.stdout);Path(str(dest)+'.stderr.log').write_bytes(p.stderr)
 if p.returncode:raise RuntimeError(p.stderr.decode(errors='replace')[-3000:])
 return json.loads(p.stdout)
def extract(p,dest):
 dest.mkdir()
 with tarfile.open(p) as t:t.extractall(dest,filter='data')
 return dest
def replay(work):
 work.mkdir(parents=True,exist_ok=False);checks={}
 def attempt(name,fn):
  try:checks[name]={'status':'RERUN_PASS',**fn()}
  except Exception as exc:checks[name]={'status':'RERUN_FAIL','error':str(exc)}
  (E/'ARCHIVE_REPLAY_V085_QA.json').write_text(json.dumps({'checks':checks,'local_qa_directory':str(work),'scope':'Fresh file/CPU verification; omitted weights/runtime/compiler/driver bytes not authenticated; no inference.'},indent=2)+'\n')
  print(name,checks[name]['status'],flush=True)
 def b570():
  d=ROOT/'artifacts/b570_partition_intervention_v1';m=read(d/'ARCHIVE.json');dest=work/'b570-fork.tar.gz';parts=[];h=hashlib.sha256();length=0
  with dest.open('xb') as out:
   for row in m['parts']:
    p=d/row['path'];assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
    with p.open('rb') as f:
     while chunk:=f.read(1024*1024):h.update(chunk);out.write(chunk);length+=len(chunk)
    parts.append({'path':row['path'],'bytes':row['bytes'],'sha256':row['sha256']})
  assert h.hexdigest()==m['archive_sha256'] and length==sum(x['bytes'] for x in m['parts'])
  root=extract(dest,work/'b570-fork');assert sha(root/'MANIFEST.json')==m['manifest_sha256']
  manifest=read(root/'MANIFEST.json');entries=manifest.get('files',manifest)
  for name,row in entries.items():
   p=root/name;expected=row['sha256'] if isinstance(row,dict) else row
   assert sha(p)==expected
   if isinstance(row,dict) and 'bytes' in row:assert p.stat().st_size==row['bytes']
  try:
   r=run([root/'scripts/platform/b570_partition_intervention_v1/verify_complete.py','--root',root],work/'b570-fork-check');original={'status':'RERUN_PASS'}
  except RuntimeError:
   prior=read(Path(str(work/'b570-fork-check')+'.stdout.log'))
   assert prior['errors'] and all(e.startswith('frozen model pair ') for e in prior['errors'])
   original={'status':'RERUN_FAIL','reason':'Windows backslash model basenames parsed with POSIX Path.name','errors':prior['errors']}
   r=run([ROOT/'paper/mlsys2027/scripts/portable_verify_b570_v085.py','--root',root],work/'b570-portable')
  assert r['validation']=='PASS';r.pop('fork_events',None);return {'archive_sha256':h.hexdigest(),'bytes':length,'ordered_parts':parts,'manifest_files':len(entries),'root':str(root),'canonical_entry_before_adapter':original,'result':r}
 attempt('B570_live_intervention',b570)
 def h2():
  index=ROOT/'artifacts/rtx_independent_proposal_replay_v2/complete-2ee030af9ed4a71bdb624698c5733cfe0ff335181ac0e915f7236dc75b04e7db.parts.json'
  r=run([ROOT/'scripts/platform/rtx_independent_proposal_replay_v2/reconstruct_parts.py',index,work/'rtx-h2'],work/'rtx-h2-check')
  return {'root':str(work/'rtx-h2/evidence'),'result':r}
 attempt('RTX_H2_complete',h2)
 def anon():
  p=next((ROOT/'artifacts/rtx_independent_proposal_replay_v2').glob('anonymous-*.tar.gz'));assert sha(p)=='a5919b59342ecc68bd5f57d3c2b192edf62933b2645924381c3765dd50beb369'
  r=extract(p,work/'rtx-h2-anonymous');result=run([r/'frozen_source/scripts/platform/rtx_independent_proposal_replay_v2/offline.py',r],work/'rtx-h2-anonymous-check')
  return {'root':str(r),'archive_sha256':sha(p),'result':result,'chronology':'Derived ordinal chronology only; not original remote chronology attestation.'}
 attempt('RTX_H2_anonymous',anon)
 for arm,directory in [('prediction','rtx_predictive_transfer_v1'),('latency','rtx_matched_latency_v1')]:
  def twoarm(arm=arm,directory=directory):
   d=ROOT/'artifacts'/directory;m=read(d/'archive_manifest.json');p=d/m['file'];assert sha(p)==m['sha256'] and p.stat().st_size==m['bytes']
   r=extract(p,work/('rtx-'+arm));a=run([r/f'verify_{arm}.py',r],work/('rtx-'+arm+'-check'));b=run([r/'verify_provenance.py',r,'--arm',arm],work/('rtx-'+arm+'-provenance'))
   return {'root':str(r),'archive_sha256':sha(p),'scientific':a,'provenance':b}
  attempt('RTX_'+arm,twoarm)
 def m4():
  d=ROOT/'artifacts/m4_runtime/runtime-profitability-control-20260925';m=read(d/'archive_descriptor.json');p=d/m['archive'];assert sha(p)==m['sha256']
  r=run([ROOT/'scripts/platform/m4_runtime/recompute_evidence_bundle.py',p,'--expected-sha256',m['sha256']],work/'m4-runtime-check');assert r==m['independent_recomputation']
  s=run([ROOT/'scripts/platform/m4_runtime/verify_guard_always_secondary.py','--receipt',work/'m4-secondary.json'],work/'m4-secondary-check')
  return {'archive_sha256':sha(p),'primary':r,'secondary':s}
 attempt('M4_runtime',m4)
 def old_b570_h1():
  d=ROOT/'artifacts/b570_mechanism_v08';m=read(d/'ARCHIVE.json');p=d/m['filename'];assert sha(p)==m['sha256'] and p.stat().st_size==m['bytes'];r=extract(p,work/'b570_mechanism_v08')
  completed=subprocess.run([sys.executable,'-B',str(r/'scripts/platform/b570_mechanism_v08/verify_archive.py'),str(r)],capture_output=True,check=True);(work/'b570-h1-check.stdout.log').write_bytes(completed.stdout);(work/'b570-h1-check.stderr.log').write_bytes(completed.stderr)
  return {'archive_sha256':sha(p),'root':str(r),'complete_verifier_stdout':completed.stdout.decode(),'scope':'Manifest, original Git object membership and complete old study verification.'}
 attempt('B570_original_H1',old_b570_h1)
 def old_b570_direct():
  d=ROOT/'artifacts/b570_direct_id_v1';m=read(d/'ARCHIVE.json');p=d/m['archive'];assert sha(p)==m['archive_sha256'] and p.stat().st_size==m['size'];r=extract(p,work/'b570_direct_id_v1')/'b570_direct_id_v1';result=run([r/'runner/verify.py','--root',r/'formal','--protocol',r/'protocol/protocol_v1.json','--analysis',r/'protocol/FORMAL_ANALYSIS.json','--manifest',r/'SHA256_MANIFEST.json'],work/'b570-direct-check')
  return {'archive_sha256':sha(p),'root':str(r),'result':result}
 attempt('B570_original_direct_ID',old_b570_direct)
 def old_rtx_direct():
  d=ROOT/'artifacts/rtx_direct_id_v2';m=read(d/'archive_manifest.json');p=d/m['archive'];assert sha(p)==m['sha256'] and p.stat().st_size==m['size_bytes'];r=extract(p,work/'rtx_direct_id_v2');result=run([r/'verify_rtx_direct_id_v2.py',r],work/'rtx-direct-check')
  return {'archive_sha256':sha(p),'root':str(r),'result':result}
 attempt('RTX_original_direct_ID',old_rtx_direct)
 checks['358H_runtime_raw']={'status':'UNAVAILABLE','reason':'Retained compact diagnostic does not include local raw traces; not a raw replay.'}
 (E/'ARCHIVE_REPLAY_V085_QA.json').write_text(json.dumps({'status':'RERUN_PASS' if all(x['status'] in ('RERUN_PASS','UNAVAILABLE') for x in checks.values()) else 'RERUN_FAIL','checks':checks,'local_qa_directory':str(work),'scope':'Fresh file/CPU verification; external omitted bytes not authenticated; no inference.'},indent=2)+'\n')
 return checks
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--work',type=Path);a=p.parse_args();work=a.work or Path(tempfile.mkdtemp(prefix='heterospec-v085-archives-'))/'fresh';r=replay(work);raise SystemExit(any(v['status']=='RERUN_FAIL' for v in r.values()))
