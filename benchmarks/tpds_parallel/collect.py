"""Compact, independently checkable evidence. Raw vectors remain in the attempt trees."""
from pathlib import Path
import gzip
import difflib
import re
import json
import math
import statistics
import shutil
import sys
from panel import HERE,OUT,BASE,ROOT,CFG,OLD,ARMS,read,sha,vectors

E=HERE/"evidence"
E.mkdir(exist_ok=True)
def write(name,obj):
    (E/name).write_text(json.dumps(obj,indent=2)+"\n",encoding="utf8")
def pack(name,data):
    with (E/name).open("wb") as stream:
        with gzip.GzipFile(fileobj=stream,mode="wb",mtime=0) as gz:gz.write(json.dumps(data,separators=(",",":")).encode())

def native_diff():
    paths=["src/llama-graph.cpp","src/llama-kv-cache.h","src/llama-context.cpp","src/hs_reference_batching.hpp","ggml/src/repair_offload.hpp"]
    lines=[];index={}
    for path in paths:
        old=BASE/"source"/path;new=OUT/"source"/path
        index[path]={"PR166":sha(old),"candidate":sha(new)}
        lines+=list(difflib.unified_diff(old.read_text(encoding="utf8").splitlines(True),new.read_text(encoding="utf8").splitlines(True),fromfile="a/"+path,tofile="b/"+path))
    (HERE/"lowering.patch").write_text("".join(lines),encoding="utf8")
    write("sources.json",index)

