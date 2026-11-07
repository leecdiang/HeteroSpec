"""Derive a new host driver; keep the qualified numerical request body."""
from pathlib import Path
import shutil

r=Path(__file__).resolve().parent
old=Path('C:/hs/b570-draft-prefill-submit-20261020-r2')
s=(old/'prefill_submit.cpp').read_text()
s=s[:s.index('void equivalent(')]
s=s.replace('std::string phase="setup";bool bad=false;',
            'json prefill_events=json::array(), prefill_masks=json::array();\n std::string phase="setup";bool bad=false;')
before='if(name.rfind("kq-",0)==0&&t->op==GGML_OP_MUL_MAT){o.prefill_q_max=std::max(o.prefill_q_max,int(t->ne[1]));o.prefill_q_nodes++;}'
after='''if(name.rfind("kq-",0)==0&&t->op==GGML_OP_MUL_MAT){
    o.prefill_q_max=std::max(o.prefill_q_max,int(t->ne[1]));o.prefill_q_nodes++;
    auto j=tensor(t);j["sources"]=json::array();
    for(int i=0;i<GGML_MAX_SRC;i++)if(t->src[i])j["sources"].push_back(tensor(t->src[i]));
    o.prefill_events.push_back(j);if(t->ne[1]!=1)o.bad=true;
   }
   if(name.rfind("kq",0)==0&&t->op==GGML_OP_SOFT_MAX&&t->src[1]){
    o.prefill_masks.push_back({{"node",tensor(t)},{"mask",tensor(t->src[1])}});
   }'''
assert before in s;s=s.replace(before,after)
s=s.replace('Context target(t,arm=="R"?1:4,dir/"target",capture);',
            'Context target(t,arm=="R"?1:4,dir/"target",capture);')
s=s.replace('bool done=commit(next);', '''if(capture&&draft){
  dump(dir/"prefill-events.json",{{"qk",draft->obs.prefill_events},{"masks",draft->obs.prefill_masks},
       {"prompt_ids",prompt},{"positions","consecutive 0..prompt_length-1"},
       {"sequence_id",0},{"last_token_logits_only",true},
       {"draft_kv_max",llama_memory_seq_pos_max(llama_get_memory(draft->c),0)},
       {"target_kv_max",llama_memory_seq_pos_max(llama_get_memory(target.c),0)}});
  need(draft->obs.prefill_q_nodes==int(prompt.size())*llama_model_n_layer(d),"incomplete layer/ubatch q observations");
 }
 bool done=commit(next);''')
s=s.replace('o.record["target_decode_seconds"]',
            'o.record["observers_installed"]=capture;\n o.record["target_decode_seconds"]',1)
s+='\n'+(r/'closeout_main.cpp.inc').read_text()
(r/'closeout.cpp').write_text(s,encoding='utf-8')
cm=(old/'CMakeLists.txt').read_text().replace('b570_prefill_submit','b570_prefill_closeout').replace('prefill_submit','closeout')
(r/'CMakeLists.txt').write_text(cm)
(r/'build/Release').mkdir(parents=True,exist_ok=True)
for f in (old/'build/Release').glob('*.dll'): shutil.copy2(f,r/'build/Release'/f.name)
print('Derived closeout.cpp without changing the numerical libraries or request algorithm')
