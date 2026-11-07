"""Publish the bounded native failure evidence and verify restored bytes."""
from host import *
PACK=ROOT.parent/'b570-decisive-evidence-20261105'
REMOTE=ROOT.parent/'b570-decisive-readback-20261105'
RESTORED=ROOT.parent/'b570-decisive-restored-20261105'
TAG='b570-decisive-v1-evidence-20261105'
def pack():
 for role,label in [('original-final','original-runtime'),('shared-01','candidate-runtime')]:
  target=ROOT/'historical'/label;target.mkdir()
  for f in read(OLD/role/'FILES.json')['files']:
   assert sha(f['path'])==f['sha256']
   shutil.copyfile(f['path'],target/Path(f['path']).name)
 # The old transport code has already delivered authenticated evidence on this host.
 legacy=Path('I:/HeteroSpec/b570-prefix-reuse-20261104/repro')
 delivery=ROOT/'delivery';delivery.mkdir()
 for name in ('object_archive.py','recover_release.py','publish_delivery.py'):
  s=(legacy/name).read_text()
  s=s.replace('b570-prefix-reuse-native-evidence','b570-decisive-native-evidence').replace('B570 natural prefix reuse evidence','B570 PR185 prefill repair and capacity evidence').replace('B570 PR175','B570 PR185 result')
  if name=='publish_delivery.py':
   s=s.replace("'INDEX.json','MEMBERS.json','object_archive.py','recompute.py','verify_raw.py','report_details.py','b570-prefix-native-source-kit.zip','README.md'","'INDEX.json','MEMBERS.json','object_archive.py','recompute.py','README.md'")
  (delivery/name).write_text(s,encoding='utf-8',newline='\n')
 for p in HERE.iterdir():
  if p.is_file():shutil.copyfile(p,ROOT/'repro/host'/p.name)
 wrapper="from pathlib import Path\nimport json,sys\nroot=Path(sys.argv[1])\nsys.path.insert(0,str(root/'repro/host'))\nfrom closeout import audit\nprint(json.dumps(audit(root),indent=2))\n"
 (delivery/'recompute.py').write_text(wrapper,encoding='utf-8')
 shutil.copyfile(HERE/'README.md',delivery/'README.md')
 sys.path.insert(0,str(delivery));import object_archive
 object_archive.pack(ROOT,PACK)
 for n in ('object_archive.py','recompute.py','README.md'):shutil.copyfile(delivery/n,PACK/n)
 object_archive.verify(PACK)
def publish(commit):
 sys.path.insert(0,str(ROOT/'delivery'));import publish_delivery
 publish_delivery.run(PACK,REMOTE,TAG,commit)
def restore():
 sys.path.insert(0,str(ROOT/'delivery'));import object_archive
 object_archive.restore(REMOTE,RESTORED)
 command([sys.executable,'-B',RESTORED/'delivery/recompute.py',RESTORED],ROOT.parent/'b570-decisive-restored-report.json')
 command([sys.executable,'-B',ROOT/'delivery/recompute.py',ROOT],ROOT.parent/'b570-decisive-local-report.json')
 assert read(ROOT.parent/'b570-decisive-restored-report.json')==read(ROOT.parent/'b570-decisive-local-report.json')==read(ROOT/'RECONSTRUCTION.json')
 write(HERE/'evidence/DELIVERY_READBACK.json',dict(release_url=read(REMOTE/'REMOTE_READBACK.json')['release_url'],index_sha256=sha(REMOTE/'INDEX.json'),restore=read(RESTORED/'RESTORE_RECEIPT.json'),report_sha256=sha(ROOT.parent/'b570-decisive-restored-report.json'),same_host_authenticated_fresh_download=True,external_native_replication=False,capacity_stop_preserved=True))
if __name__=='__main__':
 action=sys.argv[1];t0=time.monotonic();start=utc();ok=False
 try:
  if action=='pack':pack()
  elif action=='publish':publish(sys.argv[2])
  elif action=='restore':restore()
  ok=True
 finally:write(ROOT.parent/('b570-decisive-delivery-'+action+'.json'),dict(started_utc=start,finished_utc=utc(),wall_seconds=time.monotonic()-t0,success=ok,model_requests=0))
