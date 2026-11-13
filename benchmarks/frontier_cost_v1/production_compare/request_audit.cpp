#include "llama.h"
#include "llama-model.h"
#include "llama-kv-cache.h"
#include <nlohmann/json.hpp>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>
extern "C" {
#include "hash/sha256/sha256.h"
llama_model * __real_llama_model_load_from_file(const char *, llama_model_params);
llama_context * __real_llama_init_from_model(llama_model *, llama_context_params);
bool __real_llama_memory_seq_rm(llama_memory_t, llama_seq_id, llama_pos, llama_pos);
void __real_llama_memory_clear(llama_memory_t, bool);
void __real_llama_free(llama_context *);
}

namespace pair_audit {
using J = nlohmann::json;
namespace F = std::filesystem;
static J config, job, events = J::array(), contexts = J::array();
static F::path root;
static std::map<llama_model *, std::string> model_roles;
static std::map<llama_context *, std::string> roles;
static std::map<llama_memory_t, llama_context *> owners;
static llama_context * target = nullptr;
static llama_context * draft = nullptr;
static int request_index = -1, ordinal = 0, model_count = 0;
static uint64_t bytes_written = 0;
static bool initialized = false, draft_reset_due = false, closed = false;

static void need(bool ok, const char * message) {
    if (!ok) throw std::runtime_error(message);
}
static J read(const F::path & path) {
    std::ifstream stream(path); J value; stream >> value;
    need(bool(stream), "audit JSON input"); return value;
}
static std::string hash(const F::path & path) {
    sha256_t state; sha256_init(&state);
    std::ifstream stream(path, std::ios::binary);
    need(bool(stream), "audit hash input");
    std::vector<char> block(1024 * 1024);
    while (stream) {
        stream.read(block.data(), block.size());
        sha256_update(&state, reinterpret_cast<const unsigned char *>(block.data()), size_t(stream.gcount()));
    }
    need(stream.eof(), "audit hash read");
    unsigned char value[32]; sha256_final(&state, value);
    const char * hex = "0123456789abcdef"; std::string result;
    for (auto byte : value) { result += hex[byte >> 4]; result += hex[byte & 15]; }
    return result;
}
static void start() {
    if (initialized) return;
    const char * path = std::getenv("HETEROSPEC_PAIR_AUDIT");
    need(path && *path, "capture binary requires explicit audit config");
    config = read(path); job = read(config.at("job_path").get<std::string>());
    need(hash(config.at("job_path").get<std::string>()) == config.at("job_sha256"), "audit job binding");
    need(job.at("proposal_mode") == "live" && job.at("k") == 7 && job.at("draft") == true,
         "audit requires live k7 production requests");
    need(job.at("inputs").size() == 2, "audit fixed two requests");
    for (const auto & input : job.at("inputs")) {
        need(input.at("capture") == true && input.at("input").at("cap") == 16, "capture-only cap16 observer");
    }
    root = F::path(config.at("output_path").get<std::string>()) / "request_audit";
    need(!F::exists(root), "fresh production audit directory");
    F::create_directories(root); initialized = true;
}
static J geometry(llama_context * context) {
    auto * cache = dynamic_cast<llama_kv_cache *>(llama_get_memory(context));
    need(cache && cache->type_k() == GGML_TYPE_F16 && cache->type_v() == GGML_TYPE_F16, "audit dense F16 cache");
    const auto & cells = cache->get_cells(0);
    const auto next = cells.used_max_p1();
    const auto extents = cache->phase_append_requirements(next, 1);
    need(extents.size() == 1 && cells.get_used() == next, "audit native append/head guard");
    for (uint32_t index = 0; index < next; ++index) {
        need(!cells.is_empty(index) && cells.pos_get(index) == int(index) && cells.seq_has(index, 0), "audit dense positions");
    }
    return {{"used", cells.get_used()}, {"next", next}, {"extent", cache->phase_current_extent()},
            {"next_q1_extents", extents}, {"native_head_guard", true}};
}
static void capture(llama_context * context, const char * kind, J details = J::object()) {
    need(request_index >= 0 && !closed, "audit capture outside request");
    const auto role = roles.at(context);
    const auto name = job.at("inputs").at(request_index).at("name").get<std::string>();
    llama_synchronize(context);
    const auto size = llama_state_seq_get_size(context, 0);
    const auto & bound = config.at("storage").at("requests").at(request_index);
    need(size <= bound.at(role + "_state_bytes_ceiling").get<uint64_t>(), "native state exceeds declared structure ceiling");
    need(bytes_written + size <= config.at("storage").at("sidecar_bytes_per_process").get<uint64_t>(), "audit sidecar byte ceiling");
    std::vector<uint8_t> data(size);
    need(llama_state_seq_get_data(context, data.data(), size, 0) == size, "audit sequence export incomplete");
    const auto relative = name + "/" + std::to_string(ordinal++) + "-" + role + "-" + kind + ".bin";
    const auto path = root / relative;
    need(!F::exists(path), "audit capture overwrite"); F::create_directories(path.parent_path());
    std::ofstream stream(path, std::ios::binary); stream.write(reinterpret_cast<const char *>(data.data()), size); stream.flush();
    need(bool(stream), "audit state write"); bytes_written += size;
    J event = {{"request", name}, {"role", role}, {"kind", kind}, {"file", relative}, {"bytes", size},
               {"geometry", geometry(context)}, {"details", details}};
    events.push_back(event);
    std::ofstream log(root / "events.jsonl", std::ios::app); log << event.dump() << '\n'; log.flush();
    need(bool(log), "audit event log");
}
static void terminal(const char * boundary) {
    need(target && draft && !draft_reset_due, "ambiguous terminal boundary");
    capture(target, "terminal", {{"boundary", boundary}});
    capture(draft, "terminal", {{"boundary", boundary}});
}
}

