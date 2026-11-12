from pathlib import Path
import sqlite3,json,datetime,hashlib,shutil
HERE=Path(__file__).resolve().parent
PRIVATE=HERE/'private'
db=sqlite3.connect('file:'+str((PRIVATE/'state_5.sqlite').resolve()).replace('\\','/')+'?mode=ro',uri=True)
db.row_factory=sqlite3.Row
rows=[dict(x) for x in db.execute('select id,rollout_path,created_at,updated_at,source,cwd,title,archived,git_sha,git_branch,preview,first_user_message from threads where cwd like ? or title like ? or git_origin_url like ?',('%HeteroSpec%','%HeteroSpec%','%leecdiang/HeteroSpec%'))]
(PRIVATE/'relevant_threads.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
print(json.dumps([{k:x[k] for k in ('id','rollout_path','updated_at','source','cwd','title','archived','git_branch')} for x in rows],ensure_ascii=True,indent=2))
db.close()
