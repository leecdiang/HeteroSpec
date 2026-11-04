"""Read-only slot progress; never reads or optimizes timing values."""
from host import *
from datetime import datetime,timezone
status={'utc':datetime.now(timezone.utc).isoformat()}
status['reference_roots_completed']=sum((ROOT/f'main-r-{i:02}/exit.json').exists() for i in range(32))
status['aligned_reference_roots_completed']=sum((ROOT/f'aligned-r-{i:02}/exit.json').exists() for i in range(8))
status['aligned_candidate_roots_completed']=sum((ROOT/f'aligned-q-{i:02}/exit.json').exists() for i in range(8))
for stage in ['main-q-session']+[f'main-cost-s{s}' for s in range(4)]+[f'aligned-cost-s{s}' for s in range(2)]:
    d=ROOT/stage
    if (d/'input.json').exists():
        units=read(d/'input.json')['units'];status[stage]=dict(expected=len(units),receipts=sum((d/u['id']/'receipt.json').exists() for u in units),exit=read(d/'exit.json') if (d/'exit.json').exists() else None)
status['disk_free_GiB']={x:round(shutil.disk_usage(x+':/').free/1024**3,2) for x in ('E','F')}
print(json.dumps(status,indent=2))
