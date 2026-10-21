"""Scoped integration round 1. Restored PR97 source -> isolated graph/phase port."""
from pathlib import Path
import shutil,difflib,json,hashlib
ROOT=Path(__file__).resolve().parent
OLD=ROOT/'_host/pr97'
SRC=ROOT/'_host/source'
def edit(name,func):
 p=SRC/name;before=(OLD/'baseline/native/candidate-src'/name).read_text(encoding='utf-8');after=func(before);assert after!=before,name;p.write_text(after,encoding='utf-8',newline='\n')
 out=ROOT/'p0'/('source-'+name+'.diff');out.write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='PR97/'+name,tofile='PR108/'+name)),newline='\n')
def main():
 assert SRC.resolve().is_relative_to((ROOT/'_host').resolve())
 shutil.copytree(OLD/'baseline/native/candidate-src',SRC,dirs_exist_ok=True)
 shutil.copy2(ROOT/'native/local_attention.h',SRC/'local_attention.h')
 edit('llama-context.h',lambda t:t.replace('void b570_pilot_bind_phase_ubatch(uint32_t ub);','void b570_pilot_bind_phase_ubatch(uint32_t ub);\n    std::string b570_geometry_key;\n    void b570_geometry_bind(int role,int phase,int layout,uint32_t ub,int capacity);'))
 def context(t):
  t=t.replace('ub != 1 && ub != 32','ub != 1 && ub != 4 && ub != 32')
  t+='''
// Single-threaded host graph construction; each context owns its binding identity.
thread_local int b570_active_layout=0;
void llama_context::b570_geometry_bind(int role,int phase,int layout,uint32_t ub,int capacity) {
 if(role<0||role>1||phase<0||phase>4||layout<0||layout>2||capacity<1||capacity>4||
    (phase==0&&(layout!=0||(ub!=128&&ub!=512)))||
    (role==1&&(layout!=0||(phase!=0&&ub!=1)))||
    (role==0&&phase!=0&&ub!=4&&ub!=128)) throw std::runtime_error("PR108 phase guard");
 std::string key=std::to_string(role)+":"+std::to_string(phase)+":"+std::to_string(layout)+":"+std::to_string(ub)+":"+std::to_string(capacity);
 b570_active_layout=layout;
 if(key!=b570_geometry_key){
  synchronize();
  b570_pilot_bind_phase_ubatch(ub);
  gf_res_prev->reset(); // invalidate even when ub is unchanged; counts switch is irrelevant
  b570_geometry_key=key;
 }
}
extern "C" __declspec(dllexport) void llama_b570_geometry_bind(llama_context *ctx,int role,int phase,int layout,uint32_t ub,int capacity){ctx->b570_geometry_bind(role,phase,layout,ub,capacity);}
'''
  return t
 edit('llama-context.cpp',context)
 def graph(t):
  t='#include "local_attention.h"\nextern thread_local int b570_active_layout;\n'+t
  needle='    ggml_tensor * cur;\n\n    const bool use_flash_attn'
  assert t.count(needle)==1
  t=t.replace(needle,'''    ggml_tensor * cur;
    // Reserve graphs may be wider; real caller bounds are enforced before decode.
    if(b570_active_layout && q->ne[1]==2){
     if(cparams.flash_attn || arch!=LLM_ARCH_LLAMA || kq_b || sinks || v_mla ||
        hparams.attn_soft_cap || hparams.f_max_alibi_bias!=0) throw std::runtime_error("PR108 unsupported attention");
     if(!v_trans) v=ggml_cont(ctx0,ggml_transpose(ctx0,v));
     auto local=b570_local_attention(ctx0,b570_active_layout,q,k,v,kq_mask,kq_scale);
     if(!local) throw std::runtime_error("PR108 missing local graph");
     ggml_build_forward_expand(gf,local);
     return local;
    }

    const bool use_flash_attn''')
  return t
 edit('llama-graph.cpp',graph)
 print('PORT_ROUND_1_SOURCE_READY; no worker started')
if __name__=='__main__':main()
