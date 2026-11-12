from pathlib import Path
import sqlite3,json
HERE=Path(__file__).resolve().parent
db=sqlite3.connect('file:'+str((HERE/'private/codex.db').resolve()).replace('\\','/')+'?mode=ro',uri=True)
db.row_factory=sqlite3.Row
rows=[dict(x) for x in db.execute('select * from local_thread_catalog where lower(display_title) like ? or lower(cwd) like ? or display_title like ? or display_title like ?',('%heterospec%','%heterospec%','%#223%','%#221%'))]
out={'integrity':db.execute('pragma quick_check').fetchone()[0],'catalog_stats':dict(zip(('count','latest_source_updated'),db.execute('select count(*),max(source_updated_at) from local_thread_catalog').fetchone())),'relevant_threads':rows}
ids=[x['thread_id'] for x in rows]
out['relevant_active_turns']=[dict(x) for i in ids for x in db.execute('select thread_id,launch_id,observed_at_ms from active_chat_turns where thread_id=?',(i,))]
out['active_turn_count']=db.execute('select count(*) from active_chat_turns').fetchone()[0]
out['sync_state']=[dict(x) for x in db.execute('select * from local_thread_catalog_sync_state')]
(HERE/'private/CATALOG_MATCHES.json').write_text(json.dumps(out,indent=2),encoding='utf8')
view={k:v for k,v in out.items() if k!='relevant_threads'}
view['relevant_threads']=[{k:x[k] for k in ('host_id','thread_id','display_title','source_updated_at','cwd','source_kind','chatgpt_async_status')} for x in rows]
print(json.dumps(view,indent=2,ensure_ascii=True))
