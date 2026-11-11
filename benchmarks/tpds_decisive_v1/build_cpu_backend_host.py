"""Supply host buffer registration for all-GPU models; preserve CUDA runtime."""
from build_host import *
import os

def main():
    out=Path('D:/rtx184-operator/cpu-v2');out.mkdir()
    lines=subprocess.check_output('cmd /d /c D:\\rtx184-tools\\msvc\\setup_x64.bat && set',text=True).splitlines()
    env=os.environ.copy()
    for line in lines:
        if '=' in line and not line.startswith('='):
            k,v=line.split('=',1);env[k]=v
    cmake='D:/HeteroSpec-PC/.venv-analysis/Lib/site-packages/cmake/data/bin/cmake.exe'
    configure=[cmake,'-S',str(ROOT/'loop/native-arms/backend_loop4'),'-B',str(out),'-G','Ninja','-DCMAKE_MAKE_PROGRAM=D:/HeteroSpec-PC/.venv-analysis/Scripts/ninja.exe','-DCMAKE_BUILD_TYPE=Release','-DCMAKE_C_COMPILER=cl','-DCMAKE_CXX_COMPILER=cl','-DBUILD_SHARED_LIBS=ON','-DGGML_BACKEND_DL=ON','-DGGML_CPU=ON','-DGGML_CUDA=OFF','-DLLAMA_BUILD_APP=OFF','-DLLAMA_BUILD_TESTS=OFF','-DLLAMA_BUILD_EXAMPLES=OFF','-DLLAMA_BUILD_MTMD=OFF','-DLLAMA_OPENSSL=OFF','-DLLAMA_BUILD_UI=OFF','-DLLAMA_USE_PREBUILT_UI=OFF','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON']
    configure += ['-DGGML_NATIVE=OFF','-DGGML_AVX2=ON','-DGGML_FMA=ON','-DGGML_F16C=ON']
    for phase,cmd in [('configure',configure),('compile',[cmake,'--build',str(out),'--target','ggml-cpu','-j','3'])]:
        t=time.monotonic()
        with (out/(phase+'.log')).open('xb') as log:r=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
        put(out/(phase+'.json'),dict(argv=cmd,code=r.returncode,seconds=time.monotonic()-t));r.check_returncode()
    put(out/'BUILD.json',dict(modules={p.name:sha(p) for p in (out/'bin').glob('*.dll')},gpu_qualified=False,purpose='host buffer backend registration for unchanged all-GPU model placement'))

if __name__=='__main__':main()
