"""Source-bound native civil-clock load/admission windows, not GPU kernel timing."""
import pathlib,sys,json,datetime
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from protocol import read_json,file_sha,write_new
rows=[];slots={s['slot']:s for s in read_json(ROOT/'p0/PLAN_P1.json')['slots']}
for p in sorted((ROOT/'_host/run').glob('*/stdout.jsonl')):
 events=[json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()];a=[x for x in events if x.get('event')=='MEMORY' and x.get('point')=='BEFORE_LOAD'];b=[x for x in events if x.get('event')=='MEMORY' and x.get('point')=='LOADED'];assert len(a)==len(b)==1 and a[0]['pid']==b[0]['pid'];start=datetime.datetime.fromisoformat(a[0]['timestamp_utc']);end=datetime.datetime.fromisoformat(b[0]['timestamp_utc']);ms=(end-start).total_seconds()*1000;assert ms>=0;s=slots[p.parent.name];rows.append(dict(slot=s['slot'],task=s['task'],arm=s['arm'],mode=s['mode'],pid=a[0]['pid'],begin_utc=a[0]['timestamp_utc'],end_utc=b[0]['timestamp_utc'],observed_admission_window_ms=ms,raw_stdout_sha256=file_sha(p)))
write_new(ROOT/'p1/LOAD_ADMISSION_WINDOWS.json',dict(scope='Native BEFORE_LOAD to LOADED civil UTC timestamps; backend initialization, model/context allocation and vocabulary guard. GPU discovery before BEFORE_LOAD is excluded. Not pure model I/O, GPU completed time or exclusive stage decomposition.',rows=rows,window_count=len(rows),minimum_ms=min(x['observed_admission_window_ms'] for x in rows),maximum_ms=max(x['observed_admission_window_ms'] for x in rows),native_starts_added=0))
print(json.dumps(dict(windows=len(rows),min_ms=min(x['observed_admission_window_ms'] for x in rows),max_ms=max(x['observed_admission_window_ms'] for x in rows))))
