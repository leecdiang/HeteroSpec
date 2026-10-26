#pragma once
#include <set>
// Diagnostic readback only. The ordinary request path never enables this hook.
inline bool raw_stage_capture(ggml_tensor *t, bool ask, const std::string &phase) {
    const char *root = getenv("HS_STAGE_CAPTURE");
    if (!root || !*root || phase != "VERIFY") return false;
    static std::set<std::string> saved;
    std::string name=t->name;
    std::map<std::string,std::string> stages={{"hs_qb_qk-0","qk"},{"hs_qb_prob-0","softmax"},{"hs_qb_av-0","av"},{"hs_qb_final-0","final"}};
    if (!stages.count(name) || saved.count(name)) return false;
    if (ask) return true;
    fs::path dir=root;fs::create_directories(dir);
    auto save=[&](ggml_tensor *v,const std::string &key) {
        size_t span=ggml_nbytes(v);std::vector<char> bytes(span);
        ggml_backend_tensor_get(v,bytes.data(),0,span);
        std::ofstream f(dir/(key+".bin"),std::ios::binary);f.write(bytes.data(),bytes.size());need(bool(f),"stage capture write");
        json j={{"name",v->name},{"ne",{v->ne[0],v->ne[1],v->ne[2],v->ne[3]}},{"nb",{v->nb[0],v->nb[1],v->nb[2],v->nb[3]}},{"type",ggml_type_name(v->type)},{"span_bytes",span},{"op",ggml_op_name(v->op)}};
        dump(dir/(key+".json"),j);
    };
    if(stages[name]=="qk"){save(t->src[0],"K");save(t->src[1],"Q");}
    if(stages[name]=="softmax"){
        save(t->src[1],"mask");float scale;memcpy(&scale,t->op_params,sizeof(float));
        dump(dir/"capture.json",{{"provenance","NEW_REAL_REQUEST_CAPTURE"},{"layer",0},{"phase",phase},{"scale",scale},{"kv_capacity",1024},{"timing_eligible",false}});
    }
    if(stages[name]=="av")save(t->src[0],"V");
    save(t,stages[name]);saved.insert(name);return true;
}
