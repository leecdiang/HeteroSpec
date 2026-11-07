"""Reduce native receipts, preserving full kernel activities and digest identities."""
from collections import Counter
import difflib,gzip,math,statistics,sys
from host import *
from matrix import ARMS,CELLS
E=HERE/"evidence";E.mkdir(exist_ok=True)
def save(name,data):
    s=json.dumps(data,indent=None if name.endswith(".gz") else 2).encode()
    (E/name).write_bytes(gzip.compress(s,mtime=0) if name.endswith(".gz") else s)
def gpu_summary(events):
    kernels=[e for e in events if e["kind"]=="kernel"];copies=[e for e in events if e["kind"]=="copy"]
    return dict(kernels=len(kernels),kernel_ms=sum(x["end"]-x["start"] for x in kernels)*1e-6,copies=len(copies),
        transfer_bytes=sum(x["bytes"] for x in copies),transfer_ms=sum(x["end"]-x["start"] for x in copies)*1e-6)
def ops():
    data=[];gpu={};sample={}
    for m in ("0.6B","8B"):
        raw=ROOT/("witness-"+m)/"native";r=read(raw/"receipt.json")
        for op in r["nodes"]:
            name=op["weight"]["name"];folder=raw/name;rep=ROOT/("replay-"+m)/name;rows=[]
            for width in (2,4,8,16,32):
                a=rep/f"{width}-scalar.bin";base=sha(a)
                for route in ["scalar","wide","tile"]+(["packed"] if width>=8 else []):
                    key=f"{width}-{route}";v=read(rep/(key+".json"));digest=sha(rep/(key+".bin"))
                    row=dict(q=width,route=route,sha=digest,scalar_equal=digest==base,**v)
                    if m=="8B":
                        tr=read(ROOT/"profile-replay01"/name/(key+"-gpu.json"))
                        gpu[name+"/"+key]=tr;row["activity"]=gpu_summary(tr)
                    rows.append(row)
            assert sha(folder/"output.bin")==sha(rep/"32-wide.bin")
            data.append(dict(model=m,descriptor=op,inputs={key:sha(folder/(key+".bin")) for key in ("input","weight","output")},routes=rows))
            if m=="8B" and name in ("blk.0.attn_q.weight","blk.0.ffn_down.weight"):
                import base64
                sample[name]={key:base64.b64encode(path.read_bytes()).decode() for key,path in [("input",folder/"input.bin"),("live32",folder/"output.bin"),("scalar32",rep/"32-scalar.bin"),("packed32",rep/"32-packed.bin"),("native8",rep/"8-wide.bin")]}
    save("operands.json.gz",data);save("operator-activities.json.gz",gpu);save("operand-sample.json.gz",sample)
    save("first-divergence.json",read(ROOT/"first-divergence.json"))
