"""Build/run counter mocks with MSVC; no CUDA headers, libraries or API calls."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
OUT=HERE/(sys.argv[1] if len(sys.argv)>1 else "cpu-checks-v1")
OUT.mkdir(exist_ok=False)
VC=Path("D:/rtx184-tools/msvc/VC/Tools/MSVC/14.44.35207")
SDK=Path("D:/rtx184-tools/msvc/Windows Kits/10")
cl=VC/"bin/Hostx64/x64/cl.exe"
env=os.environ.copy()
env["INCLUDE"]=";".join(map(str,[VC/"include",*[SDK/"Include/10.0.26100.0"/x for x in ("ucrt","shared","um","winrt","cppwinrt")]]))
env["LIB"]=";".join(map(str,[VC/"lib/x64",SDK/"Lib/10.0.26100.0/ucrt/x64",SDK/"Lib/10.0.26100.0/um/x64"]))
env["PATH"]=str(VC/"bin/Hostx64/x64")+";"+str(SDK/"bin/10.0.26100.0/x64")+";"+env.get("PATH","")
snapshot=OUT/"source_snapshot"; snapshot.mkdir()
sources=["hs_launch_budget.cpp","hs_launch_budget.hpp","cpu_mock.cpp","mock_tu_a.cpp","mock_tu_b.cpp"]
for name in sources: shutil.copy2(HERE/name,snapshot/name)
commands=[]
for name in sources:
    if not name.endswith(".cpp"): continue
    obj=OUT/(Path(name).stem+".obj")
    argv=[str(cl),"/nologo","/std:c++17","/O2","/MT","/EHsc","/DHS_LB_CPU_TEST_ONLY", "/I"+str(snapshot),"/c",str(snapshot/name),"/Fo"+str(obj)]
    before=time.monotonic(); r=subprocess.run(argv,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (OUT/(name+".log")).write_bytes(r.stdout)
    commands.append({"argv":argv,"code":r.returncode,"wall_seconds":time.monotonic()-before})
    if r.returncode: raise RuntimeError("CPU mock compile failed "+name)
exe=OUT/"launch_counter_cpu_mock.exe"
argv=[str(cl),"/nologo","/MT",*[str(OUT/(Path(n).stem+".obj")) for n in sources if n.endswith(".cpp")],"/Fe"+str(exe)]
r=subprocess.run(argv,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT); (OUT/"link.log").write_bytes(r.stdout); commands.append({"argv":argv,"code":r.returncode})
if r.returncode: raise RuntimeError("CPU mock link failed")
imports=subprocess.run([str(VC/"bin/Hostx64/x64/dumpbin.exe"),"/imports",str(exe)],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(OUT/"imports.log").write_bytes(imports.stdout)
if imports.returncode or any(x in imports.stdout.lower() for x in (b"nvcuda",b"cudart",b"cublas")): raise RuntimeError("Mock unexpectedly imports CUDA or import verification failed")
scenarios=["unarmed","invalid-limit","boundary-4096","multithread-4096","two-TUs-one-state","inherited-reservation","failed-submission-no-refund","prelaunch-order","reconfigure-denied","reentry-denied","graph-replay-denied","opaque-BLAS-denied","opaque-CUB-denied","zero-remaining"]
scenarios += ["failstop-unarmed","failstop-opaque"]
results=[]
for name in scenarios:
    r=subprocess.run([str(exe),name],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=10)
    if name.startswith("failstop-"):
        expected=0xE0330001 if name=="failstop-unarmed" else 0xE0330004
        (OUT/(name+".log")).write_bytes(r.stdout)
        value={"scenario":name,"CPU_MOCK_ONLY":True,"actual_GPU_launches":0,"expected_exit":expected,
               "pass":r.returncode in (expected,expected-2**32) and b"UNSAFE_MOCK_DRIVER_EXECUTED" not in r.stdout}
    else:
        (OUT/(name+".json")).write_bytes(r.stdout)
        value=json.loads(r.stdout)
        value["pass"] = value["pass"] and r.returncode == 0
    value["exit_code"]=r.returncode; results.append(value)
receipt={"schema":"heterospec.launch-counter.cpu-mocks.v1","CPU_ONLY":True,"CUDA_imports":False,
         "native_numeric_DLL_loaded":False,"actual_GPU_launches":0,"model_requests":0,
         "all_pass":all(v["pass"] for v in results),"scenario_count":len(results),"results":results,
         "compiler":str(cl),"compiler_sha256":hashlib.sha256(cl.read_bytes()).hexdigest(),"commands":commands,
         "exe_sha256":hashlib.sha256(exe.read_bytes()).hexdigest(),
         "sources":{n:hashlib.sha256((snapshot/n).read_bytes()).hexdigest() for n in sources}}
(OUT/"RECEIPT.json").write_text(json.dumps(receipt,indent=2),encoding="utf8")
print(json.dumps({"all_pass":receipt["all_pass"],"scenarios":len(results),"actual_GPU_launches":0,"receipt":str(OUT/"RECEIPT.json")}))
if not receipt["all_pass"]: raise SystemExit(1)
