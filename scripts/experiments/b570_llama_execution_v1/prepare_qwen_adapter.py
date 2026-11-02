"""Adapt the original k1 Qwen controls to the exported per-target layout scope."""
from pathlib import Path
import argparse,sys,shutil
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import sha,read,write,need

def prepare(repo,out):
    repo=Path(repo);out=Path(out);need(not out.exists(),'fresh adapter source');out.mkdir(parents=True)
    original=repo/'benchmarks/b570_native_reproduction_v1/native/formal.cpp';text=original.read_text()
    def change(a,b):
        nonlocal text
        need(text.count(a)==1,'source anchor missing or ambiguous');text=text.replace(a,b)
    change('#include "llama.h"','#include "llama.h"\nextern "C" LLAMA_API void hs_b570_set_layout(int);')
    change('Clock::time_point whole;double deadline=230;void cutoff(){need(seconds(whole)<deadline,"internal deadline");}', '''Clock::time_point whole;double deadline=1200;ggml_backend_dev_t resource_device=nullptr;json resource_samples=json::array();
void cutoff(){need(seconds(whole)<deadline,"internal deadline");if(resource_device){size_t f=0,t=0;ggml_backend_dev_memory(resource_device,&f,&t);MEMORYSTATUSEX m{};m.dwLength=sizeof(m);need(GlobalMemoryStatusEx(&m),"RAM query");resource_samples.push_back({{"seconds",seconds(whole)},{"device_free_bytes",f},{"device_total_bytes",t},{"ram_available_bytes",m.ullAvailPhys}});need(f>=128ULL*1024*1024,"device reserve");need(m.ullAvailPhys>=2ULL*1024*1024*1024,"RAM reserve");}}''')
    change('bool capture;int calls=0;', 'bool capture;int layout=0;int calls=0;')
    change('int rc=llama_decode(c,b);','hs_b570_set_layout(layout);int rc=llama_decode(c,b);hs_b570_set_layout(0);')
    change(' _putenv_s("HS_REQUEST_LAYOUT",arm=="QB"?"QB":"PQ");',' // Semantic setter is applied only during target decoding; draft remains mode zero.')
    change(' Context target(t,arm=="R"?1:4,dir/"target",capture);',' Context target(t,arm=="R"?1:4,dir/"target",capture);target.layout=arm=="R"?0:arm=="QB"?2:1;')
    change('need((mode=="qual")&&index>=0&&index<4,"mode/index");deadline=mode=="qual"?230:590;', 'need((mode=="qual"||mode=="admit")&&index>=0&&index<4,"mode/index");deadline=1200;')
    change('need(gpu,"B570 absent");', 'need(gpu,"B570 absent");resource_device=gpu;')
    change('result["model_load_seconds"]=seconds(load_start);','result["model_load_seconds"]=seconds(load_start);cutoff();')
    anchor='  auto run=[&](const json&input,std::string label,bool capture,std::string category){'
    change(anchor,'''  if(mode=="admit"){
   {Context a(t,4,root/"target",false);Context b(d,1,root/"draft",false);cutoff();}
   cleanup();result["status"]="RESOURCE_ADMITTED";result["normal_cleanup_returned"]=true;result["forward_calls"]=0;dump(root/"result.json",result);return 0;
  }
'''+anchor)
    text=text.replace('dump(root/"result.json",result);','result["resource_samples"]=resource_samples;result["min_device_reserve_bytes"]=128ULL*1024*1024;dump(root/"result.json",result);')
    (out/'qwen_formal.cpp').write_text(text,encoding='utf-8')
    shutil.copyfile(original.parent/'raw_capture.h',out/'raw_capture.h')
    write(out/'SOURCE.json',{'original':str(original.resolve()),'original_sha256':sha(original),'adapter_sha256':sha(out/'qwen_formal.cpp'),'raw_capture_sha256':sha(out/'raw_capture.h'),'changes':['Exported layout setter around target decode only; draft mode zero','Zero-forward admission and per-decode 128MiB VRAM/2GiB RAM reserves with actual samples','Finite 1200-second diagnostic deadline'],'resource_policy_reason':'Separate historical Qwen regression preserves its original all-GPU target/draft placement. Initial 512MiB guard rejected before any forward. Prospective 128MiB guard applies only to this old Qwen validation, not Llama qualification or timing; admission must also allocate both contexts and every decode remains guarded.','unchanged':['k1 acceptance/correction loop','all-GPU Q8 models','F16 KV and native q2/q4 key256/512 domain','original prompt IDs, caps and full-vector capture']})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',required=True);p.add_argument('--out',required=True);a=p.parse_args();prepare(a.repo,a.out)
