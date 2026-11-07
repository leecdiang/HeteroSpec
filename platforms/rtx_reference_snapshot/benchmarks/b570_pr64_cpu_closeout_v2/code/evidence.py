"""Read-only CAS reader and finite CPU stage journal. Never imports model runners."""
import csv, hashlib, json, os, pathlib, sys, datetime

ROOT = pathlib.Path(os.environ.get('HS_CPU_ROOT', 'C:/hs/b570-pr64-cpu-closeout-v2'))
CFG = json.loads((ROOT/'CONFIG.json').read_text(encoding='utf-8-sig'))
RAW = pathlib.Path(CFG['read_only_restore'])
INDEX = json.loads((ROOT/'private/CAS_INDEX.json').read_text(encoding='utf-8'))
OUT = ROOT/'output'
OUT.mkdir(exist_ok=True)
SEEN = {}
def digest(data): return hashlib.sha256(data).hexdigest()
def read(name):
    data=(RAW/name).read_bytes()
    expected=INDEX['files'][name]
    assert len(data)==expected['bytes'] and digest(data)==expected['sha256'], 'CAS mismatch: '+name
    SEEN[name]=expected
    return data
def load(name): return json.loads(read(name))
def check_receipt(name):
    d=load(name)
    for p,h in d['files'].items(): assert digest(read(p))==h, p
    return d
def write(name,obj):
    p=OUT/name; p.parent.mkdir(parents=True,exist_ok=True)
    data=(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
    tmp=p.with_suffix(p.suffix+'.tmp'); tmp.write_bytes(data); tmp.replace(p)
def table(name,rows):
    p=OUT/name; p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader();w.writerows(rows)
def event(kind,**kw):
    row=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),event=kind,**kw)
    with (OUT/'LEDGER.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
def bindings():
    old=OUT/'INPUT_BINDINGS.json'
    if old.exists(): SEEN.update(json.loads(old.read_text())['files'])
    write('INPUT_BINDINGS.json',dict(original_archive=CFG['archive_sha256'],files=SEEN))
def begin(stage):
    event('CPU_START',stage=stage)
    write('STATUS.json',dict(state='RUNNING',stage=stage,new_model_requests=0,new_forward=0,new_warmup=0))
def finish(stage):
    bindings()
    owns={'qualification':['COUNTS.json','QUALIFICATION.json','QUALIFICATION_RECOMPUTED.csv','D_REFERENCE_BINDINGS.json','EXPOSURE_RECHECK.json'],'cross':['CAUSAL_RECHECK.json','CAUSAL_ALL_ROW_SCORES.csv','KV_RECHECK.csv'],'cost_work':['COSTS_RECOMPUTED.csv','COST_TASK_PAIRS.csv','COST_ROUND_PAIRS.csv','WORK_BREAKDOWN.csv','DEVELOPMENT_WORK_CHECK.csv','DEVELOPMENT_TARGET_WORK_CHECK.csv','MATCHED_TARGET_WORK.csv','COST_SUMMARY.json'],'figures':['FIGURE_DATA.json','figures/argmax_cross.svg','figures/argmax_cross.pdf','figures/qualified_speed.svg','figures/qualified_speed.pdf']}
    paths=[OUT/n for n in owns.get(stage,[])];files={p.relative_to(OUT).as_posix():digest(p.read_bytes()) for p in paths if p.exists()}
    unit=OUT/'UNIT_MANIFEST.json'; d=json.loads(unit.read_text()) if unit.exists() else {}
    d[stage]=dict(status='COMPLETE',source_sha256=digest(pathlib.Path(sys.argv[0]).read_bytes()),reader_sha256=digest(pathlib.Path(__file__).read_bytes()),output_hashes=files)
    write('UNIT_MANIFEST.json',d);event('CPU_COMPLETE',stage=stage,source_sha256=d[stage]['source_sha256'],reader_sha256=d[stage]['reader_sha256'],output_hashes=files)
    write('STATUS.json',dict(state='STAGE_COMPLETE',stage=stage,new_model_requests=0,new_forward=0,new_warmup=0))
def endpoint(ids,flags,eog_set,cap=128):
    assert len(ids)==len(flags), 'ID/EOG length'
    assert flags==[x in eog_set for x in ids], 'runtime EOG flags'
    stop=min([i+1 for i,f in enumerate(flags) if f]+[cap])
    assert len(ids)>=stop, 'truncated output before endpoint'
    return dict(ids=ids[:stop],eog=flags[:stop],reason='EOG' if flags[stop-1] else 'CAP')

if __name__=='__main__':
    write('PROTOCOL.json',dict(version='CPU_CLOSEOUT_V2',inputs=CFG,stages=['qualification','cross','cost_work','handoff','figures','verification','seal','delivery'],constraints=['read-only original CAS','no model binaries','additive new directory','no merge'],preparation_failure='Quoted Unicode git ls-tree paths; corrected with -z before numerical parsing. A schema inspection used an incorrect capture path; corrected using receipt files.'))
    write('INPUT_BINDINGS.json',dict(original_archive=CFG['archive_sha256'],files={}))
    write('UNIT_MANIFEST.json',{})
    event('PROTOCOL_FREEZE',version='v2'); write('STATUS.json',dict(state='READY',new_model_requests=0,new_forward=0,new_warmup=0))
