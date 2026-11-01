"""Stage a successor native worker from authenticated PR151/156 source; never edit old trees."""
from __future__ import annotations
import argparse
import ast
from pathlib import Path
import re
import shutil
from common import *
HERE=Path(__file__).resolve().parent
LEGACY='scripts/experiments/rtx_dense14b_transfer_v1/'
UPPATH='scripts/experiments/rtx_scope_transfer_v1/'
ADAPTER_BLOB='f38e7f31cbfc594ede1ac4720300817844d4e506'
HEADERS=('repair_runtime.hpp','repair_boundary.hpp','repair_observer.inc','repair_mm.hpp')

def once(text,old,new):
    need(text.count(old)==1,'missing/nonunique source anchor: '+old[:90]);return text.replace(old,new)

def inherited_adapt(raw,adapter):
    """Evaluate only the two pinned pure source-transform functions, not module top level."""
    need(git_blob(adapter)==ADAPTER_BLOB,'14B adapter blob drift')
    tree=ast.parse(adapter.decode());fns=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('replace_once','adapt_worker')]
    need(len(fns)==2,'adapter functions missing')
    scope={'need':need,'STUDY':'rtx_dense14b_transfer_v1'}
    exec(compile(ast.Module(body=fns,type_ignores=[]),'pinned_adapter','exec'),scope)
    return scope['adapt_worker'](raw)

def adapt(text,observer_text):
    text=once(text,'slot.at("study_id")=="rtx_dense14b_transfer_v1"','slot.at("study_id")=="'+STUDY+'"')
    text=once(text,'struct Observer {','#include "repair_runtime.hpp"\nstruct Observer {')
    start=text.index('    static bool callback(');end=text.index('\n};\nstruct Context',start)
    text=text[:start]+observer_text.rstrip()+text[end:]
    text=once(text,'c=llama_init_from_model(m,p);need(c,"context initialization");',
        'c=llama_init_from_model(m,p);need(c,"context initialization");obs.context=c;obs.observe_target=target;obs.metadata_enabled=capture;')
    text=once(text,'obs=Observer{};', 'obs=Observer{};obs.context=c;obs.observe_target=target;obs.metadata_enabled=capture;')
    text=once(text,'obs.phase=phase;obs.base=pos;obs.caller=int(ids.size());',
        'obs.phase=phase;obs.base=pos;obs.caller=int(ids.size());obs.call_index=calls;')
    text=once(text,'need(!obs.bad,"observer/placement failed");',
        'need(!obs.bad,hs_repair::opt.error.empty()?"scheduler observer failed":hs_repair::opt.error.c_str());')
    text=once(text,'struct Pair {','#include "repair_boundary.hpp"\nstruct Pair {')
    text=once(text,'dense_target_layers>0&&dense_target_layers<40','dense_target_layers>0&&dense_target_layers<=999')
    text=once(text,'llama_model_n_layer(t)==40&&llama_model_n_embd(t)==5120',
        'llama_model_n_layer(t)==binding.at("repair_model").at("layers").get<int>()&&llama_model_n_embd(t)==binding.at("repair_model").at("embd").get<int>()')
    old='''    if(producer=="P1"){for(size_t i=0;i<prompt.size();i++)target->decode({prompt[i]},int(i),false,"PREFILL");}
    else target->decode(prompt,0,false,"PREFILL");
    if(draft)draft->decode(prompt,0,false,"PREFILL");
    int pending=target->sample(-1,"initial"),base=int(prompt.size()),cycle=0,cap=input["cap"];'''
    new='''    int transferred_pending=-1;json boundary;
    if(hs_repair::opt.prefill!="native"){
        transferred_pending=hs_repair::produce_and_import(t,*target,prompt,capture,dir,boundary);
    }else{
        target->decode(prompt,0,false,"PREFILL");
        if(capture)hs_repair::save_native_boundary(*target,dir,boundary);
    }
    r["boundary"]=boundary;r["repair_prefill"]=hs_repair::opt.prefill;
    if(draft)draft->decode(prompt,0,false,"PREFILL");
    int pending=transferred_pending>=0?transferred_pending:target->sample(-1,"initial");
    int base=int(prompt.size()),cycle=0,cap=input["cap"];
    need(!hs_repair::opt.probe||!spec.draft,"teacher probe cannot run acceptance loop");
    if(hs_repair::opt.probe)cap=int(hs_repair::opt.teacher.size())+1;
    r["teacher_forced"]=hs_repair::opt.probe;r["qualification_eligible"]=!hs_repair::opt.probe;
    r["probe_prefix"]=hs_repair::opt.teacher;
    r["observer_mode"]=hs_repair::opt.trace_mode;'''
    text=once(text,old,new)
    old='auto commit=[&](int id){ids.push_back(id);eog.push_back(llama_vocab_is_eog(v,id));return bool(eog.back())||int(ids.size())==cap;};'
    new='''auto commit=[&](int id){
        if(hs_repair::opt.probe && ids.size()<hs_repair::opt.teacher.size()){
            id=hs_repair::opt.teacher[ids.size()];need(!llama_vocab_is_eog(v,id),"teacher prefix includes EOG");pending=id;
        }
        ids.push_back(id);eog.push_back(llama_vocab_is_eog(v,id));return bool(eog.back())||int(ids.size())==cap;
    };'''
    text=once(text,old,new)
    text=once(text,'auto r=request(t,d,input,spec,life,slot.at("observer")=="heavy",',
        'hs_repair::configure(slot,root/id);\n            auto r=request(t,d,input,spec,life,slot.at("observer")=="heavy",')
    # Account for the additional live producer context, not only the original
    # resident pools. These are allocation probes with zero generated tokens.
    text=once(text,'        dump(root/"PROVISIONED.json",result);','''        if(admission_only){
            result["producer_allocation_probes"]=json::array();
            for(int candidate=0;candidate<3;++candidate){
                Context donor(t,candidate==0?1:4,true,candidate!=0,false,root/"bridge_capacity",candidate==2?0:1);
                size_t f=0,total=0;ggml_backend_dev_memory(gpu,&f,&total);
                result["producer_allocation_probes"].push_back({{"producer",candidate==0?"reference":candidate==1?"pq":"qb"},{"free_vram_bytes",f}});
                need(f>=binding.at("dense14b").at("min_vram_free_bytes").get<size_t>(),"producer context violates VRAM reserve");
                MEMORYSTATUSEX mm{};mm.dwLength=sizeof(mm);need(GlobalMemoryStatusEx(&mm),"producer RAM probe");
                need(mm.ullAvailPhys>=binding.at("dense14b").at("min_ram_free_bytes").get<unsigned long long>(),"producer context violates RAM reserve");
            }
        }
        dump(root/"PROVISIONED.json",result);''')
    text=once(text,'r["request_start_utc"]=request_start_utc;',
        'r["trace_files"]=hs_repair::opt.files;r["trace_bytes"]=hs_repair::opt.bytes;\n            r["request_start_utc"]=request_start_utc;')
    # Exact imported-data and canonical-producer costs remain inside service_seconds.
    return text