extern "C" llama_model * __wrap_llama_model_load_from_file(const char * path, llama_model_params params) {
    using namespace pair_audit;
    start(); need(model_count < 2, "unexpected model creation");
    const std::string role = model_count++ == 0 ? "target" : "draft";
    need(F::canonical(path) == F::canonical(job.at(role + "_model").get<std::string>()), "actual model path differs");
    need(hash(path) == job.at(role + "_sha256"), "actual model SHA differs");
    auto * model = __real_llama_model_load_from_file(path, params);
    need(model, "model load failed");
    const auto & hp = model->hparams;
    need(hp.n_layer() == (role == "target" ? 36U : 28U) && hp.n_embd_k_gqa() == 1024 && hp.n_embd_v_gqa() == 1024,
         "unexpected authenticated model structure");
    need(hp.n_pos_per_embd() == 1 && hp.ple_n_heads == 0, "unsupported extended sequence metadata");
    model_roles[model] = role; return model;
}

extern "C" llama_context * __wrap_llama_init_from_model(llama_model * model, llama_context_params params) {
    using namespace pair_audit;
    const auto role = model_roles.at(model);
    need(roles.size() < 2, "unexpected extra context");
    auto * context = __real_llama_init_from_model(model, params);
    need(context && llama_n_ctx(context) == 1024 && llama_n_ubatch(context) == (role == "target" ? 32U : 4U), "actual context mismatch");
    if (role == "target") { need(!target, "second target context"); target = context; }
    else { need(!draft, "second draft context"); draft = context; }
    roles[context] = role; owners[llama_get_memory(context)] = context;
    contexts.push_back({{"role", role}, {"n_ctx", llama_n_ctx(context)}, {"n_ubatch", llama_n_ubatch(context)}});
    return context;
}

extern "C" void __wrap_llama_memory_clear(llama_memory_t memory, bool data) {
    using namespace pair_audit;
    auto * context = owners.at(memory);
    if (context == target) {
        if (request_index >= 0) terminal("before_next_target_clear");
        need(++request_index < 2 && !draft_reset_due, "unexpected request reset");
        draft_reset_due = true;
    } else {
        need(context == draft && draft_reset_due, "draft reset without target reset");
        draft_reset_due = false;
    }
    __real_llama_memory_clear(memory, data);
    capture(context, "reset", {{"clear_data", data}});
}

extern "C" bool __wrap_llama_memory_seq_rm(llama_memory_t memory, llama_seq_id sequence, llama_pos p0, llama_pos p1) {
    using namespace pair_audit;
    need(request_index >= 0 && !draft_reset_due && sequence == 0 && p0 >= 0 && p1 == -1, "unexpected trim lifecycle");
    bool ok = __real_llama_memory_seq_rm(memory, sequence, p0, p1);
    need(ok, "native trim failed");
    capture(owners.at(memory), "trim", {{"sequence", sequence}, {"p0", p0}, {"p1", p1}});
    return ok;
}

extern "C" void __wrap_llama_free(llama_context * context) {
    using namespace pair_audit;
    if (context && roles.count(context) && !closed) {
        need(request_index == 1, "context free before both planned requests");
        terminal("before_first_context_free"); closed = true;
        J result = {{"schema", "heterospec.original-entry-sequence-audit.v1"},
                    {"status", "OBSERVATIONS_CLOSED_NOT_ENTRY_QUALIFIED"},
                    {"job_sha256", config.at("job_sha256")}, {"requests_seen", request_index + 1},
                    {"model_loads", model_count}, {"contexts", contexts}, {"events", events},
                    {"state_bytes", bytes_written}, {"performance_admitted", false}};
        const auto path = root / "AUDIT.json"; need(!F::exists(path), "audit footer overwrite");
        std::ofstream stream(path); stream << result.dump(2) << '\n'; stream.flush();
        need(bool(stream), "audit footer write");
    }
    __real_llama_free(context);
}
