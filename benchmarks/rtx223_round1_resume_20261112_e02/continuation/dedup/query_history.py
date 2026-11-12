from pathlib import Path
import sqlite3,json,datetime
HERE=Path(__file__).resolve().parent
db=sqlite3.connect('file:'+str((HERE/'private/thread_history_1.sqlite').resolve()).replace('\\','/')+'?mode=ro',uri=True)
db.row_factory=sqlite3.Row
stats=dict(zip(('turns','latest_started','latest_completed'),db.execute('select count(*),max(started_at),max(completed_at) from thread_turns').fetchone()))
needles=['rtx221-round1-20261112','af436df989570ad882db65bd8a4b265b9e8cfdae','PR #223','Prompt 1','bc78721363f01ae8f36dd7b1d32c89b8c9e26cea']
matches=[]
for n in needles:
    rows=db.execute('select thread_id,turn_id,item_id,created_at_ms,item_type,item_json from thread_items where instr(item_json,?)>0',(n,)).fetchall()
    for row in rows:
        x=dict(row);raw=x.pop('item_json');x['needle']=n;x['excerpt']=raw[max(0,raw.find(n)-80):raw.find(n)+len(n)+120];matches.append(x)
(HERE/'private/history_matches.json').write_text(json.dumps(matches,indent=2),encoding='utf8')
print(json.dumps({'stats':stats,'matched_items':len(matches),'matches':matches[:20]},indent=2,ensure_ascii=True))
g=Path('C:/Users/ASUS/.codex/.codex-global-state.json')
data=json.loads(g.read_bytes())
print(json.dumps({'global_state_top_keys':list(data)},indent=2))
