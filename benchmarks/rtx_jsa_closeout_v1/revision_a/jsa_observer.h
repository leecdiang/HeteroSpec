#pragma once
#include "llama.h"
#include "ggml-backend.h"
#include "../src/hsc_counter.h"
#include "nlohmann/json.hpp"
#include <cmath>
#include <filesystem>
#include <fstream>
#include <map>
#include <string>
#include <vector>
#include <cstring>

namespace jsa_observer {
using json = nlohmann::ordered_json;
inline uint64_t decode_id = 0;
inline std::map<llama_context *, uint64_t> owner;
inline bool enabled() { return hsc::is_heavy() && std::getenv("HS_JSA_CAPTURE"); }
inline std::filesystem::path root() { return std::getenv("HS_JSA_CAPTURE"); }
inline void emit(json record) {
    if (!enabled()) return;
    std::filesystem::create_directories(root());
    std::ofstream file(root()/"observer.jsonl", std::ios::binary|std::ios::app);
    file << record.dump() << "\n";
    if (!file) throw std::runtime_error("JSA observer write failed");
}
inline json shape(ggml_tensor * tensor) {
    if (!tensor) return nullptr;
    return {{"ne",{tensor->ne[0],tensor->ne[1],tensor->ne[2],tensor->ne[3]}},
            {"nb",{tensor->nb[0],tensor->nb[1],tensor->nb[2],tensor->nb[3]}},
            {"type",ggml_type_name(tensor->type)}};
}
inline bool selected(int layer) {
    const char * configured = std::getenv("HS_JSA_LAYERS");
    if (!configured) throw std::runtime_error("JSA layer set missing");
    const std::string layers = std::string(",")+configured+",";
    return layers.find(","+std::to_string(layer)+",") != std::string::npos;
}
inline bool geometry(ggml_tensor * tensor, bool ask) {
    if (!enabled() || hsc::w.role != 1) return false;
    const std::string name = tensor->name;
    const bool softmax = name.rfind("kq_soft_max-",0) == 0;
    const bool flash = name.rfind("hs_jsa_flash-",0) == 0;
    if (!softmax && !flash) return false;
    const int layer = std::stoi(name.substr(name.find_last_of('-')+1));
    if (!selected(layer)) return false;
    if (ask) return true;
    auto * qk = tensor->src[0];
    auto * q = flash ? tensor->src[0] : qk->src[1];
    auto * k = flash ? tensor->src[1] : qk->src[0];
    auto * mask = flash ? tensor->src[3] : tensor->src[1];
    if (!mask || !q || !k) throw std::runtime_error("JSA geometry source missing");
    if (mask->type != GGML_TYPE_F32 && mask->type != GGML_TYPE_F16) throw std::runtime_error("JSA mask type unsupported");
    std::vector<uint8_t> bytes(ggml_nbytes(mask));
    ggml_backend_tensor_get(mask,bytes.data(),0,bytes.size());
    json visible = json::array();
    for (int64_t d3=0;d3<mask->ne[3];++d3) for (int64_t d2=0;d2<mask->ne[2];++d2) for (int64_t row=0;row<mask->ne[1];++row) {
        int count=0;
        for (int64_t key=0;key<mask->ne[0];++key) {
            const size_t offset=key*mask->nb[0]+row*mask->nb[1]+d2*mask->nb[2]+d3*mask->nb[3];
            float value;
            if (mask->type==GGML_TYPE_F32) std::memcpy(&value,bytes.data()+offset,sizeof(value));
            else { ggml_fp16_t half;std::memcpy(&half,bytes.data()+offset,sizeof(half));value=ggml_fp16_to_fp32(half); }
            if (std::isfinite(value)) ++count;
        }
        visible.push_back(count);
    }
    std::filesystem::create_directories(root());
    std::ofstream raw(root()/"masks.bin",std::ios::binary|std::ios::app);
    const auto offset=raw.tellp();raw.write((const char*)bytes.data(),bytes.size());
    if (!raw) throw std::runtime_error("JSA mask write failed");
    auto * memory=llama_get_memory((llama_context*)hsc::w.context);
    emit({{"event","geometry"},{"decode_id",decode_id},{"layer",layer},{"phase",hsc::w.prefill?"prefill":"continuation"},
          {"caller_rows",hsc::w.caller_rows},{"Q",shape(q)},{"K",shape(k)},{"mask",shape(mask)},
          {"physical_key_extent",k->ne[1]},{"q_occupied",q->ne[1]*q->ne[3]},
          {"visible_keys",visible},{"mask_file","masks.bin"},{"mask_offset",(int64_t)offset},{"mask_bytes",bytes.size()},
          {"kv_min",llama_memory_seq_pos_min(memory,0)},{"kv_max",llama_memory_seq_pos_max(memory,0)},
          {"flash",flash}});
    return true;
}
inline void begin(llama_context * context) { if (enabled()) owner[context]=++decode_id; }
inline void logits(llama_context * context,llama_batch batch,const char * role) {
    if (!enabled()) return;
    const int vocabulary=llama_vocab_n_tokens(llama_model_get_vocab(llama_get_model(context)));
    std::filesystem::create_directories(root());
    for (int row=0;row<batch.n_tokens;++row) {
        if (!(batch.logits ? batch.logits[row] : row==batch.n_tokens-1)) continue;
        const float * values=llama_get_logits_ith(context,row);
        if (!values) throw std::runtime_error("JSA requested logits absent");
        std::ofstream file(root()/"logits.f32",std::ios::binary|std::ios::app);
        const auto offset=file.tellp();file.write((const char*)values,vocabulary*sizeof(float));
        if (!file) throw std::runtime_error("JSA logits write failed");
        emit({{"event","decision_vector"},{"decode_id",owner[context]},{"role",role},{"row",row},
              {"input_id",batch.token[row]},{"position",batch.pos?batch.pos[row]:-1},
              {"logits_file","logits.f32"},{"offset",(int64_t)offset},{"floats",vocabulary},
              {"proposal_phase",hsc::w.proposal_phase},{"verification_pending",hsc::w.pending}});
    }
}
inline void sample(llama_context * context,int row,int id) {
    if (enabled()) emit({{"event","sample_owner"},{"decode_id",owner[context]},{"row",row},{"id",id}});
}
}
