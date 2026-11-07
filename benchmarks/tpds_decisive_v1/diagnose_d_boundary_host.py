"""Bounded causal probe at the already failed head; never a panel retry."""
from profile_host import *
from native_adapter import RUNS

def build():
    dest=ROOT/'D-boundary-diagnostic-v1';dest.mkdir()
    for name in ('worker.cpp','target_capture.hpp','replay_path.hpp'):shutil.copy2(ROOT/'forced-v2'/name,dest/name)
    source=(HERE/'forced_host.cpp').read_text()
    source=source.replace('#include "replay_path.hpp"','#include "replay_path.hpp"\n#include "llama-kv-cache.h"')
    code=r'''
        if(job.contains("diagnostic_verify")){
            auto geometry=[](Context*c){auto*kv=static_cast<llama_kv_cache*>(llama_get_memory(c->c));const auto&cells=kv->get_cells(0);json mapping=json::array();for(uint32_t i=0;i<cells.size();i++)if(!cells.is_empty(i))mapping.push_back({i,cells.pos_get(i)});llama_kv_cache::slot_info info;info.strm={0};info.idxs={{0}};return json{{"cells",mapping},{"used_max_p1",cells.used_max_p1()},{"attention_key_extent",kv->get_n_kv(info)}};};
            auto*candidate=residents[pool_key("Qwen",arm_spec("C_QB"))].target.get();
            auto tokens=job.at("diagnostic_verify").get<std::vector<int>>();need(tokens.size()==4,"fixed actual failed call");
            auto input=root/"0/767/sequence.bin";std::ifstream f(input,std::ios::binary|std::ios::ate);need(bool(f),"prefix open");std::vector<uint8_t> bytes(size_t(f.tellg()));f.seekg(0);f.read((char*)bytes.data(),bytes.size());need(bool(f),"prefix read");
            result["diagnostic"]=json::array();
            for(auto widths:{std::vector<int>{4},std::vector<int>{1,3}}){
                auto name=widths.size()==1?"actual4":"boundarycut1plus3";auto dir=root/name;candidate->reset(false,dir);need(llama_state_seq_set_data(candidate->c,bytes.data(),bytes.size(),0)==bytes.size(),"independent prefix import");json record={{"name",name},{"before",geometry(candidate)},{"calls",json::array()}};int offset=0;
                for(int width:widths){std::vector<int> ids(tokens.begin()+offset,tokens.begin()+offset+width);candidate->decode(ids,767+offset,true,"VERIFY");result["token_rows"]=result["token_rows"].get<int64_t>()+width;record["calls"].push_back({{"width",width},{"after",geometry(candidate)}});for(int row=0;row<width;row++)tpds_decisive::capture_existing(candidate->c,t,dir/std::to_string(768+offset+row),row);offset+=width;}
                result["requests"]=result["requests"].get<int>()+1;result["diagnostic"].push_back(record);
            }
        }
'''
    source=source.replace('        residents.clear();llama_model_free(d);',code+'        residents.clear();llama_model_free(d);',1)
    (dest/'forced_host.cpp').write_text(source,encoding='utf8');compile_one(dest,'forced_host.cpp')
    return dest

def run():
    dest=ROOT/'D-boundary-diagnostic-v1'
    job=json.loads((RUNS/'D-main-forced-10/job.json').read_bytes());job['attempt_id']='D-boundary-diagnostic-v1';job['exe']=str(dest/'bin/worker.exe');job['binding']['families']['Qwen']['executable_sha256']=sha(dest/'bin/worker.exe')
    forced=job['forced'];assert len(forced['prompt_ids'])==704
    suffix=forced['paths'][0]['suffix'][:67];assert suffix[63:67]==[220,16,198,286]
    forced['paths']=[dict(suffix=suffix,positions=list(range(767,772)))];forced['diagnostic_verify']=suffix[63:67]
    job['reservation']=dict(requests=3,token_rows=779,operators=0)
    out=execute(job);profile=json.loads((ROOT/'QWEN_PROFILE.json').read_bytes());rows=[]
    for name in ('actual4','boundarycut1plus3'):
        vectors=[]
        for n in range(768,772):vectors.append(dict(prefix=n,equal=sha(out/'native'/name/str(n)/'frontier.f32')==sha(out/'native/0'/str(n)/'frontier.f32')))
        a,_=parse((out/'native'/name/'771/sequence.bin').read_bytes(),list(range(771)),profile);r,_=parse((out/'native/0/771/sequence.bin').read_bytes(),list(range(771)),profile)
        rows.append(dict(name=name,vectors=vectors,active_kv_equal=a==r,active_sha256=hashlib.sha256(a).hexdigest(),reference_sha256=hashlib.sha256(r).hexdigest()))
    put(ROOT/'D-BOUNDARY-DIAGNOSIS.json',dict(rows=rows,native_result=str(out/'native/result.json'),scope='fixed failed head 767, token-only independent scalar prefix, original core and numerical modules; diagnostic counterfactual only, no main retry or performance inference'))
    print(json.dumps(rows),flush=True)

if __name__=='__main__':
    import sys
    if sys.argv[1]=='build':build()
    else:run()
