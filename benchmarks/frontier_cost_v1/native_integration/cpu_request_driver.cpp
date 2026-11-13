#include "llama.h"
#include "llama-kv-cache.h"
#include "ggml-backend.h"
#include <nlohmann/json.hpp>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

namespace integration_audit {
using J = nlohmann::json;
namespace F = std::filesystem;
static F::path root;
static bool enabled = false;
static int ordinal = 0;
static J events = J::array();
static std::map<llama_model *, std::string> model_roles;
static std::map<llama_context *, std::string> context_roles;
static std::map<llama_memory_t, llama_context *> memory_contexts;
static auto real_init = &llama_init_from_model;
static auto real_logits = &llama_get_logits_ith;
static auto real_remove = &llama_memory_seq_rm;
static auto real_clear = &llama_memory_clear;

static void require(bool ok, const char * message) {
    if (!ok) throw std::runtime_error(message);
}
static void bytes(const F::path & path, const void * data, size_t size) {
    require(!F::exists(path), "audit path already exists");
    std::ofstream out(path, std::ios::binary);
    out.write(static_cast<const char *>(data), std::streamsize(size));
    out.flush();
    require(bool(out), "audit write failed");
}
static std::string label(const std::string & role, const char * kind) {
    char n[32]; std::snprintf(n, sizeof(n), "%05d", ordinal++);
    return std::string(n) + "-" + role + "-" + kind;
}
static J geometry(llama_context * context) {
    auto * cache = dynamic_cast<llama_kv_cache *>(llama_get_memory(context));
    require(cache != nullptr, "audit requires dense cache");
    const auto & cells = cache->get_cells(0);
    const auto next = cells.used_max_p1();
    auto requirements = cache->phase_append_requirements(next, 1);
    require(requirements.size() == 1, "append guard after trim/reset");
    bool dense = cells.get_used() == next;
    for (uint32_t i = 0; i < next; ++i) {
        dense = dense && !cells.is_empty(i) && cells.pos_get(i) == int(i) && cells.seq_has(i, 0);
    }
    require(dense, "audit non-dense sequence");
    return {{"used", cells.get_used()}, {"used_max_p1", next},
            {"current_extent", cache->phase_current_extent()},
            {"next_q1_extents", requirements}, {"dense", dense},
            {"native_append_head_guard_passed", true},
            {"position_min", llama_memory_seq_pos_min(llama_get_memory(context), 0)},
            {"position_max", llama_memory_seq_pos_max(llama_get_memory(context), 0)}};
}
static void state(llama_context * context, const char * kind, const J & details = J::object()) {
    if (!enabled) return;
    llama_synchronize(context);
    const auto size = llama_state_seq_get_size(context, 0);
    std::vector<uint8_t> data(size);
    require(llama_state_seq_get_data(context, data.data(), size, 0) == size, "state capture incomplete");
    const auto name = label(context_roles.at(context), kind);
    bytes(root/(name + ".bin"), data.data(), data.size());
    events.push_back({{"kind", kind}, {"role", context_roles.at(context)},
                      {"file", name + ".bin"}, {"bytes", size},
                      {"geometry", geometry(context)}, {"details", details}});
}
static llama_context * init(llama_model * model, llama_context_params params) {
    auto * context = real_init(model, params);
    if (context) {
        context_roles[context] = model_roles.at(model);
        memory_contexts[llama_get_memory(context)] = context;
    }
    return context;
}
static float * logits(llama_context * context, int32_t row) {
    auto * data = real_logits(context, row);
    if (enabled && data) {
        const int n = llama_vocab_n_tokens(llama_model_get_vocab(llama_get_model(context)));
        for (int i = 0; i < n; ++i) require(std::isfinite(data[i]), "nonfinite requested vector");
        const auto name = label(context_roles.at(context), "requested-logits");
        bytes(root/(name + ".f32"), data, size_t(n)*sizeof(float));
        events.push_back({{"kind", "requested-logits"}, {"role", context_roles.at(context)},
                          {"row", row}, {"vocab", n}, {"file", name + ".f32"}});
    }
    return data;
}
static bool remove(llama_memory_t memory, llama_seq_id sequence, llama_pos p0, llama_pos p1) {
    const bool ok = real_remove(memory, sequence, p0, p1);
    if (ok && enabled) state(memory_contexts.at(memory), "trim", {{"sequence", sequence}, {"p0", p0}, {"p1", p1}});
    return ok;
}
static void clear(llama_memory_t memory, bool data) {
    real_clear(memory, data);
    if (enabled) state(memory_contexts.at(memory), "reset", {{"clear_data", data}});
}
static void begin(const F::path & directory) {
    require(!F::exists(directory), "fresh audit directory required");
    F::create_directories(directory); root = directory; ordinal = 0; events = J::array(); enabled = true;
}
}

