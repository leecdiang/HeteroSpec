from pathlib import Path
import hashlib,json,shutil
r=Path(__file__).parent;p=Path("C:/hs/b570-formal-request-20261020")
def sha(p):
    h=hashlib.sha256()
    with p.open("rb")as f:
        for b in iter(lambda:f.read(8*1024*1024),b""):h.update(b)
    return h.hexdigest()
for f in json.loads((p/"BUILD_MANIFEST.json").read_text())["files"]:assert sha(Path(f["path"]))==f["sha256"],f["path"]
for f in json.loads((p/"RAW_LOGITS_MANIFEST.json").read_text()):assert sha(p/f["path"])==f["sha256"],f["path"]
for f in (p/"build/Release").glob("*.dll"):shutil.copy2(f,r/"build/Release"/f.name)
paths=[r/n for n in ("prefill_submit.cpp","main.cpp.inc","prepare.py","setup.py","CMakeLists.txt","INPUT_PANEL.json","MODEL_IDENTITY.json","PREREGISTRATION.json","RUN.ps1","recheck.py")]
paths+=list((r/"build/Release").glob("*.dll"))+list((r/"build/Release").glob("*.exe"))
paths+=[Path(x["path"])for x in json.loads((r/"MODEL_IDENTITY.json").read_text())]
paths+=[p/f"qual-{i}/result.json"for i in range(4)]+[p/"RAW_LOGITS_MANIFEST.json",Path("C:/hs/b570-spec-bridge-20261020200000/results/result.json")]
(r/"BUILD_MANIFEST.json").write_text(json.dumps({"parent_19_inputs_and_914_raw_files_verified":True,"files":[{"path":str(x),"bytes":x.stat().st_size,"sha256":sha(x)}for x in paths]},indent=2))
print("Frozen",len(paths),"inputs; parent inputs and all914 raw vectors unchanged")
