#pragma once
// Diagnostic capture of one actual q8 model projection. Not clean admission.
// Include after ggml/ggml-backend and nlohmann/json. Never slices q32 into q8.
#include "ggml.h"
#include "ggml-backend.h"
#include <nlohmann/json.hpp>
#include <windows.h>
#include <filesystem>
#include <fstream>
#include <optional>
#include <stdexcept>
#include <vector>
#include <cstdint>
#include <limits>
#include <cmath>
#include <cstring>

namespace hs_q8_capture {
using json = nlohmann::ordered_json;
namespace fs = std::filesystem;
inline void need(bool ok, const char * text) { if (!ok) throw std::runtime_error(text); }
inline void write_new(const fs::path & path, const void * data, size_t bytes) {
    need(bytes > 0 && bytes <= std::numeric_limits<DWORD>::max(), "capture write size");
    HANDLE file = CreateFileW(path.c_str(), GENERIC_WRITE, 0, nullptr, CREATE_NEW,
                              FILE_ATTRIBUTE_NORMAL, nullptr);
    need(file != INVALID_HANDLE_VALUE, "capture output already exists/unavailable");
    DWORD done = 0;
    const bool okay = WriteFile(file, data, DWORD(bytes), &done, nullptr) && done == bytes && FlushFileBuffers(file);
    CloseHandle(file);
    need(okay, "capture write incomplete");
}
inline ggml_backend_buffer_t actual_buffer(const ggml_tensor * t) {
    const ggml_tensor * current = t;
    for (int n = 0; current && n < 16; ++n, current = current->view_src)
        if (current->buffer) return current->buffer;
    return nullptr;
}
inline json tensor_meta(const ggml_tensor * t) {
    need(t != nullptr, "capture tensor absent");
    auto buffer = actual_buffer(t);
    need(buffer != nullptr && t->data != nullptr, "capture tensor unallocated");
    auto buft = ggml_backend_buffer_get_type(buffer);
    auto device = ggml_backend_buft_get_device(buft);
    need(device != nullptr, "capture tensor device absent");
    const auto base = uintptr_t(ggml_backend_buffer_get_base(buffer));
    const auto data = uintptr_t(t->data);
    const auto size = ggml_backend_buffer_get_size(buffer);
    const auto bytes = ggml_nbytes(t);
    need(data >= base && data - base <= size && bytes <= size - (data - base), "capture allocation span");
    return {{"name", t->name}, {"type", ggml_type_name(t->type)},
        {"ne", {t->ne[0], t->ne[1], t->ne[2], t->ne[3]}},
        {"nb", {t->nb[0], t->nb[1], t->nb[2], t->nb[3]}},
        {"contiguous", ggml_is_contiguous(t)}, {"tensor_bytes", bytes},
        {"view", t->view_src != nullptr}, {"buffer_type", ggml_backend_buft_name(buft)},
        {"device_name", ggml_backend_dev_name(device)},
        {"device_description", ggml_backend_dev_description(device)},
        {"device_type", int(ggml_backend_dev_type(device))},
        {"buffer_usage", int(ggml_backend_buffer_get_usage(buffer))},
        {"allocation_bytes", size}, {"allocation_tensor_bytes", ggml_backend_buffer_get_alloc_size(buffer,t)},
        {"data_offset", data-base}};
}

struct Capture {
    fs::path root;
    std::string arm;
    std::string weight_name = "blk.0.attn_q.weight";
    std::string required_phase = "VERIFY";
    size_t byte_cap = 0;
    bool armed = false, completed = false;
    const ggml_tensor * pending = nullptr;
    json before;

