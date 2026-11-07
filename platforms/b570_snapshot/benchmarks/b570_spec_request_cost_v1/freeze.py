from pathlib import Path
import hashlib,json,shutil
r=Path(__file__).parent;p=Path("C:/hs/b570-spec-bridge-20261020200000")
def sha(p):
    h=hashlib.sha256()
    with p.open("rb")as f:
        for b in iter(lambda:f.read(4*1024*1024),b""):h.update(b)
    return h.hexdigest()
prior=json.loads((p/"BUILD_MANIFEST.json").read_text())
for f in prior["files"]:assert sha(Path(f["path"]))==f["sha256"],f["path"]
for f in (p/"build/Release").glob("*.dll"):shutil.copy2(f,r/"build/Release"/f.name)
files=[r/n for n in ("spec_cost.cpp","CMakeLists.txt","PREREGISTRATION.json","INPUT.json","QUALIFIED_REFERENCE.json","MODEL_IDENTITY.json","RUN.ps1")]
files+=list((r/"build/Release").glob("*.dll"))+list((r/"build/Release").glob("*.exe"))
files+=[Path(x["path"])for x in json.loads((r/"MODEL_IDENTITY.json").read_text())]
(r/"BUILD_MANIFEST.json").write_text(json.dumps({"files":[{"path":str(f),"bytes":f.stat().st_size,"sha256":sha(f)}for f in files]},indent=2))
print("Frozen",len(files),"cost inputs; all219 bridge inputs unchanged")
