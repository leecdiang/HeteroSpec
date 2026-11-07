"""CPU-only compact Git delivery; preserves all full raw files locally."""
import pathlib,json,hashlib,zipfile,gzip,shutil,base64
root=pathlib.Path(__file__).parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
native=[root/name for name in ["configure.log","build.log"]]
for s in range(3):
    native += [root/f"session-{s}"/name for name in ["result.json","timing.jsonl"]]
    native += [root/f"session-{s}.{name}" for name in ["stdout.log","stderr.log","PROCESS_RECEIPT.json"]]
with zipfile.ZipFile(root/"NATIVE_EVIDENCE.zip","w",compression=zipfile.ZIP_DEFLATED) as z:
    for p in native:z.write(p,p.relative_to(root).as_posix())
with zipfile.ZipFile(root/"NATIVE_EVIDENCE.zip") as z:
    assert len(z.namelist())==len(native)
    for p in native:assert z.read(p.relative_to(root).as_posix())==p.read_bytes()
pointer={
 "raw_root":str(root),"raw_delivered_to_github":False,
 "compact_archive":"NATIVE_EVIDENCE.zip","archive_files":len(native),"archive_roundtrip_byte_verified":True,
 "prior_raw_root":"C:/hs/b570-qb-aa-balanced-20261020065000",
 "runtime_sha256":"79b0031bea367da64a8f580f1b00fe1108c83cc2ab73e893739d9740e4408423",
 "manifest_policy":"Hashes all session raw files, root documentation/scripts/figures/compact ZIP, and three release binaries. Excludes build intermediates, Git payload and manifest self/hash/gzip to avoid circularity. External compile inputs are additionally listed in BUILD_MANIFEST.json.",
}
(root/"EVIDENCE_POINTERS.json").write_text(json.dumps(pointer,indent=2)+"\n")
excluded={"FINAL_MANIFEST.json","FINAL_MANIFEST.json.gz","FINAL_MANIFEST.sha256","GIT_PAYLOAD.json"}
files=[p for p in root.iterdir() if p.is_file() and p.name not in excluded]
files += [p for s in range(3) for p in (root/f"session-{s}").rglob("*") if p.is_file()]
files += [root/"build/Release"/name for name in ["transaction.exe","ggml-base.dll","ggml-vulkan.dll"]]
manifest={"scope":pointer["manifest_policy"],"artifact_count":len(files),"files":[
 {"path":p.relative_to(root).as_posix(),"bytes":p.stat().st_size,"sha256":sha(p)} for p in sorted(files)]}
data=(json.dumps(manifest,indent=2)+"\n").encode()
(root/"FINAL_MANIFEST.json").write_bytes(data)
(root/"FINAL_MANIFEST.json.gz").write_bytes(gzip.compress(data,mtime=0))
digest=sha(root/"FINAL_MANIFEST.json")
(root/"FINAL_MANIFEST.sha256").write_text(digest+"  FINAL_MANIFEST.json\n")
names=["transaction.cpp","CMakeLists.txt","RUN_ALL.ps1","PREREGISTRATION.json","BUILD_MANIFEST.json",
 "analyze.py","verify_raw.py","closeout.py","package.py","ANALYSIS.json","RESIDENT_ANALYSIS.json",
 "BLOCK_MEANS.csv","BUDGET_LEDGER.json","CPU_RAW_RECHECK.json","REFERENCE_CONTINUITY.json",
 "RESULT_SUMMARY.json","RESULT.md","PAPER_INTEGRATION.md","MAPPING_COSTS.svg",
 "NATIVE_EVIDENCE.zip","EVIDENCE_POINTERS.json","FINAL_MANIFEST.json.gz","FINAL_MANIFEST.sha256"]
dest=pathlib.Path("C:/Users/DIANG/Documents/ChatGPT/HeteroSpec/benchmarks/b570_qb_batch_broadcast_v1/transaction_v1")
dest.mkdir(exist_ok=False)
payload=[]
for name in names:
    p=root/name;b=p.read_bytes();binary=name.endswith((".gz",".zip"))
    shutil.copyfile(p,dest/name)
    payload.append({"name":name,"path":"benchmarks/b570_qb_batch_broadcast_v1/transaction_v1/"+name,
     "binary":binary,"content":base64.b64encode(b).decode() if binary else b.decode(),
     "bytes":len(b),"sha256":hashlib.sha256(b).hexdigest(),"git_blob_sha":hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()})
(root/"GIT_PAYLOAD.json").write_text(json.dumps(payload))
print(json.dumps({"files":len(payload),"delivery_bytes":sum(x["bytes"] for x in payload),"manifest_artifacts":len(files),"manifest_sha256":digest}))
