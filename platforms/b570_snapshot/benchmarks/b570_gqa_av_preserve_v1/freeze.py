from pathlib import Path
import json,hashlib,shutil
r=Path(__file__).parent
prior=Path("C:/hs/b570-gqa-admission-20261020184000")
for entry in json.loads((prior/"BUILD_MANIFEST.json").read_text())["files"]:
    assert hashlib.sha256(Path(entry["path"]).read_bytes()).hexdigest()==entry["sha256"],entry["path"]
assert (r/"gqa.cpp").read_bytes()==(prior/"gqa.cpp").read_bytes()
base=Path("C:/hs/b570-direct-id-v1-build/bin/Release/ggml-base.dll")
assert base.exists()
shutil.copy2(base,r/"build/Release/ggml-base.dll")
files=[r/n for n in ("gqa.cpp","ggml-vulkan.cpp","av-preserve.patch","CMakeLists.txt","RUN.ps1","PREREGISTRATION.json")]
files += [r/"CPU_ADDRESS_CHECK.json",r/"prepare.py"]
files+=list((r/"build/Release").glob("*.dll"))+list((r/"build/Release").glob("*.exe"))
files+=[Path("C:/hs/b570-query-head-lowering/benchmarks/b570_query_head_lowering_v1/native/query_head.h")]
files+=list(Path("C:/hs/b570-direct-id-v1-build/ggml/src/ggml-vulkan/ggml-vulkan.dir/Release").glob("*.comp.obj"))
files+=list(Path("C:/hs/llama-b10839/ggml/include").glob("*.h"))
manifest={"files":[{"path":str(p),"bytes":p.stat().st_size,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()}for p in files]}
(r/"BUILD_MANIFEST.json").write_text(json.dumps(manifest,indent=2))
print("Frozen",len(files),"inputs")
