"""Stage a new native worker from pinned PR151 source, leaving old sources untouched.
The adapted worker retains its transaction. Build with the inherited build command.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from common import need, save, file_hash, upstream_bytes, UPSTREAM, STUDY

def replace_once(text, old, new, count=1):
    need(text.count(old)==count, 'source anchor missing/duplicated: '+old[:70])
    return text.replace(old,new)

def adapt_worker(text):
    text=replace_once(text,'#include "arm_spec.h"','#include "arm_spec.h"\n#include <regex>')
    text=replace_once(text,'using Clock=std::chrono::steady_clock;',
        'using Clock=std::chrono::steady_clock;\nstatic int dense_target_layers=24;\nstatic int dense_threads=24;')
    text=replace_once(text,'p.n_threads=24;p.n_threads_batch=24;',
        'p.n_threads=dense_threads;p.n_threads_batch=dense_threads;')
    text=replace_once(text,
        'if(!d||std::string(ggml_backend_dev_description(d)).find("5070") == std::string::npos)o.bad=true;',
        '''// A hybrid target is permitted only with observed CPU/5070 placement.
        if(!d || (ggml_backend_dev_type(d)!=GGML_BACKEND_DEVICE_TYPE_CPU &&
           std::string(ggml_backend_dev_description(d)).find("5070")==std::string::npos))o.bad=true;
        std::smatch layer;std::regex layer_suffix("-([0-9]+)$");
        if(std::regex_search(name,layer,layer_suffix))j["layer"]=std::stoi(layer[1]);
        else j["layer"]=nullptr;
        j["device_type"]=d?int(ggml_backend_dev_type(d)):-1;''')
    text=replace_once(text,'auto identity=binding.at("families").at(family);',
        '''need(family=="Qwen","dense14b uses original Qwen source cohort");
        dense_target_layers=binding.at("dense14b").at("target_gpu_layers").get<int>();
        dense_threads=binding.at("dense14b").at("threads").get<int>();
        need(dense_target_layers>0&&dense_target_layers<40,"hybrid target layer range");
        need(dense_threads>0&&dense_threads<=128,"thread count");
        auto identity=binding.at("families").at(family);''')
    text=replace_once(text,'slot.at("study_id")=="rtx_scope_transfer_v1"',
        'slot.at("study_id")=="'+STUDY+'"')
    text=replace_once(text,'mp.n_gpu_layers=999;', 'mp.n_gpu_layers=dense_target_layers;')
    text=replace_once(text,'d=llama_model_load_from_file(argv[3],mp);',
        'mp.n_gpu_layers=999;d=llama_model_load_from_file(argv[3],mp);')
    text=replace_once(text,'need(d,"draft load");',
        '''need(d,"draft load");need(llama_model_n_layer(t)==40&&llama_model_n_embd(t)==5120,"not 14B target geometry");
        result["placement"]={{"target_gpu_layers",dense_target_layers},{"draft_gpu_layers",999},{"threads",dense_threads}};''')
    text=replace_once(text,'{"R","C_GS","C_PQ","C_QB"}', '{"R","C_PQ","C_QB"}')
    text=replace_once(text,'residents.size()==4','residents.size()==3')
    text=text.replace('all four factorial pools','three registered dense14b pools')
    text=replace_once(text,'memory_free>=256ULL*1024*1024',
        'memory_free>=binding.at("dense14b").at("min_vram_free_bytes").get<size_t>()')
    text=text.replace('less than 256 MiB free after provisioning','insufficient frozen VRAM headroom')
    text=replace_once(text,'dump(root/"PROVISIONED.json",result);',
        '''MEMORYSTATUSEX ms{};ms.dwLength=sizeof(ms);need(GlobalMemoryStatusEx(&ms),"RAM probe failed");
        result["memory_after_provisioning"]["ram_available_bytes"]=ms.ullAvailPhys;
        need(ms.ullAvailPhys>=binding.at("dense14b").at("min_ram_free_bytes").get<unsigned long long>(),"insufficient RAM headroom");
        dump(root/"PROVISIONED.json",result);''')
    # Additional sequence-state bytes are captured after the request clock.
    # Heavy diagnostic logits retain the upstream capture timing and are NOT performance samples.
    text=replace_once(text,'    return r;\n}\nint main',
        '''    if(capture){
        auto state_record=[&](Context* x,const char* role){
            if(!x)return;
            const auto n=llama_state_seq_get_size(x->c,0);std::vector<uint8_t> bytes(n);
            need(llama_state_seq_get_data(x->c,bytes.data(),n,0)==n,"state serialization size");
            auto file=dir/(std::string(role)+"_final.state");std::ofstream out(file,std::ios::binary);
            out.write(reinterpret_cast<const char*>(bytes.data()),bytes.size());need(bool(out),"state write");out.close();
            r[std::string(role)+"_state"]={{"bytes",n},{"sha256",hash_file(file)}};
        };
        state_record(target,"target");state_record(draft,"draft");
    }
    return r;
}
int main''')
    text=replace_once(text,'HMODULE mods[1024];',
        'result["vocabulary_eog"]=json::array();for(int i=0;i<llama_vocab_n_tokens(tv);i++)if(llama_vocab_is_eog(tv,i))result["vocabulary_eog"].push_back(i);\n        HMODULE mods[1024];')
    text=replace_once(text,'r["identity"]=identity;',
        'r["vocabulary_eog"]=result["vocabulary_eog"];r["identity"]=identity;')
    return text

def stage(repo,out):
    out=Path(out);need(not out.exists(),'fresh stage directory required')
    sources={n:upstream_bytes(repo,n) for n in ('worker.cpp','arm_spec.h','build_native.py','study.py')}
    changed=adapt_worker(sources['worker.cpp'].decode('utf-8'))
    # The staged copy is used only to build, never as the old experiment runner.
    out.mkdir(parents=True)
    for n,b in sources.items():(out/n).write_bytes(changed.encode() if n=='worker.cpp' else b)
    save(out/'ADAPTATION.json',{'status':'STAGED_NOT_COMPILED_OR_QUALIFIED','upstream':UPSTREAM,
          'changes':['partial target offload; fully offloaded original draft','CPU/GPU observed placement',
          'three resident pools','post-clock state serialization','14B geometry guard','new study identity'],
          'acceptance_loop_changed':False,'attention_arithmetic_changed':False,
          'files':{n:file_hash(out/n) for n in sources},'native_requests':0})
    return out

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--repo',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();print(stage(a.repo,a.out))
