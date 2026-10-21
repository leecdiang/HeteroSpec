from pathlib import Path
import json, hashlib, zipfile, shutil, base64
b=Path("C:/hs/b570-spec-bridge-20261020200000")
c=Path(__file__).parent
repo=Path("C:/Users/DIANG/Documents/ChatGPT/HeteroSpec")
def dump(p,x): p.write_text(json.dumps(x,indent=2),encoding="utf-8")
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
raw=[{"path":str(p.relative_to(b)).replace("\\","/"),"bytes":p.stat().st_size,"sha256":digest(p)} for p in sorted((b/"results").rglob("*.f32"))]
assert len(raw)==78
dump(b/"RAW_LOGITS_MANIFEST.json",raw)
with zipfile.ZipFile(b/"FULL_RAW_LOCAL.zip","w",zipfile.ZIP_DEFLATED) as z:
    for row in raw: z.write(b/row["path"],row["path"])
with zipfile.ZipFile(b/"SOURCE_SNAPSHOT.zip","w",zipfile.ZIP_DEFLATED) as z:
    for p,n in [(b/"llama-graph.cpp","candidate/llama-graph.cpp"),(b/"spec_bridge.cpp","candidate/spec_bridge.cpp"),
                (Path("C:/hs/b570-direct-id-v1-src/src/llama-graph.cpp"),"original/llama-graph.cpp"),
                (Path("C:/hs/b570-query-head-lowering/benchmarks/b570_query_head_lowering_v1/native/query_head.h"),"query_head.h")]:
        z.write(p,n)
for root,sub in [(b,"b570_spec_request_bridge_v1"),(c,"b570_spec_request_cost_v1")]:
    with zipfile.ZipFile(root/"COMPACT_EVIDENCE.zip","w",zipfile.ZIP_DEFLATED) as z:
        for p in sorted(root.rglob("*")):
            rel=p.relative_to(root)
            if p.is_file() and "build" not in rel.parts and p.suffix in (".json",".log") and p.name not in ("GIT_PAYLOAD.json","PACKAGE_MANIFEST.json"):
                z.write(p,str(rel))
    dest=repo/"benchmarks"/sub
    dest.mkdir(parents=True,exist_ok=True)
    for p in sorted(root.iterdir()):
        if p.is_file() and p.name not in ("FULL_RAW_LOCAL.zip","GIT_PAYLOAD.json","PACKAGE_MANIFEST.json","QUALIFIED_REFERENCE.json","llama-graph.cpp") and p.suffix in (".md",".json",".py",".ps1",".cpp",".txt",".patch",".zip"):
            shutil.copy2(p,dest/p.name)
    manifest=[{"path":p.name,"bytes":p.stat().st_size,"sha256":digest(p)}for p in sorted(dest.iterdir()) if p.is_file() and p.name!="PACKAGE_MANIFEST.json"]
    dump(dest/"PACKAGE_MANIFEST.json",manifest)
payload=[]
for sub in ("b570_spec_request_bridge_v1","b570_spec_request_cost_v1"):
    for p in sorted((repo/"benchmarks"/sub).iterdir()):
        data=p.read_bytes()
        payload.append({"path":f"benchmarks/{sub}/{p.name}","encoding":"base64" if p.suffix==".zip" else "utf-8",
            "content":base64.b64encode(data).decode() if p.suffix==".zip" else data.decode("utf-8"),
            "bytes":len(data),"sha":hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()})
dump(c/"GIT_PAYLOAD.json",payload)
print(json.dumps({"files":len(payload),"payload_bytes":(c/"GIT_PAYLOAD.json").stat().st_size,"local_raw_archive_bytes":(b/"FULL_RAW_LOCAL.zip").stat().st_size}))
