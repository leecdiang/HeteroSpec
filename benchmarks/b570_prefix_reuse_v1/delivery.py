"""Publish separate evidence; fresh-download and CPU-reconstruct delivered bytes."""
from host import *
PACK=ROOT.parent/'b570-prefix-reuse-evidence-20261104'
REMOTE=ROOT.parent/'b570-prefix-reuse-readback-20261104'
RESTORED=ROOT.parent/'b570-prefix-reuse-restored-20261104'
TAG='b570-prefix-reuse-v1-evidence-20261104'
def prepare():
 repro=ROOT/'repro';repro.mkdir()
 for p in HERE.iterdir():
  if p.is_file():shutil.copyfile(p,repro/p.name)
 shutil.copytree(HERE.parent/'tpds_prefix_reuse_v1',repro/'toolkit',ignore=shutil.ignore_patterns('__pycache__'))
 for name in ('object_archive.py','recover_release.py','publish_delivery.py'):
  s=(OLD/'repro'/name).read_text(encoding='utf-8')
  s=s.replace('b570-parallel-native-evidence','b570-prefix-reuse-native-evidence')
  s=s.replace('B570 physical-prefix parallelism evidence','B570 natural prefix reuse evidence')
  s=s.replace('B570 PR169','B570 PR175')
  if name=='publish_delivery.py':s=s.replace("'verify_raw.py','contrast.py'","'verify_raw.py'")
  (repro/name).write_text(s,encoding='utf-8',newline='\n')
 historical=ROOT/'historical';historical.mkdir()
 for p in [*OLD.glob('R-*.json'),OLD/'K1_REGRESSION.json',OLD/'SOURCE_BINDING-candidate-D.json',OLD/'FREEZE.json']:shutil.copyfile(p,historical/p.name)
 exposure=ROOT/'corpus/exposure_objects';exposure.mkdir()
 for pin in read(ROOT/'corpus/EXPOSURE_AUDIT.json')['files']:
  src=Path(pin['path']);assert sha(src)==pin['sha256'];dest=exposure/pin['sha256']
  if not dest.exists():shutil.copyfile(src,dest)
 sys.path.insert(0,str(repro));import object_archive
 object_archive.pack(ROOT,PACK)
 for name in ('object_archive.py','recompute.py','verify_raw.py','README.md'):shutil.copyfile(repro/name,PACK/name)
 object_archive.verify(PACK)
def publish(commit):
 sys.path.insert(0,str(ROOT/'repro'));import publish_delivery
 publish_delivery.run(PACK,REMOTE,TAG,commit)
def restore():
 sys.path.insert(0,str(ROOT/'repro'));import object_archive
 object_archive.restore(REMOTE,RESTORED)
 command([sys.executable,'-B',str(RESTORED/'repro/recompute.py'),str(RESTORED)],ROOT.parent/'b570-prefix-reuse-restored-recomputed.json')
 command([sys.executable,'-B',str(ROOT/'repro/recompute.py'),str(ROOT)],ROOT.parent/'b570-prefix-reuse-local-recomputed.json')
 assert read(ROOT.parent/'b570-prefix-reuse-restored-recomputed.json')==read(ROOT.parent/'b570-prefix-reuse-local-recomputed.json')
 write(HERE/'evidence/DELIVERY_READBACK.json',dict(release_url=read(REMOTE/'REMOTE_READBACK.json')['release_url'],index_sha256=sha(REMOTE/'INDEX.json'),restored=read(RESTORED/'RESTORE_RECEIPT.json'),reconstructed_sha256=sha(ROOT.parent/'b570-prefix-reuse-restored-recomputed.json'),same_host_authenticated_fresh_download=True,external_native_replication=False))
if __name__=='__main__':
 if sys.argv[1]=='pack':prepare()
 elif sys.argv[1]=='publish':publish(sys.argv[2])
 elif sys.argv[1]=='restore':restore()