static uint64_t phase_heavy_captures = 0;
#define llama_init_from_model integration_audit::init
#define llama_get_logits_ith integration_audit::logits
#define llama_memory_seq_rm integration_audit::remove
#define llama_memory_clear integration_audit::clear
#include "worker.cpp"
#undef llama_init_from_model
#undef llama_get_logits_ith
#undef llama_memory_seq_rm
#undef llama_memory_clear

static json checked_numerical_modules(const json & expected) {
    json modules = json::array();
    std::vector<std::string> seen;
    for (const auto & raw : linux_transfer::modules()) {
        if (!fs::is_regular_file(raw)) continue;
        const auto path = fs::canonical(raw); const auto name = path.filename().string();
        if ((name.rfind("libllama", 0) != 0 && name.rfind("libggml", 0) != 0) ||
            name.find(".so") == std::string::npos) continue;
        const auto hash = hash_file(path);
        need(std::find(expected.begin(), expected.end(), json(hash)) != expected.end(), "unexpected loaded numerical library");
        seen.push_back(hash); modules.push_back({{"name", name}, {"path", path.string()}, {"sha256", hash}});
    }
    auto wanted = expected.get<std::vector<std::string>>();
    std::sort(seen.begin(), seen.end()); std::sort(wanted.begin(), wanted.end());
    need(seen == wanted && seen.size() == 4, "incomplete loaded numerical library identity");
    return modules;
}

