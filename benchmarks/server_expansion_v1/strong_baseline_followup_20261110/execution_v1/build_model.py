"""CPU-only full-model G/B/C integration; pristine R is never modified/linked."""
import argparse
import difflib
import hashlib
from pathlib import Path
import shlex
import shutil
import subprocess
from build_backend import command
from support import fresh,need,read,sha
from objects import archive_members


def replace_once(text,old,new,label):
    need(text.count(old)==1,'Pinned source anchor: '+label)
    return text.replace(old,new,1)


def build(root,backend,out):
    out.mkdir();identity=read(backend/'BUILD.json')
    need(sha(backend/'operand-worker')==identity['executable_sha256'],'Backend identity')
    need(sha(backend/'libggml-cuda.a')==identity['new_archive_sha256'],'Backend archive identity')
    tree=out/'source';shutil.copytree(backend/'source',tree)
    graph=tree/'src/llama-graph.cpp';old=graph.read_text()
    begin=old.index('        for (int64_t i=0;i<cur->ne[1];++i) {',old.index('const bool q32_ref1'))
    end=old.index('    } else if (hs_query_batch',begin)
    original_loop=old[begin:end]
    new_branch='''        const int strong_arm=hs_strong_selected_arm();
        if(strong_arm==1) {
'''+original_loop+'''        } else if(strong_arm==2) {
            if(!ggml_is_contiguous(cur)) throw std::runtime_error("B rejects noncontiguous activation; no fallback");
            res=ggml_mul_mat(ctx0,w,cur);
            hs_strong_mark(res);
            ggml_format_name(res,"hs_backend_ref1_%s",w->name);
        } else if(strong_arm==3) {
            if(!ggml_is_contiguous(cur)) throw std::runtime_error("C rejects noncontiguous activation; no fallback");
            auto * channels=ggml_view_3d(ctx0,cur,cur->ne[0],1,cur->ne[1],cur->nb[1],cur->nb[1],0);
            auto * grouped=ggml_mul_mat(ctx0,w,channels);
            ggml_format_name(grouped,"hs_ref1_group_%s_%s",ggml_type_name(w->type),w->name);
            res=ggml_reshape_2d(ctx0,grouped,w->ne[1],cur->ne[1]);
        } else throw std::runtime_error("Strong arm not selected before graph construction");
'''
    new='#include "../ggml/src/ggml-cuda/hs_strong_ref1.hpp"\nextern "C" int hs_strong_selected_arm();\n'+old[:begin]+new_branch+old[end:]
    graph.write_text(new)
    (out/'llama-graph.cpp.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),
        fromfile='pinned/llama-graph.cpp',tofile='strong/llama-graph.cpp')))
    original=root/'run-01/build-loop4-01/native'
    locked=root/'run-01/stage-04/sources/loop4'
    unit=next(x for x in read(original/'compile_commands.json')if x['file'].endswith('/llama-graph.cpp'))
    args=[a.replace(str(locked),str(tree))for a in shlex.split(unit['command'])]
    graph_obj=out/'llama-graph.cpp.o';args[args.index('-o')+1]=str(graph_obj)
    args+=['-MD','-MF',str(out/'llama-graph.cpp.d')]
    command(out,'compile-graph',args,original)
    source_archive=root/'q32-q4-full-build-04/loop4/libllama.a'
    archive=out/'libllama.a';shutil.copyfile(source_archive,archive)
    command(out,'replace-llama-archive',['ar','r',str(archive),str(graph_obj)],out)
    front=out/'frontend';shutil.copytree(root/'q32-q4-full-build-10/frontend',front)
    entry=front/'entry.cpp';old=entry.read_text();new=replace_once(old,'int main(int argc,char**argv){',
        'int sb217_legacy_main(int argc,char**argv){','entry main')
    new=replace_once(new,'phase_target_reserve==32&&m2_k==3&&((job.at("draft")==true&&job.at("draft_width")==4)||(job.at("draft")==false&&job.at("draft_width")==1))',
        'phase_target_reserve==32&&m2_k==0&&job.at("draft")==false&&job.at("draft_width")==1','M-only guard')
    new=replace_once(new,'phase_lowering=job.at("lowering");','phase_lowering="SIMPLE"; // Preserve original W/whole physical-extent cuts','whole caller')
    new=replace_once(new,'#include "m1_capability.hpp"','#include "model_capability.hpp"','actual strong capability')
    new=replace_once(new,'result["modules_after"]=module_inventory();',
        'result["modules_after"]=module_inventory();result["native_module_maps"]=hs_loaded_modules();','actual loaded ELF maps')
    new=replace_once(new,'int position=0;hsc::begin(', 'int position=0;hs_work_reset();hsc::begin(', 'forced counters start')
    new=replace_once(new,'record["prefill_descriptor_journal"]=ctx->obs.journal_meta();',
        'auto forced_work=hs_work_finish();record["application_work"]={{"quant_calls",forced_work.quant_calls},'
        '{"quant_rows",forced_work.quant_rows},{"scalar_dot_dispatches",forced_work.scalar_dot_dispatches},'
        '{"scalar_dot_columns",forced_work.scalar_dot_columns},{"backend_loop_entries",forced_work.backend_loop_entries},'
        '{"kernel_application_launch_calls",forced_work.kernel_calls}};'
        'if(job.value("capacity_overflow_probe",false)&&one.at("name")=="synthetic-capacity1024-actual-q32-first"){need(position==1024,"Capacity probe initial extent");'
        'observe_state(*ctx,case_root/"before-overflow",-1);bool rejected=false;std::string error;hs_work_reset();'
        'try{ctx->decode({0},1024,false,"ILLEGAL_OVERFLOW");}catch(const std::exception& e){error=e.what();'
        'rejected=error=="unsupported cache/append requirements";}auto negative_work=hs_work_finish();'
        'need(rejected&&negative_work.kernel_calls==0&&negative_work.quant_calls==0&&negative_work.scalar_dot_dispatches==0,"Expected pre-forward overflow rejection");'
        'observe_state(*ctx,case_root/"after-overflow",-1);record["overflow_probe"]={{"expected_rejection",true},'
        '{"message",error},{"actual_forward_rows",0},{"observed_kernel_launches",negative_work.kernel_calls},{"state_comparison_required",true}};'
        'result["trajectories"]=result["trajectories"].get<int>()+1;}'
        'record["prefill_descriptor_journal"]=ctx->obs.journal_meta();','forced physical counters and overflow')
    new=replace_once(new,'auto r=request(t,d,input,spec,"resident",capture,"NATIVE",dir,pool);',
        'hs_work_reset();auto r=request(t,d,input,spec,"resident",capture,"NATIVE",dir,pool);'
        'auto work=hs_work_finish();r["application_work"]={{"quant_calls",work.quant_calls},{"quant_rows",work.quant_rows},'
        '{"quant_bytes",work.quant_bytes},{"scalar_dot_dispatches",work.scalar_dot_dispatches},'
        '{"scalar_dot_columns",work.scalar_dot_columns},{"backend_loop_entries",work.backend_loop_entries},'
        '{"kernel_application_launch_calls",work.kernel_calls},{"copy_calls",work.copy_calls},{"copy_bytes",work.copy_bytes},'
        '{"sync_calls",work.sync_calls},{"opaque_library_internal_launches",nullptr}};', 'full request work counters')
    new=replace_once(new,'r["online_state_exports"]=capture?json(nullptr):json(0);',
        'if(!capture){observe_state(*pool.target,dir/"post-service-terminal",-1);'
        'r["post_service_terminal_state_export"]=true;}json tape={{"ids",r.at("ids")},'
        '{"prompt_ids",r.at("prompt_ids")},{"stop_reason",r.at("stop_reason")},'
        '{"target_final_kv",r.at("target_final_kv")},{"executions",pool.target->plan.executions}};'
        'r["semantic_tape_sha256"]=hash_text(tape.dump());dump(dir/"semantic-tape.json",tape);'
        'r["online_state_exports"]=capture?json(nullptr):json(0);','clean terminal and semantic tape')
    entry.write_text(new)
    (out/'entry.cpp.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True))))
    observer=front/'geometry_observer.hpp';old=observer.read_text()
    # ask=false is a post-evaluation callback. Returning false aborts the graph.
    new=replace_once(old,'if(q32_operand_wanted(t,o.phase)){q32_operand_copy(t);return false;}o.bad=true;return false;',
        'if(q32_operand_wanted(t,o.phase)){q32_operand_copy(t);return true;}o.bad=true;return false;','callback continuation')
    new=replace_once(new,'if(!phase_observe)return false;','if(!phase_observe)return false;sb217_operand_set_call(o.caller,o.base);','actual q4/q32 capture call binding')
    new=replace_once(new,'{"name",t->name},{"type",ggml_type_name(t->type)}',
        '{"name",t->name},{"strong_backend_loop_marker",t->op==GGML_OP_MUL_MAT&&t->op_params[15]==0x48534231},{"type",ggml_type_name(t->type)}',
        'durable backend marker physical record')
    observer.write_text(new)
    (out/'geometry_observer.hpp.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True))))
    worker=front/'worker.cpp';old=worker.read_text()
    new=replace_once(old,'#include "resident_context.hpp"','#include "resident_context.hpp"\n#include "request_contract.hpp"','M input contract header')
    new=replace_once(new,'input.at("prompt_ids").size()+size_t(input.at("cap").get<int>())+size_t(k+1)<=llama_n_ctx(target->c)',
        'hs_m_input_valid(input.at("prompt_ids").size(),input.at("cap").get<int>(),llama_n_ctx(target->c))','match pristine R M capacity envelope')
    worker.write_text(new)
    (out/'worker.cpp.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True))))
    here=Path(__file__).parent
    for name in ('model_entry.cpp','work_counts.h','work_counts.cpp','operand_observer.hpp','model_capability.hpp','loaded_modules.hpp','request_contract.hpp'):
        shutil.copyfile(here/name,front/name)
    original_compile=read(root/'q32-q4-full-build-10/loop4/compile/command.json')['argv']
    args=[]
    for a in original_compile:
        a=a.replace(str(root/'q32-q4-full-build-10/frontend'),str(front))
        a=a.replace(str(root/'q32-q4-full-build-04/loop4/source'),str(tree))
        if a.endswith('/entry.cpp'):a=str(front/'model_entry.cpp')
        if a.endswith('/frontend.o'):a=str(out/'model-entry.o')
        args.append(a)
    args+=['-DQ32_OFFLINE_OPERANDS','-MD','-MF',str(out/'model-entry.d')]
    command(out,'compile-model-entry',args,original)
    counts=out/'work-counts.o'
    command(out,'compile-model-counts',['/usr/bin/c++','-std=c++17','-O3','-fPIC',
        '-I/usr/local/cuda-12.5/targets/x86_64-linux/include','-c',str(front/'work_counts.cpp'),
        '-o',str(counts),'-MD','-MF',str(out/'work-counts.d')],out)
    args=[]
    for a in read(root/'q32-q4-full-build-10/loop4/link/command.json')['argv']:
        if a.endswith('/frontend.o'):args.extend([str(out/'model-entry.o'),str(counts)])
        elif a.endswith('/transfer-worker'):args.append(str(out/'model-worker'))
        elif a.startswith('-Wl,-Map='):args.append('-Wl,-Map='+str(out/'model-worker.map'))
        elif a.endswith('/libllama.a'):args.append(str(archive))
        elif a.endswith('/libggml-cuda.a'):args.append(str(backend/'libggml-cuda.a'))
        else:args.append(a)
    for symbol in ('cudaLaunchKernel','cudaLaunchKernelExC','cudaMemcpyAsync','cudaMemcpy','cudaMemcpy2DAsync',
                   'cudaMalloc','cudaMallocAsync','cudaStreamSynchronize','cudaDeviceSynchronize'):
        args.append('-Wl,--wrap='+symbol)
    command(out,'link-model-worker',args,original)
    old_members=archive_members(source_archive);new_members=archive_members(archive)
    need([e['member']for e in old_members]==[e['member']for e in new_members],
         'Full model archive membership/order')
    need(sum(e['member']=='llama-graph.cpp.o'for e in old_members)==1,'Ambiguous changed archive member')
    identities=[]
    for original_member,new_member in zip(old_members,new_members):
        name=original_member['member'];before=original_member['sha256'];after=new_member['sha256']
        need(before==after or name=='llama-graph.cpp.o','Unexpected model member change')
        identities.append(dict(member=name,ordinal=original_member['ordinal'],old_sha256=before,new_sha256=after))
    fresh(out/'BUILD.json',dict(status='CPU_MODEL_BUILT_NOT_NUMERICALLY_QUALIFIED',
        executable=str(out/'model-worker'),executable_sha256=sha(out/'model-worker'),
        original_archive_sha256=sha(source_archive),new_archive_sha256=sha(archive),members=identities,
        backend_build_sha256=sha(backend/'BUILD.json'),independent_R_linked=False,native_model_requests_started=0,
        candidate_arms=['G','B','C'],graphs_policy='off_only',
        limitations=['No GPU qualification or deployment performance claim','Complete dependency closure pending']))


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
    p.add_argument('--backend',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();need(not a.out.exists(),'Preserve previous model build')
    try:build(a.root,a.backend,a.out)
    except BaseException as e:
        if a.out.exists():fresh(a.out/'BUILD_FAILED.json',dict(status='CPU_MODEL_BUILD_FAILED',reason=str(e),native_model_requests_started=0))
        raise


if __name__=='__main__':main()
