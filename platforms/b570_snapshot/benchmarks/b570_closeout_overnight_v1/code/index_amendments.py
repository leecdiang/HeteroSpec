"""CPU-only chronology index, retaining original amendment bytes unchanged."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,subprocess
ROOT=Path(__file__).parent
items=[]
for name,commit in [('RECOVERY_AMENDMENT.json','6fee207'),('TIMER_AMENDMENT.json','9aee4cd'),('recovery/CPU_GRAPH_ZERO_AMENDMENT.json','cb9d30c'),('MATCHED_RESERVATION_AMENDMENT.json','19db04f')]:
 p=ROOT/name;body=json.loads(p.read_text(encoding='utf-8-sig'))
 info=subprocess.check_output(['git','show','-s','--format=%H%n%cI',commit],cwd=ROOT,text=True).strip().splitlines()
 items.append(dict(path=name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),recorded_utc=body.get('utc'),bound_commit=info[0],commit_timestamp=info[1],observed_file_mtime_utc=datetime.fromtimestamp(p.stat().st_mtime,timezone.utc).isoformat(),reason=body['reason']))
out=dict(utc=datetime.now(timezone.utc).isoformat(),reason='Index existing pre-new-input amendments. Timer and CPU correction receipts lacked their own UTC field; preserve them verbatim and bind contemporaneous commits/file timestamps without inventing an earlier index time.',model_forwards=0,original_amendment_bytes_changed=False,items=items)
(ROOT/'AMENDMENT_INDEX.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\n')