int main(int argc, char ** argv) {
    fs::path out;
    bool owns_output = false, initialized = false;
    llama_model * target = nullptr, * draft = nullptr;
    Pair pool;
    json result = {{"schema", "heterospec.cpu-request-integration.v1"}, {"status", "STARTED"},
                   {"GPU_qualification", "NOT_RUN"}, {"performance_claim", false},
                   {"entry_scope", "New CPU harness invoking unchanged worker provision/request; not original production CLI"},
                   {"requests", json::array()}};
    auto cleanup = [&]() {
        integration_audit::enabled = false;
        pool.draft.reset(); pool.target.reset();
        if (draft) { llama_model_free(draft); draft = nullptr; }
        if (target) { llama_model_free(target); target = nullptr; }
        if (initialized) { llama_backend_free(); initialized = false; }
    };
    try {
        need(argc == 3, "cpu_request_driver JOB OUT");
        const auto job = load(argv[1]); out = argv[2];
        need(!fs::exists(out), "fresh integration output");
        need(fs::create_directories(out), "create integration output"); owns_output = true;
        dump(out/"RESULT.json", result);
        need(job.at("synthetic_fixture") == true, "CPU driver only permits declared synthetic fixtures");
        need(hash_file(job.at("target_model").get<std::string>()) == job.at("target_model_sha256"), "target fixture hash changed");
        need(hash_file(job.at("draft_model").get<std::string>()) == job.at("draft_model_sha256"), "draft fixture hash changed");
        need(job.at("inputs").is_array() && !job.at("inputs").empty() && job.at("inputs").size() <= 16, "bounded input list");
        for (const auto & entry : job.at("inputs")) {
            const auto & input = entry.at("input");
            const auto cap = input.at("cap").get<int>();
            need(cap >= 1 && cap <= 128, "fixture cap range");
            need(input.at("prompt_ids").is_array() && !input.at("prompt_ids").empty(), "nonempty fixture prompt");
            need(input.at("prompt_ids").size() + size_t(cap) + 8 <= 1024, "fixture context capacity");
            for (const auto & token : input.at("prompt_ids")) need(token.get<int>() >= 0 && token.get<int>() < 128, "fixture token range");
        }
        phase_threads = 1; phase_target_reserve = 8; phase_draft_width = 4;
        phase_lowering = "LOCAL"; phase_proposal_mode = "live"; phase_observe = false;
        ggml_time_init(); ggml_backend_load_all(); llama_backend_init(); initialized = true;
        for (size_t i = 0; i < ggml_backend_dev_count(); ++i)
            need(ggml_backend_dev_type(ggml_backend_dev_get(i)) != GGML_BACKEND_DEVICE_TYPE_GPU, "CPU fixture scope forbids GPU backend");
        auto params = llama_model_default_params(); params.n_gpu_layers = 0;
        target = llama_model_load_from_file(job.at("target_model").get<std::string>().c_str(), params);
        draft = llama_model_load_from_file(job.at("draft_model").get<std::string>().c_str(), params);
        need(target && draft, "fixture model load");
        integration_audit::model_roles[target] = "target"; integration_audit::model_roles[draft] = "draft";
        const auto * tv = llama_model_get_vocab(target); const auto * dv = llama_model_get_vocab(draft);
        need(llama_vocab_n_tokens(tv) == 128, "fixture vocabulary scope");
        need(llama_vocab_n_tokens(tv) == llama_vocab_n_tokens(dv), "fixture vocab size differs");
        result["eog_ids"] = json::array();
        for (int i = 0; i < llama_vocab_n_tokens(tv); ++i) {
            need(std::string(llama_vocab_get_text(tv, i)) == std::string(llama_vocab_get_text(dv, i)), "fixture vocab strings differ");
            need(llama_vocab_is_eog(tv, i) == llama_vocab_is_eog(dv, i), "fixture EOG metadata differs");
            if (llama_vocab_is_eog(tv, i)) result["eog_ids"].push_back(i);
        }
        auto spec = ArmSpec{"CPU-native-request", "QB", 0, 32, job.at("k").get<int>(), true, true};
        need(spec.k == 3 || spec.k == 7, "M2 integration k3/k7 only");
        provision(pool, target, draft, spec, out/"pool");
        result["numerical_modules_before"] = checked_numerical_modules(job.at("numerical_library_sha256"));
        result["actual_context"] = {{"target_ubatch", llama_n_ubatch(pool.target->c)},
                                      {"draft_ubatch", llama_n_ubatch(pool.draft->c)},
                                      {"target_n_ctx", llama_n_ctx(pool.target->c)},
                                      {"draft_n_ctx", llama_n_ctx(pool.draft->c)},
                                      {"target_output_reserve", phase_target_reserve}};
        for (const auto & entry : job.at("inputs")) {
            const auto name = entry.at("name").get<std::string>();
            need(!name.empty() && name.find_first_of("/\\:") == std::string::npos && name.find("..") == std::string::npos, "unsafe fixture name");
            const auto dir = out/name; fs::create_directory(dir);
            integration_audit::begin(dir/"audit");
            auto r = request(target, draft, entry.at("input"), spec, "resident", false, "NATIVE", dir, pool);
            r["timing_scope"] = "Instrumented CPU integration only; not a performance measurement";
            integration_audit::state(pool.target->c, "terminal");
            integration_audit::state(pool.draft->c, "terminal");
            integration_audit::enabled = false;
            dump(dir/"AUDIT.json", integration_audit::events); dump(dir/"RECEIPT.json", r);
            result["requests"].push_back({{"name", name}, {"audit_events", integration_audit::events.size()},
                                          {"cycles", r.at("cycles").size()}, {"stop_reason", r.at("stop_reason")},
                                          {"tail_skipped", r.at("draft_tail_skipped")}, {"tail_recovered", r.at("draft_tail_recovered")}});
            dump(out/"RESULT.json", result);
        }
        result["numerical_modules_after"] = checked_numerical_modules(job.at("numerical_library_sha256"));
        need(result["numerical_modules_before"] == result["numerical_modules_after"], "loaded module identity changed");
        cleanup(); result["status"] = "COMPLETE"; result["normal_cleanup_returned"] = true;
        dump(out/"RESULT.json", result); std::cout << result.dump() << '\n'; return 0;
    } catch (const std::exception & error) {
        cleanup(); result["status"] = "FAILED"; result["error"] = error.what();
        if (owns_output) dump(out/"RESULT.json", result);
        std::cerr << error.what() << '\n'; return 2;
    }
}
