import hashlib,json,os,shutil,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path("E:/rtx170")
FROZEN=Path("E:/tpds167/build01")
ORIG=Path("E:/rtx164/active03/qwen_config01")
def read(p):return json.loads(p.read_bytes())
def put(p,x):
    with p.open("x") as f:json.dump(x,f,indent=2)
def sha(p):
    with p.open("rb") as f:return hashlib.file_digest(f,"sha256").hexdigest()
def build(label,oracle=False,core=None,profiling=False):
    out=ROOT/label;out.mkdir(parents=True)
    source=ORIG if oracle else (core or FROZEN)
    for f in (source/"bin").glob("*.dll"):os.link(f,out/f.name)
    commands=[]
    for stage in ("worker","link"):
        cmd=read(sorted(FROZEN.glob(stage+"-*.json"))[-1])["argv"]
        cmd=[s.replace(str(FROZEN),str(source)) for s in cmd]
        cmd=[s.replace(str(source/"probe.cpp"),str(HERE/"driver.cpp")).replace(str(source/"probe.obj"),str(out/"driver.obj")).replace(str(source/"bin/probe.exe"),str(out/"driver.exe")).replace("-std=c++17","-std=c++20") for s in cmd]
        if stage=="worker":
            cmd.insert(2,"-I"+str(FROZEN))
            if profiling:cmd[2:2]=["-DFRONTIER_PROFILE","-fms-extensions","-IE:/rtx170/profiler/sdk/nvidia/cuda_nvcc/include","-IE:/rtx170/profiler/sdk/nvidia/cuda_runtime/include","-IE:/rtx170/profiler/sdk/nvidia/cuda_cupti/include"]
            if oracle:cmd.insert(2,"-DTPDS_ORACLE")
        with (out/(stage+".log")).open("xb") as log:
            subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=600,check=True)
        commands.append(cmd)
    put(out/"build.json",dict(commands=commands,exe=sha(out/"driver.exe"),core=sha(source/"core/src/libllama.a")))
def launch(label,build_id,manifest,model="8B"):
    root=ROOT/label;root.mkdir(parents=True);put(root/"input.json",manifest)
    lock=Path("D:/HeteroSpec-PC/RTX_EXPERIMENT.lock")
    with lock.open("x") as f:json.dump(dict(pid=os.getpid(),job=label),f)
    try:
        exe=ROOT/build_id/"driver.exe"
        modelpath=Path("D:/HeteroSpec-PC/models/gguf")/f"Qwen3-{model}-Q8_0.gguf"
        env={k:v for k,v in os.environ.items() if not k.startswith(("HS_","GGML_","JSA_","HSC_"))}
        start=time.monotonic()
        with (root/"native.log").open("xb") as f:
            r=subprocess.run([exe,modelpath,root/"input.json",root],stdout=f,stderr=subprocess.STDOUT,timeout=3600,env=env)
        put(root/"exit.json",dict(code=r.returncode,elapsed=time.monotonic()-start));r.check_returncode()
    finally:lock.unlink()
def unit(id,mode,arm,pos,width):
    return dict(id=id,mode=mode,arm=arm,pos=pos,width=width,state=str(ROOT/f"state-{pos}.bin"))
if __name__=="__main__":
    build("capture01");build("oracle01",True)
    for model in ("0.6B","8B"):
        launch("witness-"+model,"capture01",dict(units=[unit("native","capture","native",0,32),unit("scalar","qual","S1",0,32)]),model)

