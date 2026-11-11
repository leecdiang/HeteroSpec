"""Adapt PR191's known-token probe, not its numerical kernels or reference.

Host still configures real context capacity/output reservation and original
producer, compiles, observes capacity, and qualifies the deployment. This source
overlay cannot turn a Python capacity label into an allocated native context.
"""
from pathlib import Path
import argparse
from stage_native import digest, once
from design import require, write_new


def patch(text):
    text=once(text,'if(req.contains("known_suffix")) {','''if(req.contains("known_suffix")) {
 const bool phase1_clean=req.value("phase1_clean",false);
 const auto phase1_capacity=llama_n_ctx(ctx);
 if(phase1_capacity!=req.at("capacity").get<unsigned>())throw std::runtime_error("native capacity mismatch");
 if(phase1_capacity!=1024&&phase1_capacity!=4096)throw std::runtime_error("phase1 capacity profile");
 if(req.value("rollback",0)!=0)throw std::runtime_error("use separate retained rollback controls");''')
    text=once(text,'if(input.size()+prelude.size()+suffix.size()+2>1024)throw std::runtime_error("probe context");',
              'if(input.size()+prelude.size()+suffix.size()+2>phase1_capacity)throw std::runtime_error("probe context");\n if(suffix.size()!=size_t(width))throw std::runtime_error("one registered append per measurement");')
    # Exports for pre/post qualification remain outside the append interval and
    # are absent when phase1_clean is true. Preserve them in separate heavy runs.
    require(text.count('observer.evidence.commit(ctx);')==4,'Probe commit layout drift')
    text=text.replace('observer.evidence.commit(ctx);','if(!phase1_clean)observer.evidence.commit(ctx);')
    text=once(text,' const auto probe_phase=econ_phase(ctx,observer,width,-1);', ''' llama_synchronize(ctx);
 const auto phase1_append_begin=ggml_time_us();
 const auto probe_phase=econ_phase(ctx,observer,width,-1);
 std::vector<float> phase1_requested;
 const auto phase1_vocab=llama_vocab_n_tokens(llama_model_get_vocab(model));''')
    # "model" is not assumed to exist in the host frontend: use the ctx accessor.
    text=text.replace('llama_model_get_vocab(model)','llama_model_get_vocab(llama_get_model(ctx))')
    text=once(text,'for(int j=0;j<count;++j)common_batch_add(b,suffix[at+j],int(all.size()+j),{0},true);',
              'for(int j=0;j<count;++j)common_batch_add(b,suffix[at+j],int(all.size()+j),{0},width<=4 || at+size_t(j)+1==suffix.size());')
    old='all.insert(all.end(),suffix.begin()+at,suffix.begin()+at+count);if(!phase1_clean)observer.evidence.commit(ctx);'
    new='''all.insert(all.end(),suffix.begin()+at,suffix.begin()+at+count);
  llama_synchronize(ctx);
  for(int j=0;j<count;++j)if(width<=4 || at+size_t(j)+1==suffix.size()){
   auto* values=llama_get_logits_ith(ctx,j);
   if(!values)throw std::runtime_error("missing original requested row");
   phase1_requested.insert(phase1_requested.end(),values,values+phase1_vocab);
  }'''
    text=once(text,old,new)
    text=once(text,' const int rollback=req.value("rollback",0);', ''' const auto phase1_append_end=ggml_time_us();
 if(!phase1_clean)observer.evidence.commit(ctx);
 const int rollback=req.value("rollback",0);''')
    text=once(text,'{"explicit_output_reserve",32}', '''{"capacity_observed",phase1_capacity},{"requested_mask",width<=4?"all":"last"},
 {"phase1_clean",phase1_clean},{"append_begin_us",phase1_append_begin},{"append_end_us",phase1_append_end},
 {"prefill_outside_append",true},
 {"observed_copied_rows",phase1_requested.size()/phase1_vocab},
 {"append_ms",(phase1_append_end-phase1_append_begin)/1000.0},
 {"append_includes_phase_bind_sync_and_requested_copy",true}''')
    return text


def stage(source, expected_sha256, out):
    source=Path(source);out=Path(out)
    require(not out.exists() and source.resolve()!=out.resolve(),'Fresh probe output required')
    require(digest(source)==expected_sha256,'Original probe source hash mismatch')
    result=patch(source.read_text(encoding='utf8'))
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(result,encoding='utf8')
    write_new(out.with_suffix(out.suffix+'.binding.json'),dict(status='SOURCE_OVERLAY_NOT_NATIVE_QUALIFIED',
        parent_sha256=expected_sha256,output_sha256=digest(out),core_changed=False,
        host_required=['Actual context/output allocation','Original UB128 producer','Signed capacity','Independent scalar R','Clean observer behavior with actual append counters','Actual output allocation and C4096 signed reserve; no label-only admission','Complete build input freeze before formal timing']))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('expected_sha256');p.add_argument('out',type=Path)
    a=p.parse_args();stage(a.source,a.expected_sha256,a.out)
