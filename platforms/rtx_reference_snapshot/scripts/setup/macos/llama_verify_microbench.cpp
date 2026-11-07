#include <llama.h>

#include <algorithm>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <numeric>
#include <random>
#include <string>
#include <vector>

using clock_type = std::chrono::steady_clock;

static void require_decode(llama_context * ctx, llama_batch batch, const char * phase) {
    const int rc = llama_decode(ctx, batch);
    if (rc != 0) {
        std::fprintf(stderr, "llama_decode failed during %s: %d\n", phase, rc);
        std::exit(2);
    }
    llama_synchronize(ctx);
}

static llama_batch make_batch(const std::vector<llama_token> & tokens, int start_pos, bool all_logits) {
    llama_batch batch = llama_batch_init((int) tokens.size(), 0, 1);
    batch.n_tokens = (int) tokens.size();
    for (int i = 0; i < batch.n_tokens; ++i) {
        batch.token[i] = tokens[i];
        batch.pos[i] = start_pos + i;
        batch.n_seq_id[i] = 1;
        batch.seq_id[i][0] = 0;
        batch.logits[i] = all_logits || i == batch.n_tokens - 1;
    }
    return batch;
}

int main(int argc, char ** argv) {
    if (argc != 4) {
        std::fprintf(stderr, "usage: %s MODEL.gguf REPETITIONS OUTPUT.csv\n", argv[0]);
        return 64;
    }
    const int repetitions = std::atoi(argv[2]);
    if (repetitions < 1) return 64;
    FILE * output = std::fopen(argv[3], "w");
    if (!output) return 1;

    llama_backend_init();
    llama_model_params mparams = llama_model_default_params();
    mparams.n_gpu_layers = -1;
    llama_model * model = llama_model_load_from_file(argv[1], mparams);
    if (!model) return 1;
    llama_context_params cparams = llama_context_default_params();
    cparams.n_ctx = 16384;
    cparams.n_batch = 2048;
    cparams.n_ubatch = 512;
    cparams.no_perf = true;
    llama_context * ctx = llama_init_from_model(model, cparams);
    if (!ctx) return 1;

    const std::vector<int> prefixes = {512, 2048, 8192};
    const std::vector<int> widths = {1, 2, 4, 6};
    std::mt19937 rng(20260903);
    std::fprintf(output, "prefix_tokens,verify_tokens,repetition,elapsed_us\n");
    for (int prefix : prefixes) {
        llama_memory_clear(llama_get_memory(ctx), true);
        int loaded = 0;
        while (loaded < prefix) {
            const int count = std::min(512, prefix - loaded);
            std::vector<llama_token> tokens(count, 1000);
            llama_batch batch = make_batch(tokens, loaded, false);
            require_decode(ctx, batch, "prefix");
            llama_batch_free(batch);
            loaded += count;
        }
        std::vector<int> schedule;
        for (int rep = 0; rep < repetitions; ++rep) {
            schedule.insert(schedule.end(), widths.begin(), widths.end());
        }
        std::shuffle(schedule.begin(), schedule.end(), rng);
        int seen[7] = {};
        for (int width : schedule) {
            std::vector<llama_token> tokens(width, 1001);
            llama_batch batch = make_batch(tokens, prefix, true);
            const auto start = clock_type::now();
            require_decode(ctx, batch, "verification");
            const auto end = clock_type::now();
            llama_batch_free(batch);
            const double us = std::chrono::duration<double, std::micro>(end - start).count();
            std::fprintf(output, "%d,%d,%d,%.3f\n", prefix, width, ++seen[width], us);
            std::fflush(output);
            if (!llama_memory_seq_rm(llama_get_memory(ctx), 0, prefix, -1)) {
                std::fprintf(stderr, "failed to roll back candidate KV\n");
                return 3;
            }
        }
    }
    llama_free(ctx);
    llama_model_free(model);
    llama_backend_free();
    std::fclose(output);
    return 0;
}
