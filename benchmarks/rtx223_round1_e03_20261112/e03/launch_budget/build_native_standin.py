"""Compile the real default-blocked provider into a CUDA-free host executable."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess
HERE=Path(__file__).resolve().parent; OUT=HERE/"native-host-standin-v1"; OUT.mkdir(exist_ok=False)
VC=Path("D:/rtx184-tools/msvc/VC/Tools/MSVC/14.44.35207"); SDK=Path("D:/rtx184-tools/msvc/Windows Kits/10")
env=os.environ.copy(); env["INCLUDE"]=";".join(map(str,[VC/"include",*[SDK/"Include/10.0.26100.0"/x for x in ("ucrt","shared","um","winrt","cppwinrt")]])); env["LIB"]=";".join(map(str,[VC/"lib/x64",SDK/"Lib/10.0.26100.0/ucrt/x64",SDK/"Lib/10.0.26100.0/um/x64"])); env["PATH"]=str(VC/"bin/Hostx64/x64")+";"+str(SDK/"bin/10.0.26100.0/x64")+";"+env.get("PATH","")
cl=VC/"bin/Hostx64/x64/cl.exe"; commands=[]
for name in ("hs_launch_budget.hpp","hs_launch_budget.cpp","native_gate_host_standin.cpp"): shutil.copy2(HERE/name,OUT/name)
for name in ("hs_launch_budget.cpp","native_gate_host_standin.cpp"):
    argv=[str(cl),"/nologo","/std:c++17","/O2","/MT","/EHsc","/c",str(OUT/name),"/Fo"+str(OUT/(Path(name).stem+".obj"))]
    r=subprocess.run(argv,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(OUT/(name+".log")).write_bytes(r.stdout);commands.append({"argv":argv,"exit_code":r.returncode})
    if r.returncode: raise RuntimeError("host standin compile failed")
exe=OUT/"native_gate_host_standin.exe"
argv=[str(cl),"/nologo","/MT",str(OUT/"hs_launch_budget.obj"),str(OUT/"native_gate_host_standin.obj"),"/Fe"+str(exe)]
r=subprocess.run(argv,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(OUT/"link.log").write_bytes(r.stdout);commands.append({"argv":argv,"exit_code":r.returncode})
if r.returncode: raise RuntimeError("host standin link failed")
imports=subprocess.run([str(VC/"bin/Hostx64/x64/dumpbin.exe"),"/imports",str(exe)],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(OUT/"imports.log").write_bytes(imports.stdout)
if imports.returncode or any(x in imports.stdout.lower() for x in (b"nvcuda",b"cudart",b"cublas")): raise RuntimeError("CUDA import not allowed")
r=subprocess.run([str(exe)],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=10);(OUT/"raw.json").write_bytes(r.stdout);value=json.loads(r.stdout)
receipt={"schema":"heterospec.native-gate-host-standin.v1","pass":value["pass"] and r.returncode==0,"raw":value,"exit_code":r.returncode,"commands":commands,"sources":{n:hashlib.sha256((OUT/n).read_bytes()).hexdigest() for n in ("hs_launch_budget.cpp","hs_launch_budget.hpp","native_gate_host_standin.cpp")},"exe_sha256":hashlib.sha256(exe.read_bytes()).hexdigest(),"CUDA_imports":False,"actual_GPU_launches":0,"native_numeric_DLL_loaded":False}
(OUT/"RECEIPT.json").write_text(json.dumps(receipt,indent=2),encoding="utf8");print(json.dumps({"pass":receipt["pass"],"native_configure_result":value["native_configure_result"],"actual_GPU_launches":0}))
if not receipt["pass"]: raise SystemExit(1)
