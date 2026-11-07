"""Read-only concise status from the native ledger and handshake journal."""
import json
from pathlib import Path

root=Path('E:/rtx160/research')
rows=[json.loads(l) for l in (root/'LEDGER.jsonl').read_text().splitlines() if l]
starts={(r['epoch'],r['unit']):r for r in rows if r['event']=='START'}
ends={(r['epoch'],r['unit']):r for r in rows if r['event']=='END'}
result={'reserved_credits':sum(r['reserved_requests'] for r in starts.values()),
        'failed_units':sum(not r['success'] for r in ends.values()),'active':[]}
for key,start in starts.items():
    if key in ends:continue
    unit=Path(key[0])/'units'/key[1];events=unit/'EVENTS.jsonl';slots=unit/'SLOTS.json'
    records=[json.loads(l) for l in events.read_text().splitlines() if l] if events.exists() else []
    done=[r for r in records if r['event']=='REQUEST_COMPLETED']
    result['active'].append({'epoch':Path(key[0]).name,'unit':key[1],
      'completed_events':len(done),'scheduled_requests':len(json.loads(slots.read_text())) if slots.exists() else None,
      'last_slot':done[-1]['slot_id'] if done else None})
print(json.dumps(result))