def mechanism():
    rows=[];raw=[];by_batch={}
    for batch in sorted((ROOT/"probes").iterdir()):
        comparisons=read(batch/"comparison.json")
        for entry in comparisons:
            base,w,arm=[entry[k] for k in ("base","width","arm")]
            cell=batch/f"{base}-{w}-{arm}";log=(cell/"native.log").read_text(encoding="utf8",errors="replace")
            conf=read(cell/"input.json")["units"][0]
            extents=[min(conf["ctx"],256*((base+i)//256+1)) for i in range(w)]
            groups=[]
            for i,e in enumerate(extents):
                if i==0 or e!=extents[i-1]:groups.append(0)
                groups[-1]+=1
            calls=[1]*w if arm in ("S1","oracle") else groups if arm=="WB-cut" else [w]
            tiles=[]
            if arm in ("PQ-ext","QB-local","WB-cut"):
                for size in groups:
                    t=1 if arm=="PQ-ext" else 4
                    tiles.extend([min(t,size-i) for i in range(0,size,t)])
            obs=read(cell/"row/receipt.json") if (cell/"row/receipt.json").exists() else {}
            qk=[x for x in obs.get("nodes",[]) if x["name"]=="kq-0" and x["op"]=="MUL_MAT"]
            proj=[x for x in obs.get("nodes",[]) if x["name"].startswith("tpds_projection")]
            # The scalar oracle's immutable probe predates heavy node capture.
            row=dict(attempt=batch.name,arm=arm,ctx=conf["ctx"],base=base,width=w,exit=entry["exit"],
                mismatch_rows=entry["mismatch"],predicted_calls=calls,predicted_attention_tiles=tiles,physical=obs.get("physical"),actual_calls=obs.get("calls"),
                actual_layer0_qk=[(x["shape"][0],x["shape"][1],x["shape"][3],x["backend"]) for x in qk],
                projection_dispatch=sorted({(x["name"].split(".weight")[0],x["shape"][1],x["backend"]) for x in proj}),
                graph_reuses=obs.get("graphs_reused"),failure_tail=log.splitlines()[-5:] if entry["exit"] else [])
            rows.append(row)
            hashes={f.name:sha(f) for f in (cell/"row").glob("*.f32")}
            raw.append(dict(cell=cell.relative_to(ROOT).as_posix(),input=conf,receipt=obs,exit=read(cell/"exit.json"),vectors=hashes,
                            log_sha256=sha(cell/"native.log"),tiles=re.findall(r"TPDS_TILE [^\r\n]+",log)))
        by_batch[batch.name]=len(comparisons)
    write("mechanism.json",rows);pack("mechanism-raw.json.gz",raw)
    print(by_batch)

def formal():
    root=ROOT/"formal01";items=read(root/"panel.json")
    for name in ("freeze","panel"):shutil.copyfile(root/f"{name}.json",E/f"{name}.json")
    captures=[];timing=[];oracle=[];raw=[]
    def slim(r):return {k:v for k,v in r.items() if k!="geometry"}
    for ctx in (1024,1536):
        qual=root/f"qual-{ctx}"
        aud=read(qual/"audit.json")
        for row in aud:
            captures.append(dict(ctx=ctx,**{k:v for k,v in row.items() if k!="committed_sha256"}))
        for i in range(len(items)):
            d=root/f"oracle-{ctx}"/(f"raw/old/i{i}/heavy" if ctx==1024 else f"i{i}/R/capture")
            rec=read(d.with_suffix(".json") if ctx==1024 else d/"receipt.json")
            oracle.append(dict(ctx=ctx,input=items[i]["id"],vectors=vectors(d,rec),ids=rec["ids"],endpoint={k:rec[k] for k in ("ids","eog","terminal_id","stop_reason","length")}))
            for arm in ARMS:
                d=qual/f"i{i}/{arm}/capture";r=read(d/"receipt.json")
                raw.append(dict(ctx=ctx,input=items[i]["id"],arm=arm,receipt=slim(r),hashes={p.relative_to(d).as_posix():sha(p) for p in d.rglob("*.f32")}))
                for ses in (0,1):
                    for role in ("warm","timed"):
                        p=root/f"cost-{ctx}-s{ses}/i{i}/{arm}/{role}/receipt.json"
                        rec=read(p)
                        timing.append(dict(ctx=ctx,input=items[i]["id"],session=ses,role=role,arm=arm,receipt=rec))
    write("qualification.json",captures);pack("qualification-raw.json.gz",raw);pack("oracles.json.gz",oracle)
    pack("timing-raw.json.gz",timing)
    overhead=[]
    for ctx in (1024,1536):
        for session in (0,1):
            blocks=[r for r in timing if r["ctx"]==ctx and r["session"]==session]
            invocation=read(root/f"cost-{ctx}-s{session}/exit.json")
            measured=sum(r["receipt"]["service_seconds"] for r in blocks if r["role"]=="timed")
            warm=sum(r["receipt"]["service_seconds"] for r in blocks if r["role"]=="warm")
            pool=sum(r["receipt"]["pool_setup_seconds"] for r in blocks if r["role"]=="warm")
            load=blocks[0]["receipt"]["model_load_seconds"]
            overhead.append(dict(ctx=ctx,session=session,process_wall=invocation["elapsed"],model_loading=load,
                pool_setup=pool,warm=warm,measured=measured,remaining_wall=invocation["elapsed"]-load-pool-warm-measured))
    write("complete-cost.json",overhead)

def results():
    import gzip
    timing=json.loads(gzip.decompress((E/"timing-raw.json.gz").read_bytes()))
    def gm(xs):return math.exp(statistics.mean(map(math.log,xs)))
    arms={}
    for arm in ARMS:
        rows=[r for r in timing if r["arm"]==arm and r["role"]=="timed"]
        def column(key):return [r["receipt"][key] for r in rows]
        arms[arm]={k:gm(column(k)) for k in ("service_seconds","prefill_wall_seconds","continuation_wall_seconds","setup_seconds","pool_setup_seconds")}
        arms[arm]["verify_decode_gm"]=gm([r["receipt"]["target_phases"]["VERIFY"] for r in rows]) if arm not in ("R","native-ordinary") else None
    blocks={}
    for r in timing:
        if r["role"]=="timed":blocks.setdefault((r["ctx"],r["input"],r["session"]),{})[r["arm"]]=r["receipt"]["service_seconds"]
    ratios=[]
    for key,b in blocks.items():
        ratios.append(dict(context=key[0],input=key[1],session=key[2],seconds=b,baseline_over_QB={arm:t/b["QB-local"] for arm,t in b.items()}))
    write("cost.json",dict(gm_seconds=arms,blocks=ratios,ratios={a:gm([r["baseline_over_QB"][a] for r in ratios]) for a in ARMS},
        sessions={a:[gm([r["baseline_over_QB"][a] for r in ratios if r["session"]==s]) for s in (0,1)] for a in ARMS},
        warmup_seconds=sum(r["receipt"]["service_seconds"] for r in timing if r["role"]=="warm"),measured_seconds=sum(r["receipt"]["service_seconds"] for r in timing if r["role"]=="timed")))
if __name__=="__main__":
    if sys.argv[1]=="mechanism":native_diff();mechanism()
    else:formal();results()

