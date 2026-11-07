"""Publish final compact results/transport receipts after offline readback."""
from host_rtx import *
import deliver_rtx as delivery
import zipfile

delivery.transport.RELEASE_ID=436862076

def confirmed(path):
    for attempt in range(3):
        try:
            state=delivery.transport.release();break
        except subprocess.CalledProcessError:
            if attempt==2:raise
            time.sleep(3)
    asset=next((a for a in state['assets'] if a['name']==path.name),None)
    if asset is None:return delivery.transport.upload(path)
    h=sha(path);assert asset['size']==path.stat().st_size and asset.get('digest')=='sha256:'+h
    return dict(name=path.name,bytes=path.stat().st_size,sha256=h,url=asset['browser_download_url'],asset_id=asset['id'])

def main():
    assert (ROOT/'GPU_STOP.json').exists() and not Path('D:/HeteroSpec-PC/RTX_EXPERIMENT.lock').exists()
    assert read(ROOT/'ARTIFACT_READBACK.json')['new_GPU_requests']==0
    assert read(HERE/'host_evidence/host/ARTIFACT_READBACK.json')==read(ROOT/'ARTIFACT_READBACK.json')
    path=delivery.OUT/'rtx-phase1-receipts.zip';start=time.monotonic();manifest={}
    files=[p for p in (HERE/'host_evidence').rglob('*') if p.is_file()]
    files += list(HERE.glob('*.py'))
    files += [HERE/n for n in ('RESULT.md','REPRODUCE_RTX.md','MODEL_ASSETS.json','SOURCE_AND_BUILD.json')]
    resumed=path.exists()
    if not resumed:
        with zipfile.ZipFile(path,'x',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
            for p in sorted(files):
                name=p.relative_to(HERE).as_posix();manifest[name]=dict(sha256=sha(p),bytes=p.stat().st_size);z.write(p,name)
            z.writestr('RECEIPTS_MANIFEST.json',json.dumps(dict(files=manifest,scope='Compact analysis/results and final delivery/readback receipts; native source/runtime/raw evidence are separate assets.',models_included=False),indent=2))
    else:
        # Preserve the first uploaded capsule/version; never silently rebuild it.
        with zipfile.ZipFile(path) as z:
            manifest=json.loads(z.read('RECEIPTS_MANIFEST.json'))['files']
            for name,row in manifest.items():
                raw=z.read(name);assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
    asset=confirmed(path)
    receipt=dict(asset=asset,files=len(manifest),wall_s=time.monotonic()-start,resumed_existing_verified_archive=resumed,late_failure_in='PUBLICATION_FAILURE-1.json' if resumed else None,scientific_result_commit='885959061df540c81a1ccb135cf772534b606308',final_receipts_supplement_scientific_commit=True,additional_model_requests=0)
    put(ROOT/'ARTIFACT_RECEIPTS_ASSET.json',receipt)
    put(HERE/'host_evidence/host/ARTIFACT_RECEIPTS_ASSET.json',receipt)
    for name in ('ARTIFACT_DELIVERY.json','ARTIFACT_READBACK.json','ARTIFACT_RECEIPTS_ASSET.json','PUBLICATION_FAILURE-1.json'):
        if (ROOT/name).exists():confirmed(ROOT/name)
    print('Final compact results and transport/readback receipts published, SHA256/size verified',flush=True)

if __name__=='__main__':main()
