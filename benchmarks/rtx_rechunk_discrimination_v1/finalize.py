"""Delivery-only final checks; no native request is started."""
from audit import *
import archive,subprocess,shutil,datetime
def main():
    restored=Path('F:/rtx176-restored');raw=restored/'raw-evidence.zip'
    assert sha(raw)==read(ROOT/'ARCHIVE.json')['sha256']
    verification=archive.verify(raw);put(ROOT/'RESTORED_VERIFICATION.json',verification)
    metadata=json.loads(subprocess.check_output(['gh','api','repos/leecdiang/HeteroSpec/releases/tags/rtx-rechunk-discrimination-v1-20261104']))
    assets={x['name']:x for x in metadata['assets']};manifest=read(restored/'raw-evidence.zip.parts.json')
    for x in manifest['parts']:
        assert assets[x['name']]['size']==x['bytes'] and assets[x['name']]['digest']=='sha256:'+x['sha256']
    put(ROOT/'REMOTE_ASSETS.json',dict(release_id=metadata['id'],target=metadata['target_commitish'],assets=[{k:x[k] for k in ('name','size','digest','browser_download_url')} for x in metadata['assets']]))
    prepared=Path('F:/rtx176-prepared-replay')
    cmd=['D:/HeteroSpec-PC/python311/python.exe','-B',str(HERE/'reproduce.py'),'--runtime','F:/rtx172-restored-runtime/frozen-runtime.zip','--raw',str(raw),'--model','D:/HeteroSpec-PC/models/gguf/Qwen3-8B-Q8_0.gguf','--slot','science-session-0','--out',str(prepared),'--prepare-only']
    subprocess.run(cmd,check=True)
    replay=read(prepared/'replay-binding.json');assert replay['prepare_only'] and not list((prepared/'native').iterdir()) and not (prepared/'native.log').exists()
    assert sum(read(p)['requests'] for p in ROOT.glob('*/launch.json'))==174
    assert not Path('D:/HeteroSpec-PC/RTX_EXPERIMENT.lock').exists()
    frozen=read(ROOT/'FREEZE.json')
    for p,h in frozen['sources'].items():assert sha(HERE/p)==h
    uploads={p.name:read(p) for p in Path('F:/rtx176-transfer').glob('*.json')};downloads={p.name:read(p) for p in restored.glob('*.download-*.json')}
    put(ROOT/'DELIVERY.json',dict(status='NATIVE_COMPLETE_RESTORED_ARTIFACTS_VERIFIED_RTX_STOPPED',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),release_id=metadata['id'],raw=read(ROOT/'ARCHIVE.json'),restored_verification=verification,replay_preparation=replay,prepared_snapshots=len(list((prepared/'snapshots').glob('*.bin'))),additional_model_requests=0,native_replication=False,all_stage_requests=174,scientific_requests=160,release_operation=read(ROOT/'RELEASE_OPERATION.json'),uploads=uploads,downloads=downloads,transport_cost_scope='Individual attempts include parallel transfers; do not sum as elapsed wall time. Scientific and native costs are separately in COSTS.json.'))
    for p in ['ARCHIVE.json','REMOTE_ASSETS.json','RESTORED_VERIFICATION.json','RELEASE_OPERATION.json','DELIVERY.json']:shutil.copy2(ROOT/p,HERE/'evidence'/p)
    print('Delivered verified archive and prepare-only replay; 174 requests unchanged; RTX stopped.')
if __name__=='__main__':main()
