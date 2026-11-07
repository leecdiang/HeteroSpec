from pathlib import Path
import json,hashlib,gzip,zipfile,shutil,base64
r=Path(__file__).parent;p=Path("C:/hs/b570-gqa-admission-20261020184000")
def sha(b):return hashlib.sha256(b).hexdigest()
with zipfile.ZipFile(r/"RAW_EVIDENCE.zip","w",zipfile.ZIP_DEFLATED,9) as z:
    for f in sorted((r/"results").rglob("*")):
        if f.is_file():z.write(f,f.relative_to(r).as_posix())
with zipfile.ZipFile(r/"RAW_EVIDENCE.zip") as z:
    for n in z.namelist():assert z.read(n)==(r/n).read_bytes()
with zipfile.ZipFile(r/"SOURCE_SNAPSHOT.zip","w",zipfile.ZIP_DEFLATED,9) as z:
    z.write(p/"ggml-vulkan.cpp","parent/ggml-vulkan.cpp")
    z.write(r/"ggml-vulkan.cpp","candidate/ggml-vulkan.cpp")
    z.write("C:/hs/b570-query-head-lowering/benchmarks/b570_query_head_lowering_v1/native/query_head.h","query_head.h")
    z.write("C:/hs/llama-b10839/ggml/src/ggml-vulkan/vulkan-shaders/mul_mat_vec_nc.comp","mul_mat_vec_nc.comp")
manifest={"root":str(r),"files":[]}
for f in sorted(r.rglob("*")):
    if f.is_file() and f.name not in ("FINAL_MANIFEST.json.gz","FINAL_MANIFEST.sha256","GIT_PAYLOAD.json"):
        b=f.read_bytes();manifest["files"].append({"path":f.relative_to(r).as_posix(),"bytes":len(b),"sha256":sha(b)})
mb=(json.dumps(manifest,indent=2)+"\n").encode()
(r/"FINAL_MANIFEST.json.gz").write_bytes(gzip.compress(mb,mtime=0))
(r/"FINAL_MANIFEST.sha256").write_text(sha(mb)+"\n")
names=["RESULT.md","PREREGISTRATION.json","gqa.cpp","av-preserve.patch","CMakeLists.txt","RUN.ps1","prepare.py","freeze.py",
       "analyze.py","package.py","CPU_ADDRESS_CHECK.json","CPU_RECHECK.json","BUILD_MANIFEST.json","PROCESS_RECEIPT.json",
       "BUDGET_LEDGER.json","stdout.log","stderr.log","configure.log","build.log","RAW_EVIDENCE.zip","SOURCE_SNAPSHOT.zip",
       "FINAL_MANIFEST.json.gz","FINAL_MANIFEST.sha256"]
dst=Path("C:/Users/DIANG/Documents/ChatGPT/HeteroSpec/benchmarks/b570_gqa_av_preserve_v1")
dst.mkdir(exist_ok=False)
payload=[]
for n in names:
    f=r/n;b=f.read_bytes();shutil.copy2(f,dst/n);binary=n.endswith((".zip",".gz"))
    payload.append({"path":"benchmarks/b570_gqa_av_preserve_v1/"+n,"bytes":len(b),
                    "git_blob_sha":hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest(),
                    "encoding":"base64" if binary else "utf-8","content":base64.b64encode(b).decode() if binary else b.decode("utf-8")})
(r/"GIT_PAYLOAD.json").write_text(json.dumps(payload,ensure_ascii=True))
print(json.dumps({"files":len(names),"raw_archive_bytes":(r/"RAW_EVIDENCE.zip").stat().st_size,
                  "manifest_entries":len(manifest["files"]),"manifest_sha256":sha(mb)}))
