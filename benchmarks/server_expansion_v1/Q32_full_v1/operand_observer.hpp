#pragma once
// Offline only: copy actual real-model operands after the requested operation.
// This observer is a separate ELF, never a clean timing executable.
inline fs::path q32_operand_dir;
inline std::map<std::string,bool> q32_operand_seen;
static bool q32_operand_wanted(ggml_tensor*t,const std::string& phase){
    if(q32_operand_dir.empty() || phase!="VERIFY" || t->op!=GGML_OP_MUL_MAT || !t->src[0] || !t->src[1])return false;
    const std::string name=t->src[0]->name;
    return (name=="blk.0.attn_q.weight" || name=="blk.0.attn_v.weight") &&
        (t->src[0]->type==GGML_TYPE_Q4_K || t->src[0]->type==GGML_TYPE_Q6_K) &&
        t->src[1]->type==GGML_TYPE_F32 && std::string(t->name).rfind("hs_ref1_group_",0)==0 && !q32_operand_seen[name];
}
static void q32_operand_copy(ggml_tensor*t){
    const std::string weight=t->src[0]->name;need(!q32_operand_seen[weight],"duplicate real operand capture");
    fs::create_directories(q32_operand_dir);json meta={{"weight",weight},{"weight_type",ggml_type_name(t->src[0]->type)},{"node",t->name},{"origin","Actual32B native VERIFY graph, no synthetic activation"}};
    for(auto p:std::vector<std::pair<std::string,ggml_tensor*>>{{"weight",t->src[0]},{"activation",t->src[1]},{"output",t}}){
        auto*x=p.second;need(ggml_is_contiguous(x),"Real operand capture requires dense tensor");
        std::vector<uint8_t> bytes(ggml_nbytes(x));ggml_backend_tensor_get(x,bytes.data(),0,bytes.size());
        const auto file=q32_operand_dir/(weight+"."+p.first+".bin");need(!fs::exists(file),"fresh real operand");
        std::ofstream f(file,std::ios::binary);f.write(reinterpret_cast<const char*>(bytes.data()),bytes.size());f.flush();need(bool(f),"real operand write");
        Sha256 h;h.update(reinterpret_cast<const char*>(bytes.data()),bytes.size());
        meta[p.first+"_tensor"]={{"ne",{x->ne[0],x->ne[1],x->ne[2],x->ne[3]}},{"nb",{x->nb[0],x->nb[1],x->nb[2],x->nb[3]}},{"bytes",bytes.size()},{"sha256",h.finish()},{"file",file.filename().string()}};
    }
    dump(q32_operand_dir/(weight+".json"),meta);q32_operand_seen[weight]=true;
}
