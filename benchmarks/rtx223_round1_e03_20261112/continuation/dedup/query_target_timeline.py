from pathlib import Path
import sqlite3,json
HERE=Path(__file__).resolve().parent
ids=['6af3f9e3-1098-83e8-8945-7a1ed4d3611c','6af56d1b-2528-83e8-8b52-17f91f08d8bb']
db=sqlite3.connect('file:'+str((HERE/'private/codex.db').resolve()).replace('\\','/')+'?mode=ro',uri=True)
db.row_factory=sqlite3.Row
out=[]
for tid in ids:
    rows=[dict(x) for x in db.execute('select host_id,thread_id,sequence,record_id,payload_json from thread_timeline_ledger where thread_id=? order by sequence',(tid,))]
    for r in rows:r['payload']=json.loads(r.pop('payload_json'))
    cat=[dict(x) for x in db.execute('select * from local_thread_catalog where thread_id=?',(tid,))]
    out.append({'thread_id':tid,'catalog':cat,'records':rows})
(HERE/'private/TARGET_TIMELINES.json').write_text(json.dumps(out,indent=2),encoding='utf8')
for item in out:
    print(json.dumps({'thread_id':item['thread_id'],'catalog':item['catalog'],'records':item['records'][-10:]},ensure_ascii=True,indent=2))
