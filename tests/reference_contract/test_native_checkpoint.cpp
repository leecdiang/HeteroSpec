#include "native_checkpoint.hpp"
#include "native_guard.hpp"
#include "ggml.h"
#include <iostream>
using namespace hs_reference_batching;
static int checks=0;
static void check(bool value){++checks;if(!value)throw std::runtime_error("check failed: "+std::to_string(checks));}
int main(int argc,char **argv){
 try {
    if(argc!=2)throw std::runtime_error("supply synthetic GGUF path");
    llama_backend_init();
    auto mp=llama_model_default_params();mp.n_gpu_layers=0;
    std::unique_ptr<llama_model,decltype(&llama_model_free)> model(llama_model_load_from_file(argv[1],mp),llama_model_free);
    check(bool(model));
    auto cp=llama_context_default_params();cp.n_ctx=128;cp.n_batch=32;cp.n_ubatch=32;cp.n_seq_max=1;cp.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_DISABLED;cp.n_threads=1;cp.n_threads_batch=1;
    NativeCheckpointOwner owner(model.get(),cp,"synthetic-cpu-test","ordinary-cpu"),control(model.get(),cp,"synthetic-cpu-test","ordinary-cpu");
    auto accept=[](const NativeCapsule&){return true;};
    check(owner.append({1,2,3},{4},owner.generation(),accept).committed);
    check(control.append({1,2,3},{4},control.generation(),accept).committed);
    auto before=owner.snapshot();check(before.same(control.snapshot()));check(before.output_rows==3);check(!before.output_logits.empty());
    auto fail=owner.append({4,5},{6},owner.generation(),[](const NativeCapsule&){return false;});
    check(!fail.committed && fail.restored);check(owner.clean());check(owner.snapshot().same(before));
    check(owner.snapshot().pending==std::vector<llama_token>{4});
    auto boom=owner.append({4},{},owner.generation(),accept,[]{throw std::runtime_error("injected predecode failure");});
    check(!boom.committed && boom.restored);check(owner.snapshot().same(before));
    auto reenter=owner.append({4},{},owner.generation(),[&](const NativeCapsule&){owner.invalidate();return true;});
    check(!reenter.committed && reenter.restored);check(owner.snapshot().same(before));
    check(owner.append({4,5},{6},owner.generation(),accept).committed);
    check(control.append({4,5},{6},control.generation(),accept).committed);
    check(owner.snapshot().same(control.snapshot()));
    owner.invalidate();check(!owner.clean());owner.restore();check(owner.clean());check(owner.snapshot().same(control.snapshot()));
    bool stale=false;try{owner.append({6},{},0,accept);}catch(const std::runtime_error&){stale=true;}check(stale);
    bool invalid=false;try{owner.append({-1},{},owner.generation(),accept);}catch(const std::invalid_argument&){invalid=true;}check(invalid);check(owner.clean());
    PackingRegistry registry;
    int descriptions=0;
    PackingBinding binding;binding.registry=&registry;
    binding.describe=[&](const void*,const void*){++descriptions;return PackingRequest{};};
    auto checkpoint=owner.snapshot();
    const auto rejected=owner.append({6,7,8,9,10,11,12,13},{14},owner.generation(),accept,{},
        [&](llama_context * ctx,llama_batch batch){return guarded_decode(ctx,batch,binding);});
    check(descriptions>0);check(!rejected.committed && rejected.restored);
    check(owner.clean());check(owner.snapshot().same(checkpoint));
    check(hs_get_packing_binding()==nullptr);
    check(owner.append({6},{7},owner.generation(),accept).committed);
    check(control.append({6},{7},control.generation(),accept).committed);
    check(owner.snapshot().same(control.snapshot()));
    // Test-only retention of legacy tiles. This deliberately is NOT a GPU
    // qualification and is never shipped in a production registry.
    NativeCheckpointOwner reuse(model.get(),cp,"synthetic-cpu-test","test-only-tiled");
    PackingBinding tiled;tiled.registry=&registry;
    tiled.describe=[](const void*,const void * activation){
        const auto * a=static_cast<const ggml_tensor*>(activation);
        PackingRequest r;r.deployment={"cpu","synthetic","test","llama","tiny","test-only"};
        r.state.deployment=r.deployment;r.state.clean=true;r.state.recipe="test-only";r.state.prefix_identity="test";
        r.input.columns=a->ne[1];r.prefix.status=PrefixStatus::supported;r.prefix.extents.assign(a->ne[1],256);
        return r;
    };
    tiled.qualified_tiled=[](const PackingRequest&){return true;};
    check(reuse.append({1,2,3,4,5,6,7,8},{9},reuse.generation(),accept,{},
        [&](llama_context * ctx,llama_batch batch){return guarded_decode(ctx,batch,tiled);}).committed);
    auto reuse_before=reuse.snapshot();descriptions=0;
    auto changed=reuse.append({9,10,11,12,13,14,15,16},{},reuse.generation(),accept,{},
        [&](llama_context * ctx,llama_batch batch){return guarded_decode(ctx,batch,binding);});
    check(descriptions>0);check(!changed.committed && changed.restored);check(reuse.snapshot().same(reuse_before));
    auto flash_cp=cp;flash_cp.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_ENABLED;
    NativeCheckpointOwner flash(model.get(),flash_cp,"synthetic-cpu-test","unsupported-flash");
    auto flash_before=flash.snapshot();descriptions=0;
    const auto flash_result=flash.append({1,2,3,4,5,6,7,8},{},flash.generation(),accept,{},
        [&](llama_context * ctx,llama_batch batch){return guarded_decode(ctx,batch,binding);});
    check(!flash_result.committed && flash_result.restored);check(descriptions==0);
    check(flash.snapshot().same(flash_before));
    // Direct public guard preflight, independently of the Owner's validation.
    std::unique_ptr<llama_context,decltype(&llama_free)> raw(llama_init_from_model(model.get(),cp),llama_free);
    auto batch=llama_batch_init(1,0,1);batch.n_tokens=1;batch.token[0]=1;batch.pos[0]=0;
    batch.n_seq_id[0]=1;batch.seq_id[0][0]=0;batch.logits[0]=true;
    check(hs_native_decode_supported(raw.get(),batch));
    batch.token[0]=-1;check(!hs_native_decode_supported(raw.get(),batch));batch.token[0]=1;
    batch.seq_id[0][0]=1;check(!hs_native_decode_supported(raw.get(),batch));batch.seq_id[0][0]=0;
    batch.logits[0]=false;check(!hs_native_decode_supported(raw.get(),batch));batch.logits[0]=true;
    batch.pos[0]=2;check(!hs_native_decode_supported(raw.get(),batch));batch.pos[0]=0;
    { NativeScope nested(true);check(!hs_native_decode_supported(raw.get(),batch)); }
    check(hs_native_decode_supported(raw.get(),batch));
    { PackingScope nested(binding);check(!hs_native_decode_supported(raw.get(),batch)); }
    check(hs_native_decode_supported(raw.get(),batch));llama_batch_free(batch);
    std::cout<<"native CPU checkpoint checks: "<<checks<<"\n";
 }catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}
}