def matrix_qual():
    plan=read(ROOT/"matrix.json");save("matrix-plan.json",plan);save("prefixes.json",[{**read(p/"receipt.json"),"sha256":sha(ROOT/f"state-{p.name[1:]}.bin")} for p in (ROOT/"prefix01").iterdir() if p.is_dir()])
    save("matrix-vectors.json.gz",read(ROOT/"matrix-qual.json"))
    geometries=[];prof={};raw={}
    for i,(b,q,h,cross) in enumerate(CELLS):
        for arm in ARMS:
            new=arm.startswith("new");name=f"c{i}-{arm}"
            r=read(ROOT/("qual-new-driver" if new else "qual-capture01")/name/"receipt.json")
            raw[name]=r;tr=read(ROOT/f"profile-{int(new)}"/name/"gpu.json");prof[name]=tr
            obs=r["nodes"];qk=[s["tensor"]["ne"] for s in obs if s["tensor"]["name"]=="kq-0"];av=[s["tensor"]["ne"] for s in obs if s["tensor"]["name"]=="kqv-0"]
            predicted=[1]*q if arm=="S1" else [3,q-3] if cross and "WB" in arm else [q]
            groups=[3,q-3] if cross else [q]
            tiles=[1]*q if arm=="S1" else [min(4,g-j) for g in groups for j in range(0,g,4)]
            assert r["padding"]==256 and r["calls"]==predicted and [s[3] for s in qk]==tiles and [s[3] for s in av]==tiles
            row=0
            for extent,_,_,w in qk:
                assert extent==256*((h+row)//256+1);row+=w
            mem=Counter()
            for s in obs:
                if s["op"] in ("CONCAT","CPY","CONT"):mem[s["op"]]+=s["tensor"]["bytes"]
            proj=[dict(name=s["tensor"]["name"],ne=s["tensor"]["ne"]) for s in obs if s["op"]=="MUL_MAT" and s["tensor"]["name"] not in ("kq-0","kqv-0")]
            geometries.append(dict(cell=i,arm=arm,head=h,width=q,cross=cross,predicted_calls=predicted,actual_calls=r["calls"],attention=tiles,qk=qk,av=av,
                projection_layer0=proj,graph_builds=r["physical"]-r["reuse"],reused=r["reuse"],logical_output_bytes=mem,**gpu_summary(tr)))
    save("coordinates.json",geometries);save("graph-observations.json.gz",raw);save("append-activities.json.gz",prof)
def costs():
    output=[];plan=read(ROOT/"matrix.json")["plan"]
    for row in plan:
        d=ROOT/"cost"/row["id"];assert read(d/"exit.json")["code"]==0
        output.append(dict(**row,warm=read(d/"warm/receipt.json"),measured=read(d/"measured/receipt.json"),model_load=read(d/"load.json")["seconds"],process_wall=read(d/"exit.json")["elapsed"]))
    save("append-cost.json.gz",output)
def natural_results():
    n=ROOT/"natural01";save("natural-freeze.json",read(n/"freeze.json"));save("natural-inputs.json",read(n/"inputs.json"));save("natural-qualification.json.gz",read(n/"qualification.json"))
    captures={}
    for tag in ("reference","historical","changed"):
        for path in (n/tag).glob("i*/*/capture/receipt.json"):
            r=read(path)
            captures[path.parent.relative_to(n).as_posix()]={k:v for k,v in r.items() if k!="geometry"}
    save("natural-transactions.json.gz",captures)
    output=[]
    for session in read(n/"freeze.json")["order"]:
        for row in session:
            i,s,arm=row["index"],row["session"],row["arm"];d=n/f"cost-s{s}-i{i}-{arm}"
            output.append(dict(**row,warm=read(d/f"i{i}/{arm}/warm/receipt.json"),measured=read(d/f"i{i}/{arm}/measured/receipt.json"),process_wall=read(d/"exit.json")["elapsed"]))
    save("service-cost.json.gz",output)
def sources():
    file="src/llama-graph.cpp"
    src=FROZEN/"source"/file;dst=ROOT/"candidate01/source"/file
    diff=difflib.unified_diff(src.read_text(encoding="utf8").splitlines(True),dst.read_text(encoding="utf8").splitlines(True),"a/"+file,"b/"+file)
    (HERE/"packed.patch").write_text("".join(diff),encoding="utf8")
    def gpu_info():return subprocess.check_output(["nvidia-smi","--query-gpu=name,uuid,driver_version,compute_cap","--format=csv,noheader"],text=True).strip()
    save("bindings.json",dict(gpu=gpu_info(),frozen_graph=sha(src),candidate_graph=sha(dst),frozen_core=sha(FROZEN/"core/src/libllama.a"),candidate_core=sha(ROOT/"candidate01/core/src/libllama.a"),
        compiler_builds={p.parent.name:read(p) for p in ROOT.glob("*/build.json")},ggml_cuda=sha(FROZEN/"bin/ggml-cuda.dll"),
        cuda_sources={n:sha(FROZEN/"source/ggml/src/ggml-cuda"/n) for n in ("ggml-cuda.cu","mmvq.cu","mmvq.cuh","mmq.cu","quantize.cu")},historical_freeze_sha256=sha(FROZEN.parent/"formal01/freeze.json"),sdk={p.name:sha(p) for p in (ROOT/"profiler").glob("*.whl")},service=read(ROOT/"new-driver/service-build.json"),
        failed_builds={p: dict(log_sha256=sha(ROOT/p/"worker.log"),errors=[l for l in (ROOT/p/"worker.log").read_text(errors="replace").splitlines() if "error:" in l][:6]) for p in ("prof01","prof02") if (ROOT/p/"worker.log").exists()}))
if __name__=="__main__":
    for name in sys.argv[1:]:globals()[name]()

