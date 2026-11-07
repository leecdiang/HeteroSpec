from pathlib import Path
import json,hashlib,zipfile,base64,shutil
r=Path(__file__).parent
dest=Path("C:/Users/DIANG/Documents/ChatGPT/HeteroSpec/benchmarks/b570_formal_request_v1")
dest.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
raw=[]
for d in sorted(r.glob("qual-*")):
    if d.is_dir():
        for p in sorted(d.rglob("*.f32")):raw.append({"path":str(p.relative_to(r)).replace("\\","/"),"bytes":p.stat().st_size,"sha256":sha(p)})
(r/"RAW_LOGITS_MANIFEST.json").write_text(json.dumps(raw,indent=2))
with zipfile.ZipFile(r/"FULL_RAW_LOCAL.zip","w",zipfile.ZIP_DEFLATED)as z:
    for x in raw:z.write(r/x["path"],x["path"])
with zipfile.ZipFile(r/"COMPACT_EVIDENCE.zip","w",zipfile.ZIP_DEFLATED)as z:
    for p in sorted(r.rglob("*")):
        rel=p.relative_to(r)
        if p.is_file() and "build"not in rel.parts and p.suffix in (".json",".log",".csv") and p.name not in ("GIT_PAYLOAD.json","PACKAGE_MANIFEST.json","LOCAL_ARCHIVE.json"):
            z.write(p,str(rel))
(r/"LOCAL_ARCHIVE.json").write_text(json.dumps({"full_raw_path":str(r/"FULL_RAW_LOCAL.zip"),"bytes":(r/"FULL_RAW_LOCAL.zip").stat().st_size,"sha256":sha(r/"FULL_RAW_LOCAL.zip"),"raw_files":len(raw),"hosted_on_GitHub":False},indent=2))
for p in sorted(r.iterdir()):
    if p.is_file() and p.suffix in (".json",".md",".cpp",".inc",".py",".ps1",".txt",".csv",".svg",".png",".pdf") and p.name not in ("GIT_PAYLOAD.json","PACKAGE_MANIFEST.json"):
        shutil.copy2(p,dest/p.name)
shutil.copy2(r/"COMPACT_EVIDENCE.zip",dest/"COMPACT_EVIDENCE.zip")
manifest=[{"path":p.name,"bytes":p.stat().st_size,"sha256":sha(p)}for p in sorted(dest.iterdir())if p.is_file()and p.name!="PACKAGE_MANIFEST.json"]
(dest/"PACKAGE_MANIFEST.json").write_text(json.dumps(manifest,indent=2))
payload=[]
for p in sorted(dest.iterdir()):
    if not p.is_file():continue
    b=p.read_bytes()
    binary=p.suffix in (".zip",".png",".pdf")
    payload.append({"path":"benchmarks/b570_formal_request_v1/"+p.name,"encoding":"base64"if binary else"utf-8",
                    "content":base64.b64encode(b).decode()if binary else b.decode("utf-8"),
                    "bytes":len(b),"sha":hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()})
(r/"GIT_PAYLOAD.json").write_text(json.dumps(payload))
print(json.dumps({"files":len(payload),"payload_chars":len((r/"GIT_PAYLOAD.json").read_text()),"raw_files":len(raw),"full_raw_bytes":(r/"FULL_RAW_LOCAL.zip").stat().st_size}))
