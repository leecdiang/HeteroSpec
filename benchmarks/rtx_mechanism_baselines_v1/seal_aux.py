"""Hash post-archive CPU closure receipts/drafts separately from immutable raw ZIP."""
from common import V,load,save,sha
from prepare_rtx import root
from pathlib import Path
r=root();arc=Path(str(r)+'-archive');fresh=Path(str(r)+'-fresh');members={}
for label,folder in [('archive',arc),('fresh',fresh)]:
    candidates=[p for p in folder.rglob('*') if p.is_file()] if label=='archive' else list(folder.glob('*.json'))
    for p in candidates:
        if label=='archive' and (p.name in ['raw.zip','MEMBERS.json','DELIVERY_AUX_MANIFEST.json','GIT_DELIVERY_READBACK.json'] or p.name.startswith('GIT_READBACK')):continue
        members[label+'/'+p.relative_to(folder).as_posix()]=dict(bytes=p.stat().st_size,sha256=sha(p))
save(arc/'DELIVERY_AUX_MANIFEST.json',members);save(V/'DELIVERY_AUX.json',dict(path=str(arc/'DELIVERY_AUX_MANIFEST.json'),sha256=sha(arc/'DELIVERY_AUX_MANIFEST.json'),members=len(members),scope='post-main-archive CPU restore/replay receipts,input-plan audit,preserved report formatting draft/failure;later Git readback receipt excluded to avoid recursive binding',main_raw_zip_unchanged=True,remote_raw_uploaded=False));print('auxiliary CPU receipts',len(members))
