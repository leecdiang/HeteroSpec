"""Observe the retained C1536 service without replacing its original oracle."""
from build_operator_driver import *
import difflib
def main():
    prior=json.loads((FROZEN.parent/'formal01/freeze.json').read_bytes());original=FROZEN/'service.cpp';assert sha(original)==prior['inputs'][str(original)]
    for arm in ('original','graph_tiles','backend_loop4','packed'):
        out=Path('D:/rtx184-operator')/(arm+'-service-v2');out.mkdir();(out/'bin').mkdir()
        core=ORIG if arm=='original' else out.parent/arm;source=ORIG/'source' if arm=='original' else ROOT/'loop/native-arms'/arm
        before=original.read_text();s=before.replace('struct Context {','#include "target_capture.hpp"\n#include "replay_path.hpp"\nstruct Context {')
        s=s.replace('    int sample(int row,','    void snapshot(const std::string&key,int row){tpds_decisive::capture_existing(c,model,path/"state"/key,row);}\n    int sample(int row,')
        s=s.replace('    int pending=transferred_pending','    int final_frontier=-1;int pending=transferred_pending')
        s=s.replace('bool done=commit(pending);auto first_ready=', 'if(capture)target->snapshot("initial",-1);bool done=commit(pending);auto first_ready=')
        s=s.replace('done=commit(pending);continue;','if(capture)target->snapshot("ordinary-"+std::to_string(ids.size()),-1);done=commit(pending);continue;')
        s=s.replace('int keep=base+1+accepted;target->trim(keep);draft->trim(keep);','int keep=base+1+accepted;target->trim(keep);draft->trim(keep);final_frontier=accepted;if(capture)target->snapshot("commit-"+std::to_string(cycle),accepted);')
        s=s.replace('    if(capture){\n        auto state_record=', '    if(!capture){auto began=Clock::now();target->snapshot("final-clean",final_frontier);r["post_service_state_seconds"]=since(began);}\n    if(capture){\n        auto state_record=')
        module='''static void modules184(const fs::path&p){HMODULE mods[1024];DWORD bytes=0;need(EnumProcessModules(GetCurrentProcess(),mods,sizeof(mods),&bytes)&&bytes<=sizeof(mods),"modules");json a=json::array();for(unsigned i=0;i<bytes/sizeof(HMODULE);i++){char name[32768];need(GetModuleFileNameExA(GetCurrentProcess(),mods[i],name,sizeof(name))>0,"module path");a.push_back(std::string(name));}dump(p,a);}
'''
        s=s.replace('int main(int argc,char** argv){',module+'int main(int argc,char** argv){')
        forced='''fs::path root=argv[4];fs::create_directories(root);modules184(root/"modules-before.json");
        if(panel.contains("forced")){
            auto job=panel.at("forced");need(job.at("no_candidate_payload")==true,"token-only forced replay");auto prompt=job.at("prompt_ids").get<std::vector<int>>();Context ctx(t.get(),1,true,false,false,"",1);
            json result={{"model_load_seconds",load_seconds},{"paths",json::array()},{"requests",0},{"token_rows",0}};int index=0;
            if(job.contains("sentinel_state")){
                std::ifstream f(job.at("sentinel_state").get<std::string>(),std::ios::binary|std::ios::ate);need(bool(f),"sentinel open");std::vector<uint8_t> bytes(size_t(f.tellg()));f.seekg(0);f.read((char*)bytes.data(),bytes.size());need(bool(f),"sentinel read");ctx.reset(false,root/"sentinel");need(llama_state_seq_set_data(ctx.c,bytes.data(),bytes.size(),0)==bytes.size(),"sentinel import");llama_synchronize(ctx.c);std::vector<uint8_t> exported(llama_state_seq_get_size(ctx.c,0));need(llama_state_seq_get_data(ctx.c,exported.data(),exported.size(),0)==exported.size(),"sentinel export");std::ofstream dest(root/"sentinel-export.bin",std::ios::binary);dest.write((char*)exported.data(),exported.size());need(bool(dest),"sentinel write");result["requests"]=1;result["sentinel_bounds"]=ctx.bounds();result["sentinel_only_no_model_forward"]=true;
            }
            for(const auto&path:job.at("paths")){
                auto dir=root/std::to_string(index++);fs::create_directories(dir);ctx.reset(false,dir);hsc::begin("baseline",int(prompt.size()));auto suffix=path.at("suffix").get<std::vector<int>>();need(prompt.size()+suffix.size()<=size_t(context_capacity),"forced capacity");auto wanted=path.at("positions").get<std::vector<int>>();json captures=json::array();auto began=Clock::now();
                tpds_decisive::replay_path(prompt,suffix,job.at("producer").at("caller_lengths").get<std::vector<int>>(),job.at("producer").at("last_output_flags").get<std::vector<bool>>(),
                [&](const std::vector<int>&ids,int pos,bool all,const char*phase,bool last){need(last,"original caller flags");ctx.decode(ids,pos,all,phase);result["token_rows"]=result["token_rows"].get<int64_t>()+ids.size();},
                [&](int row,int count){if(std::find(wanted.begin(),wanted.end(),count)!=wanted.end()){auto key=std::to_string(count);tpds_decisive::capture_existing(ctx.c,t.get(),dir/key,row);captures.push_back({{"position",count},{"directory",std::to_string(index-1)+"/"+key}});}});
                result["requests"]=index;result["paths"].push_back({{"index",index-1},{"seconds",since(began)},{"captures",captures},{"suffix",suffix}});dump(root/"result.json",result);
            }
            result["status"]="COMPLETE";dump(root/"result.json",result);modules184(root/"modules-after.json");return 0;
        }
'''
        s=s.replace('        for(const auto& block:panel.at("blocks")){',forced+'        for(const auto& block:panel.at("blocks")){')
        s=s.replace('        d.reset();t.reset();llama_backend_free();','        modules184(root/"modules-after.json");d.reset();t.reset();llama_backend_free();')
        (out/'service.cpp').write_text(s,encoding='utf8');(out/'CHANGE.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),s.splitlines(True))),encoding='utf8')
        for n in ('target_capture.hpp','replay_path.hpp'):shutil.copy2(HERE/'native'/n,out/n)
        commands=[]
        for phase in ('worker','link'):
            cmd=json.loads(sorted(FROZEN.glob(phase+'-*.json'))[-1].read_bytes())['argv'];cmd=[x.replace(str(FROZEN/'source'),str(source)).replace(str(FROZEN/'core'),str(core/'core')).replace(str(FROZEN/'probe.cpp'),str(out/'service.cpp')).replace(str(FROZEN/'probe.obj'),str(out/'service.obj')).replace(str(FROZEN/'bin/probe.exe'),str(out/'bin/service.exe')) for x in cmd]
            if phase=='worker' and arm=='original':cmd.insert(2,'-DTPDS_ORACLE')
            t=time.monotonic()
            with (out/(phase+'.log')).open('xb') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=600)
            record=dict(argv=cmd,code=r.returncode,seconds=time.monotonic()-t);commands.append(record);put(out/(phase+'.json'),record);r.check_returncode()
        runtime=out.parent/(arm+'-driver-v3');binding=json.loads((runtime/'RUNTIME_BINDING.json').read_bytes())
        for name,h in binding['modules'].items():os.link(runtime/'bin'/name,out/'bin'/name)
        put(out/'BUILD.json',dict(exe=sha(out/'bin/service.exe'),modules=binding['modules'],source=sha(out/'service.cpp'),original_source=sha(original),core=sha(core/'core/src/libllama.a'),commands=commands,gpu_qualified=False));print('operator service built',arm,flush=True)
if __name__=='__main__':main()
