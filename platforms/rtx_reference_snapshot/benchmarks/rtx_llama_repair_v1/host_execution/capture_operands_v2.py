"""Diagnostic-only operands; preserve graph construction and numerical policy."""
import hashlib


def apply(source, code):
    p = code / 'worker.cpp'
    before = p.read_text()
    anchor = '            j["occurrence"]=o.occurrences[o.phase+"/"+name]++;'
    assert before.count(anchor) == 1
    extra = r'''
            j["op_params_i32"]=std::vector<int32_t>(t->op_params,t->op_params+GGML_MAX_OP_PARAMS/sizeof(int32_t));
            j["operator_inputs"]=json::array();
            const bool matmul=t->op==GGML_OP_MUL_MAT &&
                (name.rfind("kq-",0)==0 || name.rfind("kqv-",0)==0);
            const bool softmax=t->op==GGML_OP_SOFT_MAX && name.rfind("kq_soft_max-",0)==0;
            for(int index=0;index<2;++index){
                if(!matmul && !(softmax && index==1))continue;
                auto* input=t->src[index];need(input && input->buffer,"operator input unavailable");
                const auto size=ggml_nbytes(input);
                const auto begin=reinterpret_cast<uintptr_t>(input->data);
                const auto end=begin+size;
                const auto output_begin=reinterpret_cast<uintptr_t>(t->data);
                need(end<=output_begin || output_begin+n<=begin,"operator input/output alias");
                if(softmax){
                    auto* base=input;while(base->view_src)base=base->view_src;
                    const bool copied=std::regex_match(std::string(base->name),std::regex(R"(^CUDA[0-9]+#attn_inp_kq_mask( \(view\))*#[0-9]+$)"));
                    j["mask_base"]=meta(base);j["mask_base"]["flags"]=base->flags;
                    j["mask_base"]["scheduler_copy"]=copied;
                    need(base->op==GGML_OP_NONE && ((base->flags&GGML_TENSOR_FLAG_INPUT)||copied),"mask is not a reviewed immutable graph input/copy");
                }
                need(size<=16ULL*1024*1024 && hs_repair::opt.files<hs_repair::opt.max_files &&
                    size<=hs_repair::opt.max_bytes-hs_repair::opt.bytes,"operand capture reservation");
                std::vector<uint8_t> operand(size);ggml_backend_tensor_get(input,operand.data(),0,size);
                const auto operand_serial=hs_repair::opt.files++;
                const auto relative=std::string("trace/")+std::to_string(operand_serial)+"_operand_"+std::to_string(index)+".bin";
                hs_repair::write_bytes(hs_repair::opt.root/relative,operand.data(),size);hs_repair::opt.bytes+=size;
                auto metadata=meta(input);metadata["source_index"]=index;metadata["file"]=relative;
                metadata["bytes"]=size;metadata["sha256"]=hash_file(hs_repair::opt.root/relative);
                metadata["capture_contract"]=matmul ? "non-inplace MUL_MAT input, disjoint output, copied before subsequent node evaluation" : "immutable graph-input mask; softmax data operand comes from preceding producing-node capture";
                j["operator_inputs"].push_back(metadata);
            }
'''
    after = before.replace(anchor, extra + anchor)
    p.write_text(after, encoding='utf-8', newline='\n')
    allocator = source / 'ggml/src/ggml-alloc.c'
    return {'kind': 'diagnostic_observer_only', 'numerical_policy_changed': False,
            'worker_before_sha256': hashlib.sha256(before.encode()).hexdigest(),
            'worker_after_sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
            'allocator_source_sha256': hashlib.sha256(allocator.read_bytes()).hexdigest(),
            'scheduler_source_sha256': hashlib.sha256((source/'ggml/src/ggml-backend.cpp').read_bytes()).hexdigest(),
            'source_review': 'ggml_op_can_inplace excludes MUL_MAT. SOFT_MAX data comes from producing-node capture. Backend split copies named CUDA<n>#attn_inp_kq_mask[ (view)]#<copy> are immutable input copies; ggml-backend.cpp sets input flags on them only when n_copies>1. Preserve root name/flags and disjointness checks.'}
