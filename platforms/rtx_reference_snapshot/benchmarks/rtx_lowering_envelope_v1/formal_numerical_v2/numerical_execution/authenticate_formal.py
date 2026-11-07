"""Authenticated archive delivery only; no numerical/native/device invocation."""
import datetime,hashlib,json,subprocess,sys,urllib.request,zipfile
from pathlib import Path,PurePosixPath
D=Path(__file__).resolve().parent;V=D.parent;R=V/'formal_readback';R.mkdir(exist_ok=True)
sys.path.insert(0,str(V))
from common import load,save,sha
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=V).decode().strip()
assert commit=='db32bbc60c5c0f86be2540c87713ab3ab5c9b972'
token=subprocess.check_output(['gh','auth','token']).decode().strip()
headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github.raw+json','Accept-Encoding':'identity','User-Agent':'HeteroSpec-formal-v2-raw-auth'}
received=[]
try:
    for source,destination in [('formal_delivery/MANIFEST.json',R/'REMOTE_MANIFEST.json'),('formal_delivery/RAW_FORMAL_V2.zip',R/'REMOTE_RAW_FORMAL_V2.zip')]:
        url='https://api.github.com/repos/leecdiang/HeteroSpec/contents/benchmarks/rtx_lowering_envelope_v1/formal_numerical_v2/'+source+'?ref='+commit
        req=urllib.request.Request(url,headers=headers)
        h=hashlib.sha256();size=0
        with urllib.request.urlopen(req,timeout=60) as response, destination.open('xb') as out:
            assert response.status==200
            while True:
                block=response.read(1024*1024)
                if not block:break
                out.write(block);h.update(block);size+=len(block)
                assert size<=805683337,'frozen archive bound'
        local=V/source;assert size==local.stat().st_size and h.hexdigest()==sha(local)
        received.append(dict(path=source,bytes=size,sha256=h.hexdigest()))
    manifest=load(R/'REMOTE_MANIFEST.json');remote=R/'REMOTE_RAW_FORMAL_V2.zip'
    assert sha(remote)==manifest['sha256'] and remote.stat().st_size==manifest['bytes']
    with zipfile.ZipFile(remote) as z:
        assert len(z.namelist())==len(set(z.namelist()))==len(manifest['members'])
        assert set(z.namelist())=={m['path'] for m in manifest['members']}
        for m in manifest['members']:
            p=PurePosixPath(m['path']);assert not p.is_absolute() and '..' not in p.parts and ':' not in m['path'] and '\\' not in m['path']
            b=z.read(m['path']);assert len(b)==m['bytes'] and hashlib.sha256(b).hexdigest()==m['sha256']
    # Keep exactly two complete archive copies. Move, never recopy: the frozen
    # package_formal fresh-restore entry will read the actually downloaded bytes.
    original=V/'formal_delivery/RAW_FORMAL_V2.zip';backup=R/'LOCAL_ORIGINAL.zip'
    assert original.resolve().is_relative_to(V.resolve()) and backup.resolve().is_relative_to(V.resolve())
    assert not backup.exists() and sha(original)==sha(remote)
    original.rename(backup);remote.rename(original)
    save(D/'AUTHENTICATED_FORMAL.json',dict(recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),data_commit=commit,authenticated_remote_bytes=True,files=received,archive_sha256=manifest['sha256'],verified_members=len(manifest['members']),actual_downloaded_archive_for_frozen_restore=str(original),original_local_archive_retained=str(backup),complete_archive_copies=2,new_GPU_native_model_query_starts=0,scientific_retry=False))
    print('Authenticated full remote archive and every member. Two archive copies retained; frozen restore will read actual remote bytes.')
except BaseException as exc:
    save(D/'FORMAL_READBACK_FAILED.json',dict(recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),data_commit=commit,error=repr(exc),completed_files=received,retained_partial_paths=[str(p) for p in R.glob('*') if p.is_file()],new_GPU_starts=0,no_scientific_retry=True))
    raise