    Capture() = default;
    explicit Capture(const json & contract) {
        need(contract.at("schema") == "heterospec.actual-q8-capture.v1", "capture schema");
        arm = contract.at("arm");
        need(arm == "A" || arm == "B", "capture oracle arm");
        need(contract.at("q") == 8 && contract.at("weight_type") == "Q8_0" && contract.at("activation_type") == "F32", "capture recipe");
        need(contract.at("allow_derived_input") == false, "derived inputs forbidden");
        root = contract.at("output_dir").get<std::string>();
        weight_name = contract.at("weight_name");
        required_phase = contract.at("phase");
        byte_cap = contract.at("capture_byte_reservation").get<size_t>();
        need(byte_cap > 0 && !fs::exists(root), "capture output/reservation");
        fs::create_directories(root);
        armed = true;
    }
    std::optional<bool> callback(ggml_tensor * t, bool ask, const std::string & phase, int base, int caller_rows) {
        if (!armed || completed || phase != required_phase) return std::nullopt;
        if (!ask) {
            if (t != pending) return std::nullopt;
            need(pending != nullptr, "capture unmatched completion");
            auto * w = t->src[0]; auto * x = t->src[1];
            const auto wb = ggml_nbytes(w), xb = ggml_nbytes(x), yb = ggml_nbytes(t);
            constexpr size_t metadata_margin=65536;
            need(byte_cap>metadata_margin && wb<=byte_cap-metadata_margin && xb<=byte_cap-metadata_margin-wb && yb<=byte_cap-metadata_margin-wb-xb, "capture reservation exceeded");
            std::vector<char> weights(wb), input(xb), output(yb);
            ggml_backend_tensor_get(w,weights.data(),0,wb);
            ggml_backend_tensor_get(x,input.data(),0,xb);
            ggml_backend_tensor_get(t,output.data(),0,yb);
            for (size_t i=0;i<yb/sizeof(float);++i) {
                float value; std::memcpy(&value,output.data()+i*sizeof(float),sizeof(value));
                need(std::isfinite(value), "capture nonfinite output");
            }
            write_new(root/"weight.bin",weights.data(),wb);
            write_new(root/"input.bin",input.data(),xb);
            write_new(root/"output.bin",output.data(),yb);
            json receipt={{"schema","heterospec.actual-q8-capture.receipt.v1"},
                {"status","CAPTURED_ACTUAL_MODEL_PROJECTION_NOT_YET_QUALIFIED"},
                {"arm",arm},{"phase",phase},{"base",base},{"caller_rows",caller_rows},
                {"actual_q",8},{"source_origin","ACTUAL_NATIVE_Q8_NODE_NO_Q32_SLICING"},
                {"weight",tensor_meta(w)},{"activation",tensor_meta(x)},{"output",tensor_meta(t)},
                {"pre_execution_descriptor",before},{"raw_capture_bytes",wb+xb+yb},
                {"metadata_reservation_bytes",metadata_margin},
                {"capture_only",true},{"clean_guard_attested",false},
                {"dispatch_attested",false},{"dispatch","UNKNOWN_CALLBACK_ONLY"},
                {"quantized_activation_attested",false},{"kernel_launch_count_attested",false},
                {"timing_admitted",false}};
            auto text=receipt.dump(2);
            write_new(root/"receipt.json",text.data(),text.size());
            completed=true;pending=nullptr;
            return false;
        }
        if (pending || t->op != GGML_OP_MUL_MAT || !t->src[0] || !t->src[1]) return std::nullopt;
        auto * w=t->src[0]; auto * x=t->src[1];
        if (std::string(w->name)!=weight_name || w->type!=GGML_TYPE_Q8_0 || x->type!=GGML_TYPE_F32 || t->type!=GGML_TYPE_F32) return std::nullopt;
        const auto q=x->ne[1]*x->ne[2]*x->ne[3];
        if(q!=8) return std::nullopt;
        need(caller_rows==8, "capture native q8 must be requested by actual eight-row caller");
        need(w->ne[2]==1 && w->ne[3]==1 && x->ne[0]==w->ne[0] && t->ne[0]==w->ne[1], "capture native projection shape");
        need(ggml_is_contiguous(w) && ggml_is_contiguous(x) && ggml_is_contiguous(t), "capture unsupported stride");
        need(w->ne[0]%512==0 && w->ne[1]%2==0 && t->ne[1]*t->ne[2]*t->ne[3]==8, "capture narrow operator geometry");
        for(auto * tensor:{w,x,t}) {
            auto buffer=actual_buffer(tensor);
            need(buffer!=nullptr,"capture missing actual allocation");
            auto device=ggml_backend_buft_get_device(ggml_backend_buffer_get_type(buffer));
            need(device && ggml_backend_dev_type(device)==GGML_BACKEND_DEVICE_TYPE_GPU,"capture actual operand not GPU");
        }
        before={{"weight",tensor_meta(w)},{"activation",tensor_meta(x)},{"output",tensor_meta(t)},
            {"op",ggml_op_name(t->op)},{"arm",arm},{"q",q}};
        pending=t;
        return true; // scheduler supplies the completed output in the following ask=false callback
    }
    void require_complete() const { need(armed && completed && pending==nullptr,"actual q8 capture not completed"); }
};
inline Capture * active=nullptr;
inline std::optional<bool> callback(ggml_tensor * t,bool ask,const std::string & phase,int base,int caller_rows) {
    return active?active->callback(t,ask,phase,base,caller_rows):std::nullopt;
}
}
