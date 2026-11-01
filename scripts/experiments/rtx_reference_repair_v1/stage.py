"""Generate the repair worker from immutable PR156/PR151 sources. No inference."""
from __future__ import annotations
import argparse, difflib, hashlib, shutil, subprocess, sys
from pathlib import Path
from common import BASE, HISTORICAL_WORKER, STUDY, blob, git_bytes, need, save, sha


def replace(text,old,new,n=1):
    need(text.count(old)==n,'source anchor count changed: '+old[:90]);return text.replace(old,new)

PREFILL = '''    int pending=-1;
    if(producer=="RSEED" || producer=="BSEED"){
        Context* seed_context=producer=="RSEED"?reference_seed:candidate_seed;
        need(seed_context && seed_context!=target,"separate producer context required");
        auto seed_start=Clock::now();
        seed_context->reset(capture,dir/"seed");
        seed_context->decode(prompt,0,false,"PREFILL");
        auto boundary=repair_snapshot(*seed_context);
        r["seed_boundary"]=repair_boundary_identity(boundary);
        if(capture){r["seed_geometry"]=json::array();for(auto&item:seed_context->obs.signatures)r["seed_geometry"].push_back(item.second);}
        r["restore"]=repair_import(*target,boundary,prompt);
        if(capture)repair_save_boundary(boundary,dir/"producer_boundary");
        pending=repair_initial(boundary.logits,*target);
        r["producer_and_transfer_seconds"]=since(seed_start);
    }else{
        if(producer=="P1")for(size_t i=0;i<prompt.size();i++)target->decode({prompt[i]},int(i),false,"PREFILL");
        else target->decode(prompt,0,false,"PREFILL");
        if(producer=="SELF"){
            auto boundary=repair_snapshot(*target);
            r["restore"]=repair_import(*target,boundary,prompt);
            if(capture)repair_save_boundary(boundary,dir/"producer_boundary");
            pending=repair_initial(boundary.logits,*target);
        }else{
            pending=target->sample(-1,"initial");
            if(capture)repair_save_boundary(repair_snapshot(*target),dir/"producer_boundary");
        }
    }
    if(draft)draft->decode(prompt,0,false,"PREFILL");
    int base=int(prompt.size()),cycle=0,cap=input["cap"];
    r["row_repair_policy"]=std::getenv("HS_REPAIR_ROWS")?std::getenv("HS_REPAIR_ROWS"):"off";
    r["trace_mode"]=repair_options.value("mode",std::string("metadata"));
    r["diagnostic_teacher_forced"]=input.contains("teacher_ids");
    need(!input.contains("teacher_ids")||!spec.draft,"teacher forcing is target-only diagnostics");
'''


