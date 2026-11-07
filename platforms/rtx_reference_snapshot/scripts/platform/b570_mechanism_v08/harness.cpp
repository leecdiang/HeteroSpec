// Mechanism-only common target frontend for pinned llama.cpp b10839.
#include "arg.h"
#include "common.h"
#include "sampling.h"
#include "llama.h"
#include "nlohmann/json.hpp"
#include <clocale>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <limits>

using json = nlohmann::ordered_json;

int main(int argc, char ** argv) {
    std::setlocale(LC_NUMERIC, "C");
    common_params params;
    common_init();
    if (!common_params_parse(argc, argv, params, LLAMA_EXAMPLE_COMPLETION)) return 1;
    if (params.n_ctx != 1024 || params.n_batch != 512 ||
        (params.n_ubatch != 128 && params.n_ubatch != 1) || params.n_predict != 128 ||
        params.sampling.temp != 0 || params.sampling.seed != 123 || params.warmup) {
        std::cerr << "Frozen mechanism parameter contract violated\n"; return 2;
    }
    llama_backend_init();
    llama_numa_init(params.numa);
    auto init = common_init_from_params(params);
    auto * ctx = init->context();
    auto * model = init->model();
    auto * sampler = init->sampler(0);
    if (!ctx || !model || !sampler) return 3;
    const auto * vocab = llama_model_get_vocab(model);
    std::vector<llama_token> input;
    const char * input_path = std::getenv("HS_MECHANISM_INPUT_IDS");
    if (input_path) {
        std::ifstream file(input_path);
        json ids; file >> ids;
        input = ids.get<std::vector<llama_token>>();
    } else {
        input = common_tokenize(ctx, params.prompt, true, true);
    }
    if (input.empty() || input.size()+128 > 1024) return 4;
    for (auto id : input) if (id < 0 || id >= llama_vocab_n_tokens(vocab)) return 5;
    const char * output_path = std::getenv("HS_MECHANISM_OUTPUT");
    if (!output_path) return 6;
    json result;
    result["schema"] = "heterospec.b570.mechanism.harness.v08";
    result["prompt_ids"] = input;
    result["context"] = {{"n_ctx",llama_n_ctx(ctx)},{"n_batch",llama_n_batch(ctx)},
                         {"n_ubatch",llama_n_ubatch(ctx)},{"sequence_id",0},
                         {"flash_attention","off"},{"seed",123},{"greedy",true}};
    result["partitions"] = json::array();
    result["decisions"] = json::array();
    std::vector<llama_token> all;
    int n_past = 0;
    for (size_t i=0;i<input.size();i+=512) {
        const int size = std::min(size_t(512),input.size()-i);
        std::vector<llama_token> chunk(input.begin()+i,input.begin()+i+size);
        all.insert(all.end(),chunk.begin(),chunk.end());
        for (auto id:chunk) common_sampler_accept(sampler,id,false);
        result["partitions"].push_back({{"kind","prefill"},{"position",n_past},
                                        {"input_ids",chunk},{"n_tokens",size}});
        if (!common_prompt_batch_decode(ctx,all,size,n_past,512,"",false)) return 7;
    }
    std::vector<llama_token> generated;
    std::vector<bool> eog;
    for (int i=0;i<128;++i) {
        const float * logits = llama_get_logits_ith(ctx,-1);
        if (!logits) return 8;
        int top1=-1,top2=-1;
        // Ascending IDs preserve the greedy sampler's first-ID tie convention.
        for (int id=0;id<llama_vocab_n_tokens(vocab);++id) {
            if (top1<0 || logits[id]>logits[top1]) { top2=top1;top1=id; }
            else if (top2<0 || logits[id]>logits[top2]) top2=id;
        }
        const float first=logits[top1],second=logits[top2];
        const llama_token id=common_sampler_sample(sampler,ctx,-1);
        common_sampler_accept(sampler,id,true);
        const bool stop=llama_vocab_is_eog(vocab,id);
        generated.push_back(id);eog.push_back(stop);
        result["decisions"].push_back({{"output_index",i},{"sequence_position",n_past},
            {"committed_id",id},{"eog",stop},{"raw_target_top1",top1},
            {"raw_target_top2",top2},{"top1_logit",first},{"top2_logit",second},
            {"margin",first-second},{"n_past",n_past}});
        if (stop || i==127) break;
        all.push_back(id);
        result["partitions"].push_back({{"kind","decode"},{"position",n_past},
                                        {"input_ids",std::vector<llama_token>{id}},{"n_tokens",1}});
        if (!common_prompt_batch_decode(ctx,all,1,n_past,512,"",false)) return 9;
    }
    result["generated_ids"]=generated;
    result["eog"]=eog;
    std::ofstream out(output_path,std::ios::binary);
    out << result.dump(2) << "\n";
    if (!out) return 10;
    std::cout << "Mechanism capture complete: " << generated.size() << " committed IDs\n";
    return 0;
}
