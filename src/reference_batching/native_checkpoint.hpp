#pragma once
#include "llama.h"
#include <algorithm>
#include <cstdint>
#include <cstring>
#include <functional>
#include <memory>
#include <mutex>
#include <stdexcept>
#include <string>
#include <vector>

namespace hs_reference_batching {
struct NativeCapsule {
    std::string deployment, recipe;
    std::vector<llama_token> tokens, pending;
    std::vector<llama_pos> positions;
    std::vector<uint8_t> memory;
    std::vector<float> output_logits;
    int32_t output_rows=0;
    bool same(const NativeCapsule & b) const {
        return deployment==b.deployment && recipe==b.recipe && tokens==b.tokens &&
            pending==b.pending && positions==b.positions && memory==b.memory &&
            output_rows==b.output_rows && output_logits.size()==b.output_logits.size() &&
            (output_logits.empty() || std::memcmp(output_logits.data(),b.output_logits.data(),output_logits.size()*sizeof(float))==0);
    }
};
struct NativeTransactionResult { bool committed=false, restored=false; std::string error; };

// Owns the context. Only greedy, contiguous, sequence-zero inference is admitted.
// Logits live in the capsule because this source's state_write_data omits them.
// Model and verifier lifetimes are owned by the host. No claim of reference
// equivalence is made by constructing this class or matching serialized bytes.
class NativeCheckpointOwner {
    using Context=std::unique_ptr<llama_context,decltype(&llama_free)>;
    llama_model * model_;
    llama_context_params params_;
    Context context_{nullptr,llama_free};
    NativeCapsule current_, checkpoint_;
    bool clean_=false, busy_=false;
    uint64_t generation_=0;
    mutable std::recursive_mutex mutex_;
    struct Busy {
        bool & value;
        explicit Busy(bool & v):value(v) { if(v)throw std::runtime_error("reentrant native transaction");v=true; }
        ~Busy(){value=false;}
    };
    Context make_context() {
        auto * raw=llama_init_from_model(model_,params_);
        if(!raw)throw std::runtime_error("context creation failed");
        return Context(raw,llama_free);
    }
    static std::vector<uint8_t> serialize(llama_context * ctx) {
        llama_synchronize(ctx);
        std::vector<uint8_t> bytes(llama_state_get_size(ctx));
        if(bytes.empty() || llama_state_get_data(ctx,bytes.data(),bytes.size())!=bytes.size())
            throw std::runtime_error("state export incomplete");
        return bytes;
    }
    void check_positions(llama_context * ctx,const NativeCapsule & c) const {
        auto mem=llama_get_memory(ctx);
        if(!mem)throw std::runtime_error("memory required");
        const auto lo=llama_memory_seq_pos_min(mem,0),hi=llama_memory_seq_pos_max(mem,0);
        if(c.positions.empty()) { if(lo!=-1 || hi!=-1)throw std::runtime_error("nonempty initial state"); }
        else if(lo!=c.positions.front() || hi!=c.positions.back())throw std::runtime_error("position readback mismatch");
    }
    void restore_impl() {
        clean_=false;++generation_;
        // Build separately; do not repair a partially failed context in place.
        auto fresh=make_context();
        if(llama_state_set_data(fresh.get(),checkpoint_.memory.data(),checkpoint_.memory.size())!=checkpoint_.memory.size())
            throw std::runtime_error("short state import");
        if(serialize(fresh.get())!=checkpoint_.memory)throw std::runtime_error("state readback mismatch");
        check_positions(fresh.get(),checkpoint_);
        context_.swap(fresh);
        current_=checkpoint_; // Includes independent logits and pending metadata.
        clean_=true;
    }
public:
    NativeCheckpointOwner(llama_model * model,llama_context_params params,
                          std::string deployment,std::string recipe):model_(model),params_(params) {
        if(!model || deployment.empty() || recipe.empty() || params.n_seq_max!=1 || params.embeddings)
            throw std::invalid_argument("single-sequence greedy deployment required");
        if(params.samplers || params.n_samplers)throw std::invalid_argument("backend samplers unsupported");
        context_=make_context();current_.deployment=std::move(deployment);current_.recipe=std::move(recipe);
        check_positions(context_.get(),current_);current_.memory=serialize(context_.get());
        checkpoint_=current_;clean_=true;
    }
    bool clean() const { std::lock_guard<std::recursive_mutex> lock(mutex_);return clean_; }
    uint64_t generation() const { std::lock_guard<std::recursive_mutex> lock(mutex_);return generation_; }
    NativeCapsule snapshot() const {
        std::lock_guard<std::recursive_mutex> lock(mutex_);
        if(busy_ || !clean_)throw std::runtime_error("state not committed");
        return current_;
    }
    void invalidate() {
        std::lock_guard<std::recursive_mutex> lock(mutex_);Busy busy(busy_);
        clean_=false;++generation_;
    }
    void restore() {
        std::lock_guard<std::recursive_mutex> lock(mutex_);Busy busy(busy_);restore_impl();
    }
    NativeTransactionResult append(const std::vector<llama_token> & tokens,
            const std::vector<llama_token> & pending,
            uint64_t expected_generation,
            const std::function<bool(const NativeCapsule &)> & verify,
            const std::function<void()> & before_decode={},
            const std::function<int(llama_context *,llama_batch)> & decode={}) {
        std::lock_guard<std::recursive_mutex> lock(mutex_);Busy busy(busy_);
        if(!clean_ || generation_!=expected_generation)throw std::runtime_error("stale native admission");
        if(tokens.empty() || tokens.size()>llama_n_batch(context_.get()) || !verify)
            throw std::invalid_argument("invalid append request");
        const int32_t vocab=llama_vocab_n_tokens(llama_model_get_vocab(model_));
        for(auto token:tokens)if(token<0 || token>=vocab)throw std::invalid_argument("token out of vocabulary");
        for(auto token:pending)if(token<0 || token>=vocab)throw std::invalid_argument("pending token out of vocabulary");
        if(current_.tokens.size()+tokens.size()>llama_n_ctx(context_.get()))throw std::invalid_argument("capacity exceeded");
        clean_=false;++generation_;
        try {
            if(serialize(context_.get())!=current_.memory)throw std::runtime_error("state changed outside owner");
            check_positions(context_.get(),current_);
            auto batch=llama_batch_init(int32_t(tokens.size()),0,1);
            struct BatchFree { llama_batch & b; ~BatchFree(){llama_batch_free(b);} } free{batch};
            batch.n_tokens=int32_t(tokens.size());
            for(size_t i=0;i<tokens.size();++i) {
                batch.token[i]=tokens[i];batch.pos[i]=llama_pos(current_.tokens.size()+i);
                batch.n_seq_id[i]=1;batch.seq_id[i][0]=0;batch.logits[i]=true;
            }
            if(before_decode)before_decode();
            // C++ catches exceptions before any future C/Python wrapper boundary.
            const int rc=decode ? decode(context_.get(),batch) : llama_decode(context_.get(),batch);
            if(rc)throw std::runtime_error("llama_decode failed: "+std::to_string(rc));
            llama_synchronize(context_.get());
            NativeCapsule next=current_;
            next.tokens.insert(next.tokens.end(),tokens.begin(),tokens.end());next.pending=pending;
            for(size_t i=current_.positions.size();i<next.tokens.size();++i)next.positions.push_back(llama_pos(i));
            next.output_rows=int32_t(tokens.size());next.output_logits.clear();
            for(int32_t i=0;i<batch.n_tokens;++i) {
                const auto * row=llama_get_logits_ith(context_.get(),i);
                if(!row)throw std::runtime_error("missing output row");
                next.output_logits.insert(next.output_logits.end(),row,row+vocab);
            }
            next.memory=serialize(context_.get());check_positions(context_.get(),next);
            if(!verify(next))throw std::runtime_error("reference verification rejected");
            current_=next;checkpoint_=next;clean_=true;
            return {true,false,{}};
        } catch(const std::exception & error) {
            const std::string message=error.what();
            try { restore_impl();return {false,true,message}; }
            catch(const std::exception & restore_error) {return {false,false,message+"; restore: "+restore_error.what()};}
        } catch(...) {
            try {restore_impl();return {false,true,"unknown native failure"};}
            catch(...) {return {false,false,"unknown native and restoration failure"};}
        }
    }
};
} // namespace hs_reference_batching
