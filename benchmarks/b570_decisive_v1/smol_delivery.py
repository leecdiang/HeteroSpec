"""Append-only recovery release and authenticated fresh-byte reconstruction."""
from smol import *
# Separate local volume keeps archive/readback/restore copies away from the
# original run volume's mandatory reserve. No original evidence is moved.
DELIVERY_ROOT=Path(os.environ.get('HS_DECISIVE_DELIVERY_ROOT','E:/HeteroSpec'))
PACK=DELIVERY_ROOT/'b570-decisive-recovery-pack-20261105'
REMOTE=DELIVERY_ROOT/'b570-decisive-recovery-readback-20261105'
RESTORED=DELIVERY_ROOT/'b570-decisive-recovery-restored-20261105'
TAG='b570-decisive-recovery-v2-evidence-20261105'

def prepare():
 assert not LOCK.exists()
 repro=ROOT/'repro/recovery';shutil.copytree(HERE,repro,ignore=shutil.ignore_patterns('__pycache__'))
 shutil.copytree(TOOLKIT,ROOT/'repro/recovery-toolkit',ignore=shutil.ignore_patterns('__pycache__'))
 transport=ROOT/'delivery-v2';transport.mkdir()
 for name in ('object_archive.py','recover_release.py','publish_delivery.py'):
  text=(ROOT/'delivery'/name).read_text();text=text.replace('B570 PR185 prefill repair and capacity evidence','B570 PR185 repair continuation and Smol native evidence')
  (transport/name).write_text(text,encoding='utf-8',newline='\n')
 wrapper="from pathlib import Path\nimport os,sys,json\nroot=Path(sys.argv[1]).resolve()\nos.environ['HS_DECISIVE_ROOT']=str(root)\nreader=root/'repro/recovery-final'\nif not reader.exists():reader=root/'repro/recovery'\nsys.path.insert(0,str(reader))\nfrom smol_audit import audit\nprint(json.dumps(audit(),indent=2))\n"
 (transport/'recompute.py').write_text(wrapper)
 shutil.copyfile(HERE/'README.md',transport/'README.md')
 log=ROOT.parent/'b570-decisive-recovery-local-report.json'
 command([sys.executable,'-B',transport/'recompute.py',ROOT],log)
 write(ROOT/'RECOVERY_RECONSTRUCTION.json',read(log))
 write(HERE/'evidence/recovery/RECONSTRUCTION.json',read(log))

def pack():
 assert not LOCK.exists();transport=ROOT/'delivery-v2'
 # Include the final reviewable source/report without overwriting initial-v1 kit.
 target=ROOT/'repro/recovery-final';shutil.copytree(HERE,target,ignore=shutil.ignore_patterns('__pycache__'))
 (transport/'README.md').write_text('''# B570 PR185 result evidence, recovery v2

This is the separate SmolLM2-1.7B/135M Q8 result: four development roots,
twelve test roots, six retained arms, six paired sessions, 432 measurements
and 432 immediate warmups. All15 fixed contrasts and complete native costs
are retained. The Qwen mandatory-control capacity failure and initial v1
release remain failures/unchanged; Smol is not a Qwen admission claim.

Download every raw-objects-*.zip plus INDEX.json, MEMBERS.json and
object_archive.py into one directory DOWNLOAD. Choose a fresh RESTORED path.

```powershell
python object_archive.py verify --root DOWNLOAD
python object_archive.py restore --root DOWNLOAD --out RESTORED
python -m pip install -r RESTORED/repro/recovery-final/requirements-host.txt
python -B RESTORED/delivery-v2/recompute.py RESTORED
```

No model weights are needed for this read-only reconstruction. It verifies
all16 root qualifications, full target vectors/active states, actual physical
columns, terminal suffixes, all15 contrasts, loaded libraries, cleanup and the
cumulative immutable ledger. Every data path is rebased into RESTORED.

The final report is RESTORED/repro/recovery-final/RESULTS.md. Detailed receipts
are beside it in evidence/recovery. Actual frozen execution sources are under
secondary-smol/campaign02/source-freeze. Native binaries, portable frontend
inputs, commands, model identities and failed raw attempts are included.
Exact GGUF weights remain separate inputs for a native rerun; see the restored
README and authentication receipts. This package makes no external native
replication or anonymous-access claim. REMOTE_READBACK.json records actual
authenticated fresh-download verification on the B570 host. Final restored
report equality is recorded separately in result PR187.

Some CPU preparation/postprocessing was not separately wall-metered; all native
requests, warmups, failed attempts and model provisioning remain charged.
Inclusive coordinator/storage clocks overlap native wall and are not additive.
No merge, paper edit, new model download or rental.
''',encoding='utf-8',newline='\n')
 sys.path.insert(0,str(transport));import object_archive
 object_archive.pack(ROOT,PACK)
 for n in ('object_archive.py','recompute.py','README.md'):shutil.copyfile(transport/n,PACK/n)
 object_archive.verify(PACK)

def publish(commit):
 sys.path.insert(0,str(ROOT/'delivery-v2'));import publish_delivery
 publish_delivery.run(PACK,REMOTE,TAG,commit)

def restore():
 sys.path.insert(0,str(ROOT/'delivery-v2'));import object_archive
 object_archive.restore(REMOTE,RESTORED)
 log=ROOT.parent/'b570-decisive-recovery-restored-report.json'
 command([sys.executable,'-B',RESTORED/'delivery-v2/recompute.py',RESTORED],log)
 assert read(log)==read(ROOT/'RECOVERY_RECONSTRUCTION.json')
 write(HERE/'evidence/recovery/DELIVERY_READBACK.json',dict(release_url=read(REMOTE/'REMOTE_READBACK.json')['release_url'],index_sha256=sha(REMOTE/'INDEX.json'),restore=read(RESTORED/'RESTORE_RECEIPT.json'),report_sha256=sha(log),same_host_authenticated_fresh_download=True,external_native_replication=False,old_v1_release_unchanged=True))

if __name__=='__main__':
 action=sys.argv[1];started=utc();t0=time.monotonic();ok=False
 try:
  if action=='publish':publish(sys.argv[2])
  else:{'prepare':prepare,'pack':pack,'restore':restore}[action]()
  ok=True
 finally:write(ROOT.parent/('b570-recovery-delivery-'+action+'-'+started.replace(':','').replace('.','')+'.json'),dict(started_utc=started,finished_utc=utc(),wall_seconds=time.monotonic()-t0,success=ok,model_requests=0))
