"""Derive the V4 worker with an isolated continuation context."""
from prepare import *

def main():
    original=ROOT/'scripts/platform/rtx_trajectory_cost_v4/worker.cpp'
    s=original.read_text(encoding='utf-8')
    s=s.replace('#include <vector>','#include <vector>\n#include <fstream>')
    s=s.replace('X(llama_vocab_get_suppress_tokens)', 'X(llama_state_get_size) X(llama_state_get_data) X(llama_state_set_data) X(llama_sampler_clone) X(llama_memory_seq_pos_min) X(llama_n_ubatch) X(llama_vocab_get_suppress_tokens)')
    s=s.replace('argc==5','argc==6').replace('ubatch role','ubatch role continuation-ub-or-0')
    s=s.replace('    int nextpos=0;', '''    llama_context * source_ctx=nullptr;
    llama_sampler * source_sampler=nullptr;
    auto state=[&](llama_context*c){f_llama_synchronize(c);std::vector<uint8_t>b(f_llama_state_get_size(c));
      require(f_llama_state_get_data(c,b.data(),b.size())==b.size(),"short state write");return b;};
    auto positions=[&](llama_context*c){auto*m=f_llama_get_memory(c);return json{{"sequence",0},{"min",f_llama_memory_seq_pos_min(m,0)},{"max",f_llama_memory_seq_pos_max(m,0)}};};
    auto bytes=[&](const char*suffix,const void*b,size_t n){const char*p=std::getenv("HS_WORKER_WITNESS");require(p!=nullptr,"missing witness path");
      std::ofstream f(std::string(p)+suffix,std::ios::binary);f.write((const char*)b,n);f.flush();require(bool(f),"state write failed");};
    auto transfer=[&](int pending,int idx){
      int dest=std::stoi(argv[5]);require(dest==0||dest==1||dest==2,"continuation UB invalid");
      if(dest==0)return json(nullptr);
      require(role=="R"&&cp.n_ubatch==2,"target-only transfer boundary");
      auto before=state(ctx);auto pos=positions(ctx);const float*l=f_llama_get_logits_ith(ctx,idx);require(l!=nullptr,"pending logits missing");
      bytes(".pending_logits.f32",l,nv*sizeof(float));auto*clone=f_llama_sampler_clone(sampler);require(clone!=nullptr,"sampler clone failed");
      auto cp2=cp;cp2.n_ubatch=dest;auto*dst=f_llama_init_from_model(model,cp2);require(dst!=nullptr,"continuation allocation failed");
      size_t consumed=f_llama_state_set_data(dst,before.data(),before.size());auto restored=state(dst),after=state(ctx);
      bytes(".source_before.kv",before.data(),before.size());bytes(".destination.kv",restored.data(),restored.size());bytes(".source_after.kv",after.data(),after.size());
      json result={{"source_ub",cp.n_ubatch},{"destination_ub",dest},{"state_bytes",before.size()},{"consumed_bytes",consumed},{"before",pos},{"after",positions(dst)},
        {"source_after",positions(ctx)},{"state_equal",before==restored},{"source_unchanged",before==after},{"pending_id",pending},{"pending_logits_index",idx},
        {"sampler_clone","llama_sampler_clone of full post-accept chain; opaque sampler byte serialization unavailable"},{"seed",123},
        {"history",std::vector<int>{pending}},{"pending_boundary","sample and accept once in source; carry own ID without destination resample"}};
      require(consumed==before.size()&&before==restored&&before==after&&pos==positions(dst),"state transfer failed");
      source_ctx=ctx;source_sampler=sampler;ctx=dst;sampler=clone;return result;
    };
    int nextpos=0;''')
    s=s.replace('{"logits_bytes_hex",hex(logits,nv*sizeof(float))},','')
    s=s.replace('out["terminal"]=s["eog"];','out["terminal"]=s["eog"];\n            out["transfer"]=transfer(id,n-1);')
    s=s.replace('f_llama_sampler_free(sampler);f_llama_free(ctx);','f_llama_sampler_free(sampler);f_llama_free(ctx);if(source_sampler)f_llama_sampler_free(source_sampler);if(source_ctx)f_llama_free(source_ctx);')
    (HERE/'worker.cpp').write_text(s,encoding='utf-8',newline='\n')
    src=OUT/'pinned-source';binary=OUT/'worker-bin';zig=ASSET/'.venv-analysis/Lib/site-packages/ziglang/zig.exe'
    attempts=read(DOC/'WORKER_BUILD_ATTEMPTS.json') if (DOC/'WORKER_BUILD_ATTEMPTS.json').exists() else []
    for role,defines in [('P',['-DPROPOSER_ONLY']),('R',[])]:
        cmd=[str(zig),'c++','-std=c++17','-O2','-target','x86_64-windows-gnu','-I'+str(src/'include'),'-I'+str(src/'ggml/include'),'-I'+str(src/'vendor/nlohmann'),str(HERE/'worker.cpp'),*defines,'-lpsapi','-o',str(binary/(role+'.exe'))]
        with (OUT/('build-'+role+'.log')).open('wb') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
        attempts.append({'command':cmd,'exit_code':r.returncode});save(DOC/'WORKER_BUILD_ATTEMPTS.json',attempts)
        if r.returncode:raise RuntimeError('worker build failed '+role)
    save(DOC/'WORKER_BUILD_IDENTITY.json',{'source_sha256':sha(HERE/'worker.cpp'),'original_sha256':sha(original),'compiler_sha256':sha(zig),'commands':attempts,'binaries':{role:sha(binary/(role+'.exe')) for role in ['P','R']}})
    print('new P/R workers built',flush=True)

if __name__=='__main__':main()
