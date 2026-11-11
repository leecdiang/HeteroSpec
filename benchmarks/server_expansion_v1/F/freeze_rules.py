"""Bind real unchanged planner/transaction/backend sources before Llama outputs."""
from pathlib import Path
import argparse, hashlib, sys
from transfer_check import classify

def body(text,start,end):
    a=text.index(start);return text[a:text.index(end,a)+len(end)]

def main():
    p=argparse.ArgumentParser()
    for key in ('baseline','runtime','builds','out'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();sys.dont_write_bytecode=True;sys.path.insert(0,str(a.runtime.resolve()));from common import need,read,save,sha,verify_tree
    need(not a.out.exists(),'Fresh pre-output source/rule freeze');a.out.mkdir(parents=True)
    base=a.baseline/'stage-04';lock=read(base/'SOURCE_LOCK.json')
    for role in ('reference','loop4','packed'):verify_tree(base/'sources'/role,lock['sources'][role])
    before=base/'frontend';after=a.builds/'frontend';hashtext=lambda x:hashlib.sha256(x.encode()).hexdigest()
    def rules(front):
        text=(front/'worker.cpp').read_text()
        r={name:sha(front/name) for name in ('phase_plan.hpp','resident_context.hpp')}
        for name,start,end in [('Context','struct Context {','\n};'),('provision','static void provision(','\n}'),('request','static json request(','\n}')]:
            r['worker.cpp:'+name]=hashtext(body(text,start,end))
        return r
    backend={role+'/'+name:h for role,files in lock['sources'].items() for name,h in files.items()}
    spec=read(Path(__file__).parent/'models.json')
    old=dict(rule_files=rules(before),backend_files=backend,model_sha256=read(a.baseline/'inputs-01/MODELS.json')['Qwen']['target_sha256'])
    new=dict(rule_files=rules(after),backend_files=backend,model_sha256=spec['target']['sha256'])
    checked=classify(old,new);need(checked['source_rule_transfer']=='UNCHANGED','Initial transfer must use frozen existing final rules')
    save(a.out/'BEFORE.json',old);save(a.out/'LLAMA_INITIAL.json',new)
    save(a.out/'RULE_TRANSFER.json',{**checked,'candidate_model_forwards_seen':0,'frozen_before_Llama_candidate_outputs':True,
        'observer_frontend_adaptations':['Full-GPU model/KV observation','Capability/record binding','Heavy norm/RoPE/MUL_MAT descriptors'],
        'source_equality_is_not_numeric_qualification':True,'deployment_placement_is_separately_bound':True})
    save(a.out/'FREEZE.json',dict(status='FINAL_RULES_FROZEN_BEFORE_LLAMA_OUTPUTS',source_lock_sha256=sha(base/'SOURCE_LOCK.json'),
        build_complete_sha256=sha(a.builds/'BUILD_COMPLETE.json'),before_sha256=sha(a.out/'BEFORE.json'),after_sha256=sha(a.out/'LLAMA_INITIAL.json'),
        rule_transfer_sha256=sha(a.out/'RULE_TRANSFER.json'),numerical_qualification='NOT_RUN',formal_performance='NOT_RUN'))
    print('FINAL_RULES_FROZEN_BEFORE_LLAMA_OUTPUTS',flush=True)

if __name__=='__main__':main()
