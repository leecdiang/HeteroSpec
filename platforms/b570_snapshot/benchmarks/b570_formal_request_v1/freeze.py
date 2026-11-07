from pathlib import Path
import json,hashlib,shutil
r=Path(__file__).parent
p=Path("C:/hs/b570-spec-bridge-20261020200000")
def sha(p):
    h=hashlib.sha256()
    with p.open("rb")as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b""):h.update(chunk)
    return h.hexdigest()
prior=json.loads((p/"BUILD_MANIFEST.json").read_text())
for f in prior["files"]:assert sha(Path(f["path"]))==f["sha256"],f["path"]
for f in (p/"build/Release").glob("*.dll"):shutil.copy2(f,r/"build/Release"/f.name)
paths=[r/n for n in ("formal.cpp","main.cpp.inc","prepare.py","setup.py","CMakeLists.txt","INPUT_PANEL.json","MODEL_IDENTITY.json","PREREGISTRATION.json","RUN.ps1","recheck.py")]
paths+=list((r/"build/Release").glob("*.exe"))+list((r/"build/Release").glob("*.dll"))
paths+=[Path(x["path"])for x in json.loads((r/"MODEL_IDENTITY.json").read_text())]
paths+=[p/"results/result.json"]
(r/"BUILD_MANIFEST.json").write_text(json.dumps({"prior_219_inputs_verified":True,"files":[{"path":str(x),"bytes":x.stat().st_size,"sha256":sha(x)}for x in paths]},indent=2))
print("Frozen",len(paths),"inputs. Prior219 unchanged.")