def patch_worker(text):
    text=replace(text,'#include <regex>','#include <regex>\n#include <cstdlib>')
    start=text.index('struct Observer {');end=text.index('struct Context {',start)
    text=text[:start]+'#include "repair_observer.h"\n'+text[end:]
    text=replace(text,'Observer obs;','Observer obs;std::vector<int> token_history;')
    text=replace(text,'obs=Observer{};',
        'obs=Observer{};obs.context=c;obs.root=dir;obs.enabled=cap;obs.values=cap && repair_options.value("mode",std::string("metadata"))=="values";token_history.clear();')
    text=replace(text,'obs.phase=phase;obs.base=pos;obs.caller=int(ids.size());',
        'need(pos==int(token_history.size()),"decode prefix position mismatch");obs.context=c;obs.root=path;obs.enabled=capture;obs.values=capture && repair_options.value("mode",std::string("metadata"))=="values";obs.call=calls;obs.prefix_hash=hash_text(json(token_history).dump());obs.prefix_ids=token_history;obs.call_ids=ids;obs.phase=phase;obs.base=pos;obs.caller=int(ids.size());')
    text=replace(text,'phases[phase]+=since(t);hsc::decode_end();calls++;',
        'phases[phase]+=since(t);hsc::decode_end();calls++;token_history.insert(token_history.end(),ids.begin(),ids.end());')
    text=replace(text,'void trim(int keep){need(llama_memory_seq_rm',
        'void trim(int keep){need(keep>=0&&size_t(keep)<=token_history.size(),"invalid logical trim");token_history.resize(keep);need(llama_memory_seq_rm')
    text=replace(text,'struct Pair {std::unique_ptr<Context> target,draft;};',
        'struct Pair {std::unique_ptr<Context> target,draft;};\n#include "repair_boundary.h"')
    text=replace(text,'const fs::path&dir,Pair&resident){','const fs::path&dir,Pair&resident,Context* reference_seed,Context* candidate_seed){')
    old='''    if(producer=="P1"){for(size_t i=0;i<prompt.size();i++)target->decode({prompt[i]},int(i),false,"PREFILL");}
    else target->decode(prompt,0,false,"PREFILL");
    if(draft)draft->decode(prompt,0,false,"PREFILL");
    int pending=target->sample(-1,"initial"),base=int(prompt.size()),cycle=0,cap=input["cap"];'''
    text=replace(text,old,PREFILL.rstrip())
    text=replace(text,'auto commit=[&](int id){ids.push_back(id);',
        '''auto commit=[&](int id){
        if(input.contains("teacher_ids")){
            r["teacher_predictions"].push_back(id);
            need(ids.size()<input.at("teacher_ids").size(),"teacher trace too short");
            id=input.at("teacher_ids").at(ids.size()).get<int>();pending=id;
        }
        ids.push_back(id);''')
    text=replace(text,'bool done=commit(pending);','bool done=commit(pending);repair_checkpoint(*target,ids,pending,done,dir);')
    text=replace(text,'done=commit(pending);continue;}','done=commit(pending);repair_checkpoint(*target,ids,pending,done,dir);continue;}')
    text=replace(text,'base=keep;cycle++;','base=keep;cycle++;repair_checkpoint(*target,ids,pending,done,dir);')
    text=replace(text,'slot.at("study_id")=="rtx_dense14b_transfer_v1"','slot.at("study_id")=="'+STUDY+'"')
    text=replace(text,'producer=="NATIVE" || (family=="Llama" && (producer=="P1" || producer=="P4_NATIVE"))',
        'producer=="NATIVE" || producer=="P1" || producer=="RSEED" || producer=="BSEED" || producer=="SELF"')
    text=replace(text,'auto identity=binding.at("families").at(family);',
        '''auto identity=binding.at("families").at(family);
        const auto row_policy=binding.at("repair").at("rows").get<std::string>();
        _putenv_s("HS_REPAIR_ROWS",row_policy.c_str());
        result["repair_binding"]=binding.at("repair");''')
    text=replace(text,'dense_target_layers>0&&dense_target_layers<40','dense_target_layers>0&&dense_target_layers<=999')
    text=replace(text,'need(llama_model_n_layer(t)==40&&llama_model_n_embd(t)==5120,"not 14B target geometry");',
        'need(llama_model_n_layer(t)==binding.at("dense14b").value("expected_layers",40)&&llama_model_n_embd(t)==binding.at("dense14b").value("expected_embd",5120),"target geometry binding differs");')
    text=replace(text,'auto r=request(t,d,input,spec,life,slot.at("observer")=="heavy",slot.at("producer"),root/id,residents[pool_key(family,spec)]);',
        '''repair_options=slot.value("trace",json::object());
            auto r=request(t,d,input,spec,life,slot.at("observer")=="heavy",slot.at("producer"),root/id,residents[pool_key(family,spec)],residents[pool_key(family,arm_spec("R"))].target.get(),residents[pool_key(family,arm_spec("C_PQ"))].target.get());''')
    return text


def patch_builder(text):
    text=replace(text,'import study as s','import study as s\nfrom repair_build import patch_core')
    text=replace(text,'code = Path(__file__).parent',
        '''code = Path(__file__).parent
        report["repair_graph_patch"] = patch_core(source, code)
        for name in ("repair_observer.h", "repair_boundary.h"):
            shutil.copyfile(code / name, root / name)''')
    return text


def stage(repo,out):
    repo=Path(repo).resolve();out=Path(out).resolve();need(not out.exists(),'fresh stage required')
    # Restore fixed adapter source without relying on whichever branch is checked out.
    vendor=out.parent/(out.name+'.adapter');need(not vendor.exists(),'fresh adapter dir required');vendor.mkdir(parents=True)
    pins={}
    for name in ('common.py','native.py'):
        data=git_bytes(repo,'scripts/experiments/rtx_dense14b_transfer_v1/'+name)
        (vendor/name).write_bytes(data);pins[name]=blob(data)
    subprocess.run([sys.executable,'-B',str(vendor/'native.py'),'--repo',str(repo),'--out',str(out)],check=True,timeout=120)
    worker=out/'worker.cpp';need(sha(worker)==HISTORICAL_WORKER,'PR156 adapter worker does not match archived build source')
    before=worker.read_text();after=patch_worker(before);worker.write_text(after,encoding='utf-8',newline='\n')
    builder=out/'build_native.py';builder.write_text(patch_builder(builder.read_text()),encoding='utf-8',newline='\n')
    for name in ('repair_observer.h','repair_boundary.h','reference_rows.h','repair_build.py'):
        shutil.copyfile(Path(__file__).with_name(name),out/name)
    (out/'WORKER.diff').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='PR156/worker.cpp',tofile='repair/worker.cpp')),encoding='utf-8')
    save(out/'REPAIR_STAGE.json',{'status':'SOURCE_STAGED_NOT_NATIVE_VALIDATED','base':BASE,'adapter_blobs':pins,
        'original_worker_sha256':HISTORICAL_WORKER,'worker_sha256':sha(worker),'build_script_sha256':sha(builder),
        'native_requests':0,'acceptance_loop':'unchanged except explicit target-only diagnostic teacher override',
        'cost':'reference prefill, export/import, readback and copies remain inside paid request'})
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();print(stage(a.repo,a.out))
