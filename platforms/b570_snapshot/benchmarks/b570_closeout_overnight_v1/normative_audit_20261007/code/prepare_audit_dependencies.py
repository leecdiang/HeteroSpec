from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
ROOT=Path(__file__).parent;BASE=Path('C:/hs/b570-closeout-v1')
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
pilot=BASE/'E_PILOT_RESULTS.json';selected=load(ROOT/'AMENDMENT.json')['selection'];records=load(pilot)
bound=[r for r in records if not r['warm'] and any(r['task']==p['task'] and r['config']['k']==p['k'] and r['config']['ub']==p['ub'] for p in selected)]
payload=dict(utc=datetime.now(timezone.utc).isoformat(),purpose='CPU-only restoration dependency, not reference/model input. Selection already froze original units and immutable archive before new diagnosis.',source_sha256=hashlib.sha256(pilot.read_bytes()).hexdigest(),original_archive_sha256=load(ROOT/'AMENDMENT.json')['prior_archive_sha256'],records=[dict(unit_id=r['unit_id'],task=r['task'],config=r['config'],endpoint=r['endpoint'],files=r['files']) for r in bound])
(ROOT/'PILOT_DEPENDENCY.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8',newline='\n')
