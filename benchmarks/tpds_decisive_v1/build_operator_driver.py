"""Same driver around separately pinned original and candidate graph cores."""
from build_host import *
import os
HERE=Path(__file__).resolve().parent;FROZEN=Path('E:/tpds167/build01');ORIG=Path('E:/rtx164/active03/qwen_config01')
def main():
    for arm in ('original','graph_tiles','backend_loop4','packed'):
        out=Path('D:/rtx184-operator')/(arm+'-driver-v4');out.mkdir();(out/'bin').mkdir()
        core=ORIG if arm=='original' else out.parent/arm
        source=ORIG/'source' if arm=='original' else ROOT/'loop/native-arms'/arm
        driver=(HERE.parent/'rtx_operator_frontier_v1/execution/driver.cpp').read_text().replace('#include "replay.inc"','#include "operator_replay.inc"')
        driver=driver.replace('profile::init();auto bin=','if(j.value("diagnostic",false))profile::init();auto bin=')
        driver=driver.replace('ggml_backend_load_all_from_path(bin.string().c_str());','auto base_clock=LoadLibraryW((bin/"ggml-base.dll").c_str());check(base_clock,"shared base clock module");auto clock_init=(void(*)())GetProcAddress(base_clock,"ggml_time_init");check(clock_init,"shared clock initializer");clock_init();ggml_backend_load_all_from_path(bin.string().c_str());')
        module_code='''#include <windows.h>
#include <psapi.h>
static void modules184(const fs::path&p){HMODULE mods[1024];DWORD bytes=0;check(EnumProcessModules(GetCurrentProcess(),mods,sizeof(mods),&bytes)&&bytes<=sizeof(mods),"module inventory");json a=json::array();for(unsigned i=0;i<bytes/sizeof(HMODULE);i++){char name[32768];check(GetModuleFileNameExA(GetCurrentProcess(),mods[i],name,sizeof(name))>0,"module path");a.push_back(std::string(name));}save(p,a);}
'''
        driver=driver.replace('int main(int argc,char**argv){',module_code+'int main(int argc,char**argv){')
        driver=driver.replace('check(gpu,"native RTX");','check(gpu,"native RTX");modules184(root/"modules-before.json");')
        driver=driver.replace('replay(gpu,j,root);return 0;','replay(gpu,j,root);modules184(root/"modules-after.json");return 0;')
        driver=driver.replace('model.reset();llama_backend_free();','modules184(root/"modules-after.json");model.reset();llama_backend_free();')
        driver=driver.replace('save(dir/"receipt.json",r);hs_scope::active=false;', 'size_t z=llama_state_seq_get_size(ctx.get(),0);std::vector<char> state_bytes(z);check(llama_state_seq_get_data(ctx.get(),(uint8_t*)state_bytes.data(),z,0)==z,"state export");write_bytes(dir/"sequence.bin",state_bytes.data(),z);save(dir/"receipt.json",r);hs_scope::active=false;')
        (out/'driver.cpp').write_text(driver,encoding='utf8')
        for file in ('operator_replay.inc',):shutil.copy2(HERE/file,out/file)
        shutil.copy2(HERE.parent/'rtx_operator_frontier_v1/execution/profiler.inc',out/'profiler.inc')
        commands=[]
        for phase in ('worker','link'):
            cmd=json.loads(sorted(FROZEN.glob(phase+'-*.json'))[-1].read_bytes())['argv']
            cmd=[x.replace(str(FROZEN/'source'),str(source)).replace(str(FROZEN/'core'),str(core/'core')).replace(str(FROZEN/'probe.cpp'),str(out/'driver.cpp')).replace(str(FROZEN/'probe.obj'),str(out/'driver.obj')).replace(str(FROZEN/'bin/probe.exe'),str(out/'bin/driver.exe')).replace('-std=c++17','-std=c++20') for x in cmd]
            if phase=='worker':
                cmd[2:2]=['-DFRONTIER_PROFILE','-fms-extensions','-IE:/rtx170/profiler/sdk/nvidia/cuda_nvcc/include','-IE:/rtx170/profiler/sdk/nvidia/cuda_runtime/include','-IE:/rtx170/profiler/sdk/nvidia/cuda_cupti/include']
                if arm=='original':cmd.insert(2,'-DTPDS_ORACLE')
            start=time.monotonic()
            with (out/(phase+'.log')).open('xb') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=600)
            record=dict(argv=cmd,code=r.returncode,seconds=time.monotonic()-start);commands.append(record);put(out/(phase+'.json'),record);r.check_returncode()
        put(out/'BUILD_CORE.json',dict(commands=commands,exe=sha(out/'bin/driver.exe'),core=sha(core/'core/src/libllama.a'),gpu_qualified=False))
        print(arm,'driver linked',flush=True)
if __name__=='__main__':main()
