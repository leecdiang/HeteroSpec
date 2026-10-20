from pathlib import Path
import hashlib,json,zipfile,shutil,gzip,base64
r=Path(__file__).parent
def h(b):return hashlib.sha256(b).hexdigest()
with zipfile.ZipFile(r/"RAW_EVIDENCE.zip","w",zipfile.ZIP_DEFLATED,9) as z:
    for p in sorted((r/"results").rglob("*")):
        if p.is_file():z.write(p,p.relative_to(r).as_posix())
with zipfile.ZipFile(r/"RAW_EVIDENCE.zip") as z:
    for n in z.namelist():assert z.read(n)==(r/n).read_bytes()
with zipfile.ZipFile(r/"SOURCE_SNAPSHOT.zip","w",zipfile.ZIP_DEFLATED,9) as z:
    z.write(r/"ggml-vulkan.cpp","candidate/ggml-vulkan.cpp")
    z.write("C:/hs/b570-model-profile-final-20261020164000/ggml-vulkan.cpp","parent/ggml-vulkan.cpp")
    z.write("C:/hs/b570-query-head-lowering/benchmarks/b570_query_head_lowering_v1/native/query_head.h","query_head.h")
    sd=Path("C:/hs/llama-b10839/ggml/src/ggml-vulkan/vulkan-shaders")
    for n in ("mul_mat_vec_nc.comp","mul_mat_vec.comp","mul_mat_vec_base.glsl","mul_mat_vec_iface.glsl"):
        z.write(sd/n,"shader-text/"+n)
# Preserve the exact PR129 geometry metadata used for E0; no raw model logits needed.
shutil.copy2("C:/hs/b570-model-profile-final-20261020164000/session-0/result.json",r/"PARENT_MODEL_GEOMETRY.json")
manifest={"root":str(r),"files":[]}
for p in sorted(r.rglob("*")):
    if p.is_file() and p.name not in {"FINAL_MANIFEST.json.gz","FINAL_MANIFEST.sha256","GIT_PAYLOAD.json"}:
        b=p.read_bytes();manifest["files"].append({"path":p.relative_to(r).as_posix(),"bytes":len(b),"sha256":h(b)})
mb=(json.dumps(manifest,indent=2)+"\n").encode()
(r/"FINAL_MANIFEST.json.gz").write_bytes(gzip.compress(mb,mtime=0))
(r/"FINAL_MANIFEST.sha256").write_text(h(mb)+"\n")
names=["RESULT.md","E0_HANDOFF.md","PREREGISTRATION.json","gqa.cpp","gqa-scoped.patch","CMakeLists.txt","RUN.ps1",
       "prepare.py","freeze.py","analyze.py","package.py","CPU_RECHECK.json","BUILD_MANIFEST.json","PROCESS_RECEIPT.json",
       "BUDGET_LEDGER.json","stdout.log","stderr.log","configure.log","build.log","host-final-build.log",
       "PARENT_MODEL_GEOMETRY.json","RAW_EVIDENCE.zip","SOURCE_SNAPSHOT.zip","FINAL_MANIFEST.json.gz","FINAL_MANIFEST.sha256"]
dst=Path("C:/Users/DIANG/Documents/ChatGPT/HeteroSpec/benchmarks/b570_gqa_admission_v1")
dst.mkdir(exist_ok=False)
payload=[]
for n in names:
    p=r/n;b=p.read_bytes();shutil.copy2(p,dst/n);binary=n.endswith((".zip",".gz"))
    payload.append({"path":"benchmarks/b570_gqa_admission_v1/"+n,"bytes":len(b),
                    "git_blob_sha":hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest(),
                    "encoding":"base64" if binary else "utf-8","content":base64.b64encode(b).decode() if binary else b.decode("utf-8")})
(r/"GIT_PAYLOAD.json").write_text(json.dumps(payload,ensure_ascii=True),encoding="utf-8")
print(json.dumps({"files":len(names),"manifest_entries":len(manifest["files"]),"manifest_sha256":h(mb),
                  "raw_archive_bytes":(r/"RAW_EVIDENCE.zip").stat().st_size,"payload_bytes":(r/"GIT_PAYLOAD.json").stat().st_size}))