def patch_builder(text):
    old='''        code = Path(__file__).parent
        for name in ("worker.cpp", "arm_spec.h"):'''
    new='''        code = Path(__file__).parent
        from operator_patch import apply_rows
        repair_spec = json.loads((code / "REPAIR_BUILD.json").read_text())
        report["repair_source_changes"] = apply_rows(source, code, repair_spec["rowwise_roles"])
        report["repair_spec"] = repair_spec
        for name in ("repair_runtime.hpp", "repair_boundary.hpp", "repair_mm.hpp"):
            shutil.copyfile(code / name, root / name)
        for name in ("worker.cpp", "arm_spec.h"):'''
    return once(text,old,new)

def stage(repo,out,roles=0):
    out=Path(out);need(not out.exists(),'fresh stage directory required')
    need(type(roles) is int and 0<=roles<=7,'rowwise operator mask')
    upstream={n:git_read(repo,UPSTREAM,UPPATH+n,h) for n,h in PINS.items()}
    adapter=git_read(repo,BASE,LEGACY+'native.py',ADAPTER_BLOB)
    transformed=adapt(inherited_adapt(upstream['worker.cpp'].decode(),adapter),(HERE/'repair_observer.inc').read_text())
    out.mkdir(parents=True)
    for n,b in upstream.items():
        (out/n).write_bytes(transformed.encode() if n=='worker.cpp' else patch_builder(b.decode()).encode() if n=='build_native.py' else b)
    for n in HEADERS:shutil.copyfile(HERE/n,out/n)
    for n in ('operator_patch.py',):shutil.copyfile(HERE/n,out/n)
    # Static build choice: cannot be switched under a cached graph.
    p=out/'repair_mm.hpp';p.write_text(p.read_text().replace('#define HSR_MM_ROLES 0',f'#define HSR_MM_ROLES {roles}'),encoding='utf-8',newline='\n')
    save(out/'REPAIR_BUILD.json',{'study_id':STUDY,'base':BASE,'rowwise_roles':roles,
       'new_reference_allowed':False,'native_compilation_performed_here':False})
    save(out/'STAGING.json',{'status':'STAGED_NOT_NATIVE_QUALIFIED','base':BASE,'source_pins':PINS,
       'files':{p.name:file_hash(p) for p in out.iterdir() if p.is_file()},'native_requests':0})
    return out

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--repo',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True);ap.add_argument('--roles',type=int,default=0)
    args=ap.parse_args();print(stage(args.repo,args.out,args.roles))
